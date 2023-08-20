#! /bin/python
import requests
from bs4 import BeautifulSoup
# import test_csv
import csv
import re
import pymysql
import numpy as np
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar
import matplotlib.pyplot as plt


def get_one_page(url):
    """
    获取一级页面内容
    """
    headDict = {
        # 加入自己的“user_agent:”、“accept“、”cookie“

    }

    r = requests.get(url, headers=headDict)
    r.encoding = r.apparent_encoding
    html = r.text
    return html


def parse_one_page(html):
    """
    解析获取的页面
    电影排名、片名、评分、评价人数、电影类型、制片国家、上映时间、电影时长
    在一级页面爬取了制片国家（二级也可以爬取），其他指标都在二级爬取
    运用了find、select，也可以用xpath、re
    """
    soup = BeautifulSoup(html, 'lxml')
    movie = soup.find("ol", class_='grid_view')
    print("movie", movie)
    erjilianjie = movie.find_all('li')

    for lianjie in erjilianjie:
        #  一级页面制片国家
        others = lianjie.find('div', class_='bd').find('p').text.strip('').split('\n')
        year_country = others[2].strip('').split('\xa0/\xa0')
        pro_country = year_country[1].replace(' ', ',')

        # 链接
        a = lianjie.find('a')
        erji = a['href']
        html = get_one_page(erji)

        soup = BeautifulSoup(html, 'lxml')
        # 排名
        ranks = soup.select('#content > div.top250 > span.top250-no')[0].getText().strip()
        # 片名
        spans = soup.select('h1 span')
        movie_name1 = spans[0].get_text()
        movie_name = movie_name1.split(' ')[0]
        # print(movie_name)
        # 评分
        score = soup.select('#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > strong')[
            0].getText().strip()
        # 评价人数
        sorce_people = soup.select(
            '#interest_sectl > div.rating_wrap.clearbox > div.rating_self.clearfix > div > div.rating_sum > a > span')[
            0].getText().strip()
        # info板块
        info = soup.find('div', id='info')
        # 电影类型
        movie_type = ''
        movie_types = info.find_all('span', property='v:genre')
        for i in movie_types:
            movie_type = movie_type + ',' + i.string
            movie_type = movie_type.lstrip(',')
        # 二级页面制片国家
        # pro_country = re.findall("<span class=\"pl\">制片国家/地区:</span>(.*)<br/>",str(info))
        # pro_country = ','.join(pro_country)
        # print(pro_country)
        # 上映日期
        up_time = ''
        up_times = info.find_all('span', property='v:initialReleaseDate')
        for i in up_times:
            up_time = up_time + "," + i.string
            up_time = up_time.lstrip(',')
        # 电影时长
        movie_time = ''
        movie_times = info.find_all('span', property='v:runtime')
        for i in movie_times:
            movie_time = movie_time + i.string

        # 将数据写入data，做迭代器储存数据
        data = {
            'id': ranks,
            'name': movie_name,
            'score': score,
            'votes': sorce_people,
            'country': pro_country,
            'type': movie_type,
            'date': up_time,
            'runtime': movie_time,
            'link': erji
        }
        # return data
        yield data


def write_to_file(content):
    """
    写入csv文件
    """
    file_name = 'movie.csv'
    with open(file_name, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for i in content:
            writer.writerow(i.values())


def write_to_table():
    # 连接MYSQL数据库（注意：charset参数是utf8m64而不是utf-8）
    db = pymysql.connect(host="localhost",
                         user='root',
                         password='123456',
                         database="database_test",
                         db="movie",
                         charset="utf8m64", )
    # 创建对象
    cursor = db.cursor()

    # 读取csv文件
    with open('movie.csv', 'r', encoding='utf-8') as f:
        read = csv.reader(f)
        for each in list(read):
            i = tuple(each)
            # print(i)
            # SQL语句添加数据
            sql = "INSERT INTO movie VALUES" + str(i)
            # 执行SQL语句
            cursor.execute(sql)
        # 提交数据
        db.commit()
        # #关闭游标
        cursor.close()
        # #关闭数据库
        db.close()


def pandas_movie():
    """
    jupyter读取movie.csv中数据并处理
    """
    # 如果没有header = None，会自动将第一行设置为表头哦
    data = pd.read_table('movie.csv', sep=',', header=None)
    data

    data.isnull().any()  # 查看是否有缺失值数据
    data.duplicated().sum()  # 查看是否有重复值数据

    data.columns = ['排名', '片名', '评分', '评价人数', '制片国家',
                    '类型', '上映日期', '时长', '影片链接']
    data

    data.to_csv('movie1.csv')  # 保存处理好的数据到movie1.csv


def pyecharts_movie():
    """
    绘制电影评价人数前十名(柱状图)
    """
    # 读取movie1.csv文件数据
    data = pd.read_csv('movie1.csv')
    df = data.sort_values(by='评价人数', ascending=True)
    bar = (
        plt.bar
        # Bar()
        .add_xaxis(df['片名'].values.tolist()[-10:])
        .add_yaxis('评价人数', df['评价人数'].values.tolist()[-10:])
        .set_global_opts(
            title_opts=opts.TitleOpts(title='电影评价人数'),
            yaxis_opts=opts.AxisOpts(name='人数'),
            xaxis_opts=opts.AxisOpts(name='片名'),
            datazoom_opts=opts.DataZoomOpts(type_='inside'),
        )
        .set_series_opts(label_opts=opts.LabelOpts(position="top"))
        .render('电影评价人数前十名.html')
    )
    # bar

    # 制片国家里有几个国家一起的情况，要先用
    # " “代替”,“，用” "
    # 分割，再用count计算每个国家的数量

    country_all = data['制片国家'].str.replace(",", " ").str.split(" ", expand=True)
    country_all = country_all.apply(pd.value_counts).fillna(0).astype("int")
    country_all['count'] = country_all.apply(lambda x: x.sum(), axis=1)
    country_all.sort_values('count', ascending=False)
    data1 = country_all['count'].sort_values(ascending=False).head(10)

    country_counts = data1
    country_counts.columns = ['制片国家', '数量']
    country_counts = country_counts.sort_values(ascending=True)
    bar = (
        Bar()
        .add_xaxis(list(country_counts.index)[-10:])
        .add_yaxis('地区上映数量', country_counts.values.tolist()[-10:])
        .reversal_axis()
        .set_global_opts(
            title_opts=opts.TitleOpts(title='地区上映电影数量'),
            yaxis_opts=opts.AxisOpts(name='国家'),
            xaxis_opts=opts.AxisOpts(name='上映数量'),
        )
        .set_series_opts(label_opts=opts.LabelOpts(position="right"))
        .render('各地区上映电影数量前十.html')
    )
    bar

    # 绘制电影时长分布直方图

    movie_duration_split = data['时长'].str.replace("\', \'", "~").str.split("~", expand=True).fillna(0)
    movie_duration_split = movie_duration_split.replace(regex={'分钟.*': ''})
    data['时长'] = movie_duration_split[0].astype("int")
    # data['时长'].head()
    # 查看最大时长
    # data.时长.max()

    bins = [0, 80, 100, 120, 140, 160, 180, 240]
    pd.cut(data.时长, bins)
    pd.cut(data.时长, bins).value_counts()
    pd.cut(data.时长, bins).value_counts().plot.bar(rot=20)


if __name__ == "__main__":
    for i in range(10):
        urls = 'https://movie.douban.com/top250?start=' + str(i * 25) + '&filter='
        html = get_one_page(urls)
        parse_one_page(html)
        content = parse_one_page(html)
        write_to_file(content)
        print("写入第" + str(i) + "页数据成功")
        # 将movie.csv里的数据传入movie表
        # write_to_table()

    # # 调试函数
    # url = 'https://movie.douban.com/top250'
    # html = get_one_page(url)
    # parse_one_page(html)
    # content = parse_one_page(html)

