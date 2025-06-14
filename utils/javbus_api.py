import random

import requests
from typing import Optional, List, Dict, Any


class JavBusAPI:
    def __init__(self, base_url: str = None):
        """
        初始化JAVBUS API客户端

        :param base_url: API基础URL，默认为https://www.javbus.com
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def get_movies(
            self,
            page: int = 1,
            magnet: str = "exist",
            filter_type: Optional[str] = None,
            filter_value: Optional[str] = None,
            movie_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        获取影片列表

        :param page: 页码，默认为1
        :param magnet: 磁力链接筛选，'exist'或'all'，默认为'exist'
        :param filter_type: 筛选类型，可选'star','genre','director','studio','label','series'
        :param filter_value: 筛选值，必须与filter_type一起使用
        :param movie_type: 影片类型，'normal'或'uncensored'，默认为'normal'
        :return: 包含影片列表和分页信息的字典
        """
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
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def search_movies(
            self,
            keyword: str,
            page: int = 1,
            magnet: str = "exist",
            movie_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        搜索影片

        :param keyword: 搜索关键词
        :param page: 页码，默认为1
        :param magnet: 磁力链接筛选，'exist'或'all'，默认为'exist'
        :param movie_type: 影片类型，'normal'或'uncensored'，默认为'normal'
        :return: 包含影片列表和分页信息的字典
        """
        params = {
            'keyword': keyword,
            'page': page,
            'magnet': magnet,
            'type': movie_type
        }

        url = f"{self.base_url}/api/movies/search"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_movie_detail(self, movie_id: str) -> Dict[str, Any]:
        """
        获取影片详情

        :param movie_id: 影片ID（番号）
        :return: 包含影片详细信息的字典
        """
        url = f"{self.base_url}/api/movies/{movie_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def get_magnets(
            self,
            movie_id: str,
            gid: str,
            uc: str,
            sort_by: str = "size",
            sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        获取影片磁力链接

        :param movie_id: 影片ID（番号）
        :param gid: 从影片详情获取的gid
        :param uc: 从影片详情获取的uc
        :param sort_by: 排序字段，'date'或'size'，默认为'size'
        :param sort_order: 排序顺序，'asc'或'desc'，默认为'desc'
        :return: 磁力链接列表
        """
        params = {
            'gid': gid,
            'uc': uc,
            'sortBy': sort_by,
            'sortOrder': sort_order
        }

        url = f"{self.base_url}/api/magnets/{movie_id}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_star_detail(
            self,
            star_id: str,
            star_type: str = "normal"
    ) -> Dict[str, Any]:
        """
        获取演员详情

        :param star_id: 演员ID
        :param star_type: 演员类型，'normal'或'uncensored'，默认为'normal'
        :return: 包含演员详细信息的字典
        """
        params = {
            'type': star_type
        }

        url = f"{self.base_url}/api/stars/{star_id}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_star_by_name(self, star_name: str) -> dict[str, Any] | None:
        """
        根据演员名称获取演员信息
        :param star_name: 演员名称
        :return: 包含演员详细信息的字典
        """
        # 先根据演员名称获取影片列表
        star_id = ""
        movie_lists = self.search_movies(star_name)
        # 随机获取影片ID
        num = random.randint(0, len(movie_lists["movies"]) - 1)
        movie_id = movie_lists["movies"][num]["id"]

        # 根据影片ID获取影片详情
        movie_details = self.get_movie_detail(movie_id)
        for movie_detail in movie_details["stars"]:
            if movie_detail['name'] == star_name:
                star_id = movie_detail['id']

        if star_id:
            star_details = self.get_star_detail(star_id)
            return star_details
        else:
            return None

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 使用示例
# if __name__ == "__main__":
#     with JavBusAPI() as api:
#         # 获取第一页有磁力链接的影片
#         movies = api.get_movies()
#         print(f"获取到 {len(movies['movies'])} 部影片")
#
#         # 搜索关键词为"三上"的影片
#         search_result = api.search_movies(keyword="三上")
#         print(f"搜索到 {len(search_result['movies'])} 部相关影片")
#
#         # 获取特定影片详情
#         movie_detail = api.get_movie_detail("SSIS-406")
#         print(f"影片标题: {movie_detail['title']}")
#
#         # 获取影片磁力链接
#         if 'gid' in movie_detail and 'uc' in movie_detail:
#             magnets = api.get_magnets(
#                 movie_id="SSIS-406",
#                 gid=movie_detail['gid'],
#                 uc=movie_detail['uc']
#             )
#             print(f"获取到 {len(magnets)} 个磁力链接")
#
#         # 获取演员详情
#         star_detail = api.get_star_detail("2xi")
#         print(f"演员姓名: {star_detail['name']}, 年龄: {star_detail['age']}")