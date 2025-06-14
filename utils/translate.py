# 调用谷歌翻译将输入的文字翻译成日文
import random
import time
import requests
from astrbot.core import logger

def translate(text, to="ja"):
    """使用Google翻译文本（默认翻译为简体中文）"""
    # API: https://www.jianshu.com/p/ce35d89c25c3
    # client参数的选择: https://github.com/lmk123/crx-selection-translate/issues/223#issue-184432017
    logger.info(f"开始调用谷歌翻译API，输入: {text}")
    start_time = time.time()
    global _google_trans_wait
    url = f"https://translate.google.com/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=auto&tl={to}&q={text}"
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

if  __name__ == "__main__":
    print(translate("hello"))