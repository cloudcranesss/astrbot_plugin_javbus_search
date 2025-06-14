# 调用谷歌翻译将输入的文字翻译成日文
import hashlib
import json
import random
import time
from typing import Dict, Union, List, Any
import requests
from astrbot.core import logger
def translate_by_google(text, to="ja"):
    """使用Google翻译文本（默认翻译为简体中文）"""
    # API: https://www.jianshu.com/p/ce35d89c25c3
    # client参数的选择: https://github.com/lmk123/crx-selection-translate/issues/223#issue-184432017
    logger.info(f"开始调用谷歌翻译API，输入: {text}")
    start_time = time.time()
    global _google_trans_wait
    url = f"https://translate.google.com/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&hl=zh-CN&sl=auto&tl={to}&q={text}"
    r = requests.get(url)
    logger.info(f"谷歌翻译API响应: {r.status_code}")
    while r.status_code == 429:
        logger.warning(f"HTTP {r.status_code}: {r.reason}: Google翻译请求超限，将等待{_google_trans_wait}秒后重试")
        time.sleep(_google_trans_wait)
        r = requests.get(url)
        if r.status_code == 429:
            _google_trans_wait += random.randint(60, 90)
    if r.status_code == 200:
        result = r.json()
    else:
        result = {'error_code': r.status_code, 'error_msg': r.reason}
    sentences = result["sentences"]
    end_time = time.time()
    logger.info(f"翻译完成，耗时 {end_time - start_time:.2f} 秒")
    return "".join([sentence["trans"] for sentence in sentences])

class BaiduTranslator():
    """
    百度翻译API封装类

    功能:
    - 支持多种语言互译
    - 自动签名生成
    - 错误处理
    - 结果解析

    使用示例:
    translator = BaiduTranslator()
    result = translator.translate("hello", from_lang="en", to_lang="zh")
    print(result)
    """

    # 支持的语言代码映射
    LANGUAGE_MAP = {
        'auto': '自动检测',
        'zh': '中文',
        'en': '英语',
        'jp': '日语',
        'kor': '韩语',
        'fra': '法语',
        'spa': '西班牙语',
        'th': '泰语',
        'ara': '阿拉伯语',
        'ru': '俄语',
        'pt': '葡萄牙语',
        'de': '德语',
        'it': '意大利语',
        'el': '希腊语',
        'nl': '荷兰语',
        'pl': '波兰语',
        'bul': '保加利亚语',
        'est': '爱沙尼亚语',
        'dan': '丹麦语',
        'fin': '芬兰语',
        'cs': '捷克语',
        'rom': '罗马尼亚语',
        'slo': '斯洛文尼亚语',
        'swe': '瑞典语',
        'hu': '匈牙利语',
        'cht': '繁体中文',
        'vie': '越南语'
    }

    # 错误代码映射
    ERROR_MESSAGES = {
        52000: '成功',
        52001: '请求超时',
        52002: '系统错误',
        52003: '未授权用户',
        54000: '必填参数为空',
        54001: '签名错误',
        54003: '访问频率受限',
        54004: '账户余额不足',
        54005: '长query请求频繁',
        58000: '客户端IP非法',
        58001: '译文语言方向不支持',
        58002: '服务当前已关闭',
        90107: '认证未通过或未生效'
    }

    def __init__(self, appid: str, secret_key: str):
        """初始化翻译器"""
        self.api_url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

        # 获取API凭证
        self.appid = appid
        self.secret_key = secret_key

        logger.info(f"appid: {self.appid} secret_key: {self.secret_key}")

        if not all([self.appid, self.secret_key]):
            logger.error("百度翻译API配置不完整，请检查config.ini文件")
            raise ValueError("百度翻译API配置不完整")

    def _generate_sign(self, query: str, salt: str) -> str:
        """
        生成API请求签名

        参数:
            query: 要翻译的文本
            salt: 随机盐值

        返回:
            MD5签名字符串
        """
        sign_str = f"{self.appid}{query}{salt}{self.secret_key}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def translate(
            self,
            query: str,
            from_lang: str = 'auto',
            to_lang: str = 'jp',
             ** kwargs
    ) -> None | dict[str, str] | dict[str, str] | dict[str, str] | dict[str, str] | dict[str, str | Any] | dict[
        str, str] | dict[str, str] | Any:
        """
        执行翻译操作

        参数:
            query: 要翻译的文本
            from_lang: 源语言代码(默认auto)
            to_lang: 目标语言代码(默认zh)
            kwargs: 其他API参数

        返回:
            翻译结果字典或错误信息
        """
        if not query:
            logger.warning("翻译请求为空")
            return {'error': 'Empty query'}

        # 验证语言代码
        if from_lang not in self.LANGUAGE_MAP:
            logger.warning(f"不支持的源语言代码: {from_lang}")
            return {'error': f'Unsupported source language: {from_lang}'}

        if to_lang not in self.LANGUAGE_MAP:
            logger.warning(f"不支持的目标语言代码: {to_lang}")
            return {'error': f'Unsupported target language: {to_lang}'}

        salt = str(random.randint(32768, 65536))
        sign = self._generate_sign(query, salt)

        params = {
            'q': query,
            'from': from_lang,
            'to': to_lang,
            'appid': self.appid,
            'salt': salt,
            'sign': sign,
             ** kwargs
        }

        try:
            logger.info(f"发送翻译请求: {query[:50]}... (from {from_lang} to {to_lang})")
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"收到API响应: {json.dumps(result, ensure_ascii=False)}")

            if 'error_code' in result:
                error_code = result.get('error_code')
                error_msg = self.ERROR_MESSAGES.get(error_code, '未知错误')
                logger.error(f"API返回错误: {error_code} - {error_msg}")
                return {
                    'error': error_msg,
                    'error_code': error_code
                }

            trans_results = result.get('trans_result', [])
            for trans_result in trans_results:
                return trans_result.get('dst', '')

        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
        except json.JSONDecodeError:
            logger.error("无效的JSON响应")
            return {'error': 'Invalid JSON response'}
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            return {'error': f'Unexpected error: {str(e)}'}

    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表"""
        return self.LANGUAGE_MAP.copy()