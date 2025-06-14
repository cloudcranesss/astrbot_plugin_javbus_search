# 调用谷歌翻译将输入的文字翻译成日文
import random
import time
import requests
from astrbot.core import logger, AstrBotConfig

def translate(text, to="ja"):
    """使用Google翻译文本（默认翻译为简体中文）"""
    # API: https://www.jianshu.com/p/ce35d89c25c3
    # client参数的选择: https://github.com/lmk123/crx-selection-translate/issues/223#issue-184432017
    config = AstrBotConfig()
    proxy = config.get("google_proxy",  "")
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    else:
        proxies = None
    global _google_trans_wait
    url = f"https://translate.google.com.hk/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=auto&tl={to}&q={text}"
    r = requests.get(url, proxies=proxies)
    while r.status_code == 429:
        logger.warning(f"HTTP {r.status_code}: {r.reason}: Google翻译请求超限，将等待{_google_trans_wait}秒后重试")
        time.sleep(_google_trans_wait)
        r = requests.get(url,  proxies=proxies)
        if r.status_code == 429:
            _google_trans_wait += random.randint(60, 90)
    if r.status_code == 200:
        result = r.json()
    else:
        result = {'error_code': r.status_code, 'error_msg': r.reason}
    time.sleep(4)  # Google翻译的API有QPS限制，因此需要等待一段时间
    sentences = result["sentences"]
    return "".join([sentence["trans"] for sentence in sentences])

if  __name__ == "__main__":
    print(translate("hello"))