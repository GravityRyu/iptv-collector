#!/usr/bin/env python3

import requests
import re
from urllib.parse import urlparse


# IPTV源地址
SOURCE_URL = "https://raw.githubusercontent.com/bjzhou/iptv-collector/output/iptv-cm.txt"

# 输出文件
OUTPUT_FILE = "iptv-clean.txt"


# ==============================
# 购物频道关键词过滤列表
# 如果频道名称包含以下任意关键词，
# 将被认为是购物频道并删除
# ==============================
SHOP_KEYWORDS = [
    "购物",
    "商城",
    "优选",
    "精选",
    "TV购物",
    "电视购物",
    "百货",
    "直播间",
    "美妆",
    "珠宝",
    "拍卖",
    "团购",
    "好物",
    "直播",
    "游戏",
]


def is_shopping(name):
    """
    判断频道是否属于购物频道

    参数:
        name: 频道名称

    返回:
        True  : 是购物频道
        False : 普通频道
    """

    for keyword in SHOP_KEYWORDS:

        # 不区分大小写匹配
        if keyword.lower() in name.lower():
            return True

    return False



def get_ip_type(url):
    """
    判断 IPTV 地址类型

    返回:
        ipv6   : IPv6地址
        ipv4   : IPv4地址
        domain : 域名
        unknown: 无法判断

    示例:
        http://[2409::1]/xxx
            -> ipv6

        http://1.2.3.4/xxx
            -> ipv4

        http://example.com/xxx
            -> domain
    """

    try:

        # 解析URL，获取主机部分
        host = urlparse(url).hostname


        if host is None:
            return "unknown"


        # IPv6地址包含冒号
        # 例如:
        # 2409:8000::1
        if ":" in host:
            return "ipv6"


        # IPv4地址格式判断
        if re.match(
            r"^\d+\.\d+\.\d+\.\d+$",
            host
        ):
            return "ipv4"


        # 剩余情况认为是域名
        return "domain"


    except Exception:

        return "unknown"



def score(url):
    """
    给地址进行优先级评分

    优先级:
        IPv6  > IPv4 > 域名

    分数越高越优先保留
    """

    ip_type = get_ip_type(url)


    return {

        # IPv6最高优先级
        "ipv6": 3,

        # IPv4次之
        "ipv4": 2,

        # 域名最低
        "domain": 1,

        # 无法识别
        "unknown": 0

    }.get(ip_type, 0)



def download_source():
    """
    下载 IPTV 原始列表

    返回:
        文本内容
    """

    response = requests.get(
        SOURCE_URL,
        timeout=30
    )

    # HTTP错误直接抛出
    response.raise_for_status()


    return response.text



def parse(lines):
    """
    解析 IPTV 列表

    处理逻辑:

    1. 删除购物频道
    2. 相同频道只保留一个地址
    3. IPv6 > IPv4 > 域名

    返回:
        {
            频道名: 地址
        }
    """


    # 保存最终结果
    channels = {}


    for line in lines:


        # 去掉空格
        line = line.strip()


        # 空行跳过
        if not line:
            continue


        # IPTV文件可能包含注释
        # 例如 #EXTM3U
        if line.startswith("#"):
            continue


        try:

            # 默认格式:
            # 频道名称,url

            name, url = line.split(",", 1)


        except ValueError:

            # 格式错误跳过
            continue



        name = name.strip()
        url = url.strip()



        # 第一步:
        # 删除购物频道
        if is_shopping(name):
            continue



        # 第一次发现该频道
        if name not in channels:

            channels[name] = url



        else:

            # 已经存在同名频道
            old_url = channels[name]


            # 比较地址优先级
            # 如果新地址更优，则替换
            if score(url) > score(old_url):

                channels[name] = url



    return channels



def save(channels):
    """
    保存处理后的 IPTV 列表

    输出格式:
        频道名称,url
    """


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:


        for name, url in channels.items():

            f.write(
                f"{name},{url}\n"
            )



def main():

    print("正在下载 IPTV 列表...")


    # 下载原始数据
    data = download_source()



    print("正在处理频道...")


    # 分析并过滤
    channels = parse(
        data.splitlines()
    )



    print(
        f"处理完成，剩余频道数量: {len(channels)}"
    )



    # 写入文件
    save(channels)



    print(
        f"输出文件: {OUTPUT_FILE}"
    )



# Python程序入口
if __name__ == "__main__":

    main()
