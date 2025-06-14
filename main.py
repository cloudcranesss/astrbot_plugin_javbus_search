import re
from typing import AsyncGenerator, Generator
from astrbot.core.message.message_event_result import MessageEventResult
from utils.send_forward_message import forward_message_by_qq
from utils.javbus_api import *
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig

@register("JavBus Serach", "cloudcranesss", "一个基于JavBus API的搜索服务", "v1.0.0", "https://github.com/cloudcraness/astrbot_plugin_javbus_serach")
class JavBusSerach(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.javbus_api_url = config.get("javbus_api_url", "")
        self.forward_url = config.get("forward_url", "")
        self.api = JavBusAPI(self.javbus_api_url)

    def reply(self, event: AstrMessageEvent, content: List[str], screenshots: Optional[List[str]] = None) -> Generator[
        MessageEventResult, Any, None]:
        if self.forward_url:
            forward_message_by_qq(self.forward_url, event.get_sender_id(), event.get_group_id(), content, screenshots)
        else:
            for message in content:
                yield event.plain_result(message)

    # 通过关键词搜索影片，一般是番号，以搜+番号的格式
    @filter.regex(r"^搜关键词(.+)", flags=re.IGNORECASE, priority=1)
    async def search_movies(self, event: AstrMessageEvent):
        message  = event.get_messages()
        if message:
            keyword = message[0]
            # 过滤 搜 这个字
            keyword = keyword.replace("搜关键词", "")
            logger.info(f"用户 {event.get_sender_id()} 触发了 search_movies 命令，关键词为 {keyword}")
            datas = self.api.search_movies(keyword=keyword)
            movies_info = []
            for data in datas["movies"]:
                movies_info.append(f"番号: {data['id']}\r"
                                   f"名称: {data['title'][20:]}\r"
                                   f"日期: {data['date']}\r"
                                   f"标签: {data['tags']}\r"
                                   f"[CQ:image,file={data['img']}]\n")

            self.reply(event, movies_info)
            self.api.close()
            yield event.plain_result("搜索完成")
            yield event.plain_result(f"共找到 {len(datas['movies'])} 个结果")

    # 搜演员，人名
    @filter.regex(r"^搜演员(.+)")
    async def search_star(self, event: AstrMessageEvent) -> AsyncGenerator[MessageEventResult, Any]:
        logger.info("开始搜索演员")
        messages = event.get_messages()
        if len(messages) < 4:
            yield event.plain_result("请输入演员名称")
            return
        keyword = messages[0]
        keyword = keyword.replace("搜演员", "")
        data = self.api.get_star_by_name(keyword)
        star_info = []
        if data:
            star_info.append(f"姓名: {data['name']}\r"
                             f"生日: {data['birthday']}\r"
                             f"年龄: {data['age']}\r"
                             f"身高: {data['height']}\r"
                             f"三维: {data['bust']} {data['waistline']} {data['hipline']}\r"
                             f"[CQ:image,file={data['avatar']}]")
            self.reply(event, star_info)
        else:
            yield event.plain_result("未找到该演员")

    # 搜影片磁力，获取磁力链接，必须是番号
    @filter.regex(r"^搜磁力[a-zA-Z0-9]+")
    async def search_magnet(self, event: AstrMessageEvent):
        logger.info("开始搜索磁力")
        messages = event.get_messages()
        if messages is None:
            yield event.plain_result("请输入番号")
            return

        keyword = messages[0]
        keyword = keyword.replace("搜磁力", "")
        detail = self.api.get_movie_detail(keyword)

        if detail is None:
            yield event.plain_result("没有找到影片")
            return

        if "gid" in detail and "uc" in detail:
            logger.info("获取磁力链接")
            logger.info(f"gid: {detail['gid']}, uc: {detail['uc']}")
            magnets = self.api.get_magnets(
                movie_id=keyword,
                gid=detail['gid'],
                uc=detail['uc']
            )
            logger.info(f"获取到 {len(magnets)} 个磁力链接")

            # 修复这里：f-string 内部使用单引号
            info_line = [
                f"【影片详情】\r"
                f"番号：{detail['id']}\r"
                f"日期：{detail['date']}\r"
                f"时长：{detail['videoLength']}\r"
                f"标题：{detail['title']}\r"
                f"演员：{detail['stars']}\r"
                f"导演：{detail['director']}\r"
                f"【磁力链接如下】"
            ]

            if magnets:
                logger.info(f"共获取到 {len(magnets)} 个磁力链接")
                for idx, magnet in enumerate(magnets[:5], 1):
                    # 这里也改为单引号
                    info_line.append(f"{idx}. {magnet}")
            else:
                logger.info("没有获取到磁力链接")
                info_line.append("没有获取到磁力链接")
        else:
            # 这里也改为单引号
            info_line = [
                f"【{detail['title']}】\r"
                f"时长：{detail['runtime']}\r"
                f"演员：{detail['star']}\r"
                f"导演：{detail['director']}\r"
                f"【无磁力链接】"
            ]

        self.reply(event, info_line)
