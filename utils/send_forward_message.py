import json
import aiohttp
from typing import List, Optional
from astrbot.core import logger

async def forward_message_by_qq(url: str,
                                user_id: Optional[str],
                                group_id: Optional[str],
                                access_token: Optional[str],
                                messages: List[str],
                                screenshots: Optional[List[str]] = None
                                ) -> None:
    """QQ合并消息转发（异步版本）"""
    qq_url = url.rstrip('/')
    logger.info(f"QQ合并消息转发服务地址: {qq_url}")
    screenshots = screenshots or []

    def create_node(content: str) -> dict:
        return {
            "type": "node",
            "data": {
                "user_id": "10086",
                "nickname": "CloudCrane Bot",
                "content": content
            }
        }

    nodes = [create_node(message) for message in messages]
    nodes.extend(create_node(f"[CQ:image,file={url}]") for url in screenshots)

    if group_id:
        params = {
            "messages": nodes,
            "group_id": group_id,
            "access_token": access_token
        }
        qq_url = f"{qq_url}/send_group_forward_msg"
    else:
        params = {
            "messages": nodes,
            "user_id": user_id,
            "access_token": access_token
        }
        qq_url = f"{qq_url}/send_private_forward_msg"

    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(qq_url, json=params) as resp:
                resp.raise_for_status()
                resp_data = await resp.json()

                if resp_data.get("status") == "ok":
                    logger.info(f"合并转发消息成功，响应: {json.dumps(resp_data)}")
                else:
                    logger.error(f"合并转发消息失败，错误信息: {json.dumps(resp_data)}")
                    raise ValueError(f"API错误: {resp_data.get('message')}")

    except aiohttp.ClientError as e:
        logger.error(f"QQ消息发送请求失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"QQ消息发送未知错误: {str(e)}")
        raise