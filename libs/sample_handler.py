#!/usr/bin/env python
# -*- encoding: utf-8 -*-


"""
from libs.base_handler import *
import re
from lxml import etree
import requests
import os


def url_similarity(ori_url, my_url):
    ori_str_list1 = ori_url.split('//')
    ori_str_list2 = ori_str_list1[1].split('/')
    my_str_list1 = my_url.split('//')
    my_str_list2 = my_str_list1[1].split('/')
    # 定义域名
    ori_domain = ori_str_list1[0] + '//' + ori_str_list2[0]
    my_domain = my_str_list1[0] + '//' + my_str_list2[0]
    if ori_domain not in my_domain:
        return False
    # 定义深度
    ori_depth = len(ori_str_list2)
    my_depth = len(my_str_list2)
    if my_depth != ori_depth:
        return False

    # # 倒数第二层目录是否一致
    # if my_depth > 2:
    #     if ori_str_list2[ori_depth - 2] != my_str_list2[my_depth - 2]:
    #         return False

    # 是否都包含相同数目的‘_’
    if len(ori_url.split('_')) != len(my_url.split('_')):
        return False

    #####
    if '_' in ori_url and '_' in my_url:
        ori_list = ori_url.split('_')
        my_list = my_url.split('_')
        if len(ori_list) != len(my_list):
            return False
        for i in range(len(ori_list) - 1):
            if ori_list[i] != my_list[i]:
                return False


    # 结尾相似度
    ori_end_page = ori_str_list2[len(ori_str_list2) - 1]
    my_end_page = my_str_list2[len(my_str_list2) - 1]
    ori_end_list = ori_end_page.split('.')
    my_end_list = my_end_page.split('.')
    # if my_end_list[1] != ori_end_list[1]:
    #     return False

    print ori_end_list[0], my_end_list[0]
    if re.match('\\d+$', ori_end_list[0]) and not re.match('\\d+$', my_end_list[0]):
        return False

    if not re.match('\\d+$', ori_end_list[0]) and re.match('\\d+$', my_end_list[0]):
        return False

    return True

def get_info(content, key, inspired_word, extract_content):
    key_index = content.index(inspired_word)
    value_index = content[key_index:].index(extract_content) + len(content[: key_index])
    end_str_index = value_index + len(extract_content)
    end_str = content[end_str_index: end_str_index + 4]
    info[key] = (value_index - key_index, end_str, inspired_word)
    print info

def get_value(content, key):
    inspired_word = info[key][2]
    print inspired_word
    if inspired_word not in content:
        return ''
    key_index = content.index(inspired_word)

    value_index = key_index + info[key][0]
    if info[key][1] not in content[value_index:]:
        return '找不到结尾词'
    end_index = content[value_index:].index(info[key][1]) + len(content[: value_index])
    value = content[value_index: end_index]
    value = re.sub('<[^>]+>', '', value)
    value = re.sub('&[^>]+;', '', value)
    value = value.strip()
    return value 
    
info = {}

column_dict = '__COLUMN_DICT__'
column_dict = dict(eval(column_dict))

index_url = '__BEGIN_URL__'
host = index_url.split('//')[0] + '//' + index_url.split('//')[1].split('/')[0]

class Handler(BaseHandler):
    detail_page_content = str(requests.get('__DETAIL_PAGE_URL__').content)
    for k, v in column_dict.iteritems():
        if v['inspired_word'] == '' or v['extract_content'] == '':
            continue
        get_info(detail_page_content, k, v['inspired_word'], v['extract_content'])
    
    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('__BEGIN_URL__', callback=self.index_page)
        print info

    @config(age=12 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            url = each.attr.href
            if url[0: 1] == '/':
                url += host
            #抓取详细页面
            if url_similarity('__DETAIL_PAGE_URL__', url):
                self.crawl(each.attr.href, callback=self.detail_page, save={'url': url})

            #抓取下一个索引页面
            if url_similarity('__NEXT_PAGE_URL__', url):
                self.crawl(each.attr.href, callback=self.index_page)

    @config(priority=2)
    def detail_page(self, response): 
        content = response.content
        output_dict = {}


        for k in info:
            output_dict[k] = get_value(content, k)


        if output_dict['项目编号']:
            f_name = output_dict['项目编号']
        else:
            return

        if '/' in f_name:
            f_name = f_name.replace('/', '-')

        dir = '__SAVE_PATH__' + '/' + f_name
        if os.path.exists(dir):
           return
        os.mkdir(dir)
        file_name = dir + '/' +  f_name + '.txt'

        output = open(file_name, 'w')
        try:
            output.write('{')
            for k, v in output_dict.iteritems():
                s = '"' + k + '"' + ': ' + '"' + v + '", '
                output.write(s)
            output.write('}')
            # output.write(content)
        finally:
            output.close()
            
        return output_dict
"""
