import random
import re
from typing import AsyncGenerator, Any, List, Optional, Dict, Coroutine
import aiohttp
from astrbot.core.message.message_event_result import MessageEventResult
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from .utils.send_forward_message import forward_message_by_qq
from .utils.translate import BaiduTranslator


@register("JavBus Serach", "cloudcranesss", "一个基于JavBus API的搜索服务", "v1.0.1",
          "https://github.com/cloudcranesss/astrbot_plugin_javbus_search")
class JavBusSerach(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.javbus_api_url = config.get("javbus_api_url", "")
        self.forward_url = config.get("forward_url", "")
        self.javbus_image_proxy = config.get("javbus_image_proxy", "")
        self.baidu_api_key = config.get("baidu_api_key", "")
        self.baidu_secret_key = config.get("baidu_secret_key", "")
        self.qq_access_token = config.get("qq_access_token", "")
        logger.info(
            f"初始化JavBus搜索插件，API地址: {self.javbus_api_url}\n"
            f"转发地址配置: {'已配置' if self.forward_url else '未配置'}\n"
            f"JavBus 图片代理地址: {self.javbus_image_proxy}")
        self.api = JavBusAPI(self.javbus_api_url)
        self.trans = BaiduTranslator(self.baidu_api_key, self.baidu_secret_key)

    async def send_reply(
            self,
            event: AstrMessageEvent,
            content: List[str]
    ) -> AsyncGenerator[MessageEventResult, Any]:
        """统一消息发送方法"""
        logger.info(f"准备发送回复，内容长度: {len(content)}")
        if self.forward_url:
            logger.info(f"使用转发服务发送消息，接收方: {event.get_group_id() or '私聊'}")
            # 直接调用异步函数
            await forward_message_by_qq(
                self.forward_url,
                event.get_sender_id(),
                event.get_group_id(),
                self.qq_access_token,  # access_token留空或根据实际情况修改
                content,
                []
            )
            logger.info("转发消息请求已提交")
        else:
            logger.info("使用普通消息回复")
            for message in content:
                yield event.plain_result(message)
        logger.info(f"消息发送完成，共 {len(content)} 条内容")

    # 将 www.javbus.com 替换为 self.javbus_image_proxy
    async def proxy_image(self, image_url: str):
        image_url = image_url.replace("https://www.javbus.com", self.javbus_image_proxy)
        return image_url

    @filter.regex(r"^搜关键词(.+)", flags=re.IGNORECASE, priority=1)
    async def search_movies(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, Any]:
        messages = event.get_messages()
        result1 = str(messages[0])
        result2 = re.findall(r"text='(.*?)'", result1)[0]
        keyword = result2.split("搜关键词")[1]
        if not keyword:
            logger.warning("搜索关键词为空")
            yield event.plain_result("请输入搜索关键词")
            return

        logger.info(f"用户 {event.get_sender_id()} 在群组 {event.get_group_id()} 搜索影片: {keyword}")

        try:
            logger.info(f"开始调用搜索API，关键词: {keyword}")
            datas = await self.api.search_movies(keyword=keyword)  # 添加await
            logger.info(f"搜索完成，找到 {len(datas.get('movies', []))} 个结果")
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}", exc_info=True)
            yield event.plain_result("搜索服务暂时不可用")
            return

        if not datas.get("movies"):
            logger.info("未找到匹配的影片")
            yield event.plain_result("没有找到相关影片")
            return

        movies_info = []
        for idx, data in enumerate(datas["movies"]):
            logger.info(f"处理第 {idx + 1}/{len(datas['movies'])} 个结果: {data.get('id')}")
            title = data['title'][:20] + "..." if len(data['title']) > 20 else data['title']
            movies_info.append(
                f"番号: {data['id']}\n"
                f"标题: {title}\n"
                f"日期: {data['date']}\n"
                f"标签: {', '.join(data['tags'])}\n"
                f"[CQ:image,file={await self.proxy_image(data['img'])}]\n"
            )

        movies_info.append(f"找到 {len(datas['movies'])} 个结果")
        logger.info(f"准备返回 {len(movies_info)} 条消息")

        async for msg in self.send_reply(event, movies_info):
            yield msg

    @filter.regex(r"^搜演员(.+)")
    async def search_star(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, Any]:
        messages = event.get_messages()
        result1 = str(messages[0])
        result2 = re.findall(r"text='(.*?)'", result1)[0]
        keyword = result2.split("搜演员")[1]
        if not keyword:
            logger.warning("演员搜索关键词为空")
            yield event.plain_result("请输入演员名称")
            return

        logger.info(f"用户 {event.get_sender_id()} 在群组 {event.get_group_id()} 搜索演员: {keyword}")

        try:
            logger.info(f"开始调用演员搜索API: {keyword}")
            translated_keyword = await self.trans.translate(keyword)
            data = await self.api.get_star_by_name(translated_keyword)
            logger.info(f"演员搜索结果: {data}")
        except Exception as e:
            logger.error(f"演员搜索失败: {str(e)}", exc_info=True)
            yield event.plain_result("演员查询服务异常")
            return

        if not data:
            logger.info("未找到演员信息")
            yield event.plain_result("未找到该演员信息")
            return

        star_info = [
            f"姓名: {data['name']}\n"
            f"生日: {data['birthday']}\n"
            f"年龄: {data['age']}\n"
            f"身高: {data['height']}\n"
            f"三维: {data['bust']} - {data['waistline']} - {data['hipline']}\n"
            f"[CQ:image,file={await self.proxy_image(data['avatar'])}]"
        ]
        logger.info(f"演员信息已构建: {data['name']}")

        async for msg in self.send_reply(event, star_info):
            yield msg

    @filter.regex(r"^搜磁力([a-zA-Z0-9-]+)")
    async def search_magnet(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, Any]:
        messages = event.get_messages()
        result1 = str(messages[0])
        result2 = re.findall(r"text='(.*?)'", result1)[0]
        keyword = result2.split("搜磁力")[1]
        logger.info(f"用户 {event.get_sender_id()} 在群组 {event.get_group_id()} 搜索磁力: {keyword}")

        try:
            logger.info(f"开始获取影片详情: {keyword}")
            detail = await self.api.get_movie_detail(keyword)  # 添加await
            logger.info(f"影片详情获取完成，结果: {'找到' if detail else '未找到'}")
        except Exception as e:
            logger.error(f"影片详情获取失败: {str(e)}", exc_info=True)
            yield event.plain_result("影片详情获取失败")
            return

        if not detail:
            logger.info("未找到影片详情")
            yield event.plain_result("没有找到该影片")
            return

        if isinstance(detail.get("videoLength"), int):
            try:
                hours = detail["videoLength"] // 60
                minutes = detail["videoLength"] % 60
                videoLength = f"{hours}小时{minutes}分钟"
                logger.info(f"计算影片时长: {detail['videoLength']}分钟 -> {videoLength}")
            except Exception as e:
                logger.error(f"时长计算错误: {str(e)}")
                videoLength = str(detail.get("videoLength", "未知"))
        else:
            videoLength = str(detail.get("videoLength", "未知"))

        stars_str = "暂无演员信息"
        if detail.get("stars"):
            try:
                stars = [s["name"] if isinstance(s, dict) else str(s) for s in detail["stars"][:3]]
                stars_str = "、".join(stars)
                if len(detail["stars"]) > 3:
                    stars_str += f" 等{len(detail['stars'])}人"
                logger.info(f"处理演员信息完成: {stars_str}")
            except Exception as e:
                logger.error(f"演员信息处理失败: {str(e)}")
                stars_str = "演员信息解析错误"

        director_str = "未知"
        if isinstance(detail.get("director"), dict):
            director_str = detail["director"].get("name", "未知")
        elif detail.get("director"):
            director_str = str(detail["director"])
        logger.info(f"导演信息: {director_str}")

        info_lines = [
            f"【影片详情】",
            f"番号：{detail.get('id', 'N/A')}",
            f"标题：{detail.get('title', 'N/A')}",
            f"日期：{detail.get('date', 'N/A')}",
            f"时长：{videoLength}",
            f"演员：{stars_str}",
            f"导演：{director_str}"
            f"[CQ:image,file={await self.proxy_image(detail['img'])}]"
        ]

        magnets = []
        if 'gid' in detail and 'uc' in detail:
            try:
                logger.info(f"开始获取磁力链接: gid={detail['gid']}, uc={detail['uc']}")
                magnets = await self.api.get_magnets(  # 添加await
                    movie_id=keyword,
                    gid=detail['gid'],
                    uc=detail['uc']
                )[:5]
                logger.info(f"获取到 {len(magnets)} 条磁力链接")
            except Exception as e:
                logger.error(f"磁力链接获取失败: {str(e)}", exc_info=True)
        else:
            logger.warning("缺少获取磁力链接的必要参数")

        if magnets:
            info_lines.append("【磁力链接】")
            for idx, magnet in enumerate(magnets, 1):
                title = magnet['title']
                size = magnet['size']
                share_date = magnet['shareDate']
                is_hd = magnet['isHD']
                link = magnet['link']
                has_sub = magnet['hasSubtitle']

                info_lines.append(
                    f"{idx}. {title} {size}\n"
                    f"{share_date}\n"
                    f"{' 高清' if is_hd else ''} 字幕：{'有' if has_sub else '无'}\n"
                    f"{link}"
                )
        else:
            info_lines.append("【未找到磁力链接】")
            logger.info("未找到磁力链接")

        logger.info(f"准备返回磁力搜索结果，信息行数: {len(info_lines)}")
        async for msg in self.send_reply(event, ["\n".join(info_lines)]):
            yield msg


class JavBusAPI:
    def __init__(self, base_url: str = None):
        self.base_url = base_url.rstrip('/') if base_url else ""
        logger.info(f"JavBus API初始化成功，基础URL为：{self.base_url}")
        # 移除requests.Session
        # 添加默认headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def _request(self, url: str, params: Dict = None) -> Dict:
        """统一的异步请求方法"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"请求失败: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"处理响应失败: {str(e)}")
                raise

    async def get_movies(
            self,
            page: int = 1,
            magnet: str = "exist",
            filter_type: Optional[str] = None,
            filter_value: Optional[str] = None,
            movie_type: str = "normal"
    ) -> Dict[str, Any]:
        params = {
            'page': page,
            'magnet': magnet,
            'type': movie_type
        }

        if filter_type and filter_value:
            params.update({
                'filterType': filter_type,
                'filterValue': filter_value
            })

        url = f"{self.base_url}/api/movies"
        return await self._request(url, params)

    async def search_movies(
            self,
            keyword: str,
            page: int = 1,
            magnet: str = "exist",
            movie_type: str = "normal"
    ) -> Dict[str, Any]:
        params = {
            'keyword': keyword,
            'page': page,
            'magnet': magnet,
            'type': movie_type
        }

        url = f"{self.base_url}/api/movies/search"
        return await self._request(url, params)

    async def get_movie_detail(self, movie_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/movies/{movie_id}"
        return await self._request(url)

    async def get_magnets(
            self,
            movie_id: str,
            gid: str,
            uc: str,
            sort_by: str = "size",
            sort_order: str = "desc"
    ) -> dict:
        params = {
            'gid': gid,
            'uc': uc,
            'sortBy': sort_by,
            'sortOrder': sort_order
        }

        url = f"{self.base_url}/api/magnets/{movie_id}"
        return await self._request(url, params)

    async def get_star_detail(
            self,
            star_id: str,
            star_type: str = "normal"
    ) -> Dict[str, Any]:
        params = {'type': star_type}
        url = f"{self.base_url}/api/stars/{star_id}"
        return await self._request(url, params)

    async def get_star_by_name(self, star_name: str) -> dict[str, Any] | None:
        movie_lists = await self.search_movies(star_name)
        movie_ids = [movie["id"] for movie in movie_lists.get("movies", [])]

        if not movie_ids:
            return None

        movie_id = random.choice(movie_ids)
        movie_details = await self.get_movie_detail(movie_id)

        star_ids = []
        for star in movie_details.get("stars", []):
            if star_name in star.get('name', ''):
                star_ids.append(star.get('id'))

        if not star_ids:
            return None

        return await self.get_star_detail(star_ids[0])