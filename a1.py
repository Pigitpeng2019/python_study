#! /bin/python
import requests
import bs4
import re
import time
import random

url = 'www.baidu.com'
url = 'https://www.douban.com/group/topic/28938988/'
headers = {
     'User-Agent':
         'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
         '115.0.0.0 Safari/537.36 Edg/115.0.1901.188'
 }
bs4_text = requests.get(url=url, headers=headers)
print("value:", requests.get(url=url, headers=headers).text)
print("miss fush code changes at home")
