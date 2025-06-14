import json
import logging
import requests
import sys
from typing import List, Optional, Any

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def forward_message_by_qq(url: str,
        user_id: Optional[str],
        group_id: Optional[str],
        messages: List[str],
        screenshots: Optional[List[str]] = None
) -> None:
    """QQ合并消息转发（使用换行符分隔多条消息）"""
    qq_url = url
    logger.info(f"QQ合并消息转发服务地址: {qq_url}")
    screenshots = screenshots or []

    def create_node(content: str) -> dict:
        """创建标准化消息节点"""
        return {
            "type": "node",
            "data": {
                "user_id": "10086",
                "nickname": "CloudCrane Bot",
                "content": content
            }
        }

    # 构造消息节点（使用换行符分隔多条消息）
    nodes = [
        create_node(message) for message in messages
    ]

    # 添加截图节点
    nodes.extend(
        create_node(f"[CQ:image,file={url}]")
        for url in screenshots
    )

    # # 构造请求参数
    # params = {
    #     "messages": nodes,
    #     "message_type": "group" if group_id else "private",
    #     **({"group_id": group_id} if group_id else {"user_id": sender.getUserID()})
    # }
    if group_id:
        params = {
            "messages": nodes,
            "group_id": group_id
        }
        qq_url = f"{qq_url}/send_group_forward_msg"
    else:
        params = {
            "messages": nodes,
            "user_id": user_id
        }
        qq_url = f"{qq_url}/send_private_forward_msg"

    # logger.info(f"QQ合并消息发送请求参数: {json.dumps(params, indent=2)}")

    try:
        timeout = 30
        resp = requests.post(
            qq_url,
            json=params,
            timeout=timeout
        )
        resp.raise_for_status()

        try:
            resp_data = resp.json()
        except json.JSONDecodeError:
            logger.error(f"响应解析失败，原始内容: {resp.text}")
            raise ValueError("Invalid JSON response")

        if resp_data.get("status") == "ok":
            logger.info(f"合并转发消息成功，响应: {resp.text}")
        else:
            logger.error(f"合并转发消息失败，错误信息: {resp.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"QQ消息发送请求失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"QQ消息发送未知错误: {str(e)}")
        raise