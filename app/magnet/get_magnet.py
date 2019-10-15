from lxml import html

import requests
from requests.exceptions import Timeout
from app.config import PROXIES, FAKE_HEADERS, REQUEST_TIME_OUT
from ..tools.get_original_magnet import get_original_magnet
from ..exceptions.error import HttpError
from app.const import *


def get_magnet(source: dict, keyword: str, page: int, sorted_by: int = SORTED_BY_DEFAULT) -> dict:
    '''
    :param source: 从rules导入的字典，规定了各参数和xpath提取规则
    :param keyword: 查询的关键词
    :param page: 查询的页数
    :param sorted_by: 排序规则，可根据大小、日期、热度倒序排序
    :return: 资源字典
    '''
    source_name = source.get('source_name')
    base_url = source.get('base_url')
    # 根据规则对参数进行转化
    temp_sorted_by = format_query_paras(source=source, sorted_by=sorted_by)[0]
    request_url = base_url + source.get('query_tail').format(keyword=keyword, page=page, sorted_by=temp_sorted_by)
    proxy_channel = source.get('proxy_channel')  # 判断是否走代理通道
    if proxy_channel:
        proxies = PROXIES
    else:
        proxies = None
    try:
        response = requests.get(request_url, proxies=proxies, headers=FAKE_HEADERS, timeout=REQUEST_TIME_OUT)
        if response.status_code == 200:
            response_text = str(response.content, 'utf-8')
            response_xpath = html.fromstring(response_text)
            has_result = response_xpath.xpath(source.get('judge_result_xpath'))  # 判断是否有结果
            if not has_result:
                raise IndexError
            else:
                content_list = response_xpath.xpath(source.get('content_list_xpath'))
                for a_content in content_list:
                    title_content = a_content.xpath(source.get('title_content_xpath'))[0]
                    for title_strip_tap in source.get('title_strip_tags'):
                        html.etree.strip_tags(title_content, title_strip_tap)  # 删除在title_strip_tags中的标签,保留内容
                    title = ''.join(title_content.xpath('text()')).strip()
                    try:
                        magnet = get_original_magnet(a_content.xpath(source.get('magnet_xpath'))[0]).strip()  # 格式化mangnet
                    except:
                        magnet = MAGNET_NOT_FOUND
                    try:
                        create_date = a_content.xpath(source.get('create_date_xpath'))[0].strip()
                    except:
                        create_date = CREATE_DATE_NOT_FOUND
                    try:
                        size = a_content.xpath(source.get('size_xpath'))[0].strip()
                    except:
                        size = SIZE_NOT_FOUND
                    try:
                        popular = a_content.xpath(source.get('popular_xpath'))[0].strip()
                    except:
                        popular = POPULAR_NOT_FOUND

                    a_result_dict = {
                        'title': title,
                        'magnet': magnet,
                        'size': size,
                        'create_date': create_date,
                        'popular': popular,
                        'source_name': source_name
                    }
                    yield a_result_dict
        else:
            raise HttpError(response.status_code, f'在请求{source_name}时远程主机返回错误')
    except Timeout:
        raise


def format_query_paras(source: dict, sorted_by: int) -> tuple:
    if sorted_by == SORTED_BY_DEFAULT:
        return (source.get('sorted_by').get('default'),)
    elif sorted_by == SORTED_BY_DATE:
        return (source.get('sorted_by').get('date'),)

    elif sorted_by == SORTED_BY_POPULAR:
        return (source.get('sorted_by').get('popular'),)
    elif sorted_by == SORTED_BY_SIZE:
        return (source.get('sorted_by').get('size'),)
    else:
        raise IndexError
