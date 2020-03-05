"""
通过官网 https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list 查询相关项目，并生成CSV文件
"""

import os
import time
import argparse
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup

import utils

all_grant_code = utils.get_main_grant()


def parse_year(args_year: str) -> list:
    """
    解析 2004,2009-2013 字符串 到 [2004,2009,2010,2011,2012,2013] 列表
    """
    years = []
    for y in args_year.split(','):
        if y.find('-') == -1:
            years.append(int(y))
        else:
            start_year, end_year = y.split('-')
            years.extend(list(range(int(start_year), int(end_year) + 1)))
    return list(set(filter(lambda x: 1997 <= x <= time.localtime().tm_year, years)))  # 去除不在范围内 + 去重


def check_grant_code(grant_code, sub_grant_code, help_grant_code):
    if str(grant_code) not in all_grant_code.keys():
        raise RuntimeError('资助类别代码 %s 错误，请重新输入' % grant_code)
    else:
        print('资助类别代码 %s 对应 %s' % (grant_code, all_grant_code[grant_code]))

    if sub_grant_code:
        all_sub_grant_code = utils.get_sub_grant(grant_code, 'grant')
        for test_code in all_sub_grant_code:
            if int(sub_grant_code) == test_code['subGrantCode']:
                print('亚类说明代码 %s 对应 %s' % (sub_grant_code, test_code['subGrantName']))
                break
        else:
            raise RuntimeError('亚类说明代码 %s 不符合 资助类别代码 %s ，请重新输入' % (sub_grant_code, grant_code))

    if help_grant_code:
        all_help_grant_code = utils.get_sub_grant(sub_grant_code, 'sub')
        for test_code in all_help_grant_code:
            if int(help_grant_code) == test_code['subGrantCode']:
                print('亚类说明代码 %s 对应 %s' % (help_grant_code, test_code['subGrantName']))
                break
        else:
            raise RuntimeError('附注说明代码 %s 不符合 亚类说明代码 %s ，请重新输入' % (help_grant_code, sub_grant_code))


def arg_parser():
    parser = argparse.ArgumentParser(description='在国自然官网 https://isisn.nsfc.gov.cn/ 搜索并整理成CSV格式的工具')

    parser.add_argument('--prjNo', default='', help='批准号')
    parser.add_argument('--ctitle', default='', help='项目名称')
    parser.add_argument('--psnName', default='', help='项目负责人')
    parser.add_argument('--orgName', default='', help='单位名称')
    parser.add_argument('--subjectCode', required=True, help='申请代码（必填） 例如 E0407 ')
    parser.add_argument('--grantCode', required=True, help='资助类别（必填） 例如 218 （即面上项目） ')
    parser.add_argument('--subGrantCode', default='', help='亚类说明')
    parser.add_argument('--helpGrantCode', default='', help='附注说明')
    parser.add_argument('--keyWords', default='', help='项目主题词')
    parser.add_argument('--year', default=time.localtime().tm_year, required=True,
                        help='批准年度 默认为当前年度 ，多年度或跨年度使用英文 , - 连接 ， 例如 2004,2009-2019 ')

    # 解析命令并转化为字典对象
    args = vars(parser.parse_args())
    check_grant_code(args['grantCode'], args['subGrantCode'], args['helpGrantCode'])  # 检查grantCode是否允许
    args['year'] = parse_year(args['year'])  # 分解year

    return args


class NsfcOfficial:
    session: requests.Session = None
    subject_dict: dict = None

    def __init__(self):
        self.session = utils.create_session()
        self.__load_subject_dict()
        print('初始化 搜索器 %s 成功' % (__class__,))

    def __load_subject_dict(self):
        cache_file = os.path.join('.', 'cache', 'official_subject_dict.json')
        self.subject_dict = utils.json_cache(cache_file, lambda: self.session.get(
            'https://isisn.nsfc.gov.cn/egrantindex/cpt/ajaxload-tree?locale=zh_CN&key=subject_code_index&cacheable=true&sqlParamVal='
        ).json())

    def get_validate_code(self):
        time.sleep(1)

        # 获取验证码并使用pytesseract识别
        img_req = self.session.get('https://isisn.nsfc.gov.cn/egrantindex/validatecode.jpg')
        result = utils.validate_code_ocr(img_req.content)

        # 校验验证码是否正确
        check = self.session.post('https://isisn.nsfc.gov.cn/egrantindex/funcindex/validate-checkcode', data={
            "checkCode": result
        })
        if check.text == 'error':
            return self.get_validate_code()
        else:
            print('验证码 %s 验证成功' % (result,))
            return result

    def __get_search_key(self, **kwargs):
        f_subject_code_hide_id = kwargs.get('subjectCode')
        for i in self.subject_dict:
            if i['id'] == f_subject_code_hide_id:
                kwargs['subjectCode'] = i['title']
                kwargs['f_subjectCode_hideId'] = i['id']
                kwargs['sqdm'] = i['id']
                break
        else:  # 没有找到对应的申请代码详细信息
            raise RuntimeError('输入的申请代码 %s 不合法', f_subject_code_hide_id)

        search_map = {
            "prjNo": kwargs.get('prjNo', ''),  # 批准号
            "ctitle": kwargs.get('ctitle', ''),  # 项目名称
            "psnName": kwargs.get('psnName', ''),  # 项目负责人
            "orgName": kwargs.get('orgName', ''),  # 单位名称
            "subjectCode": kwargs.get('subjectCode', ''),  # 申请代码 （长）   E0407.矿山修复工程
            "f_subjectCode_hideId": kwargs.get('f_subjectCode_hideId', ''),  # 申请代码 （短）   E0407
            "subjectCode_hideName": kwargs.get('subjectCode_hideName', ''),  # 应该也是申请代码，但是实际并没有用到
            "keyWords": kwargs.get('keyWords', ''),  # 项目主题词
            "checkcode": kwargs.get('checkcode', ''),  # 验证码
            "grantCode": kwargs.get('grantCode', ''),  # 资助类别
            "subGrantCode": kwargs.get('subGrantCode', ''),  # 亚类说明
            "helpGrantCode": kwargs.get('helpGrantCode', ''),  # 附注说明
            "year": kwargs.get('year', time.localtime().tm_year),  # 批准年度
            "sqdm": kwargs.get('sqdm', '')  # 申请代码 （短）
        }

        return ",".join([k + ':' + str(v) for k, v in search_map.items()])

    def __search_loop(self, search_key, page=1, checkcode=''):
        time.sleep(3)

        data = []

        print("请求分页 %s (使用验证码 %s)" % (page, checkcode))
        l1 = self.session.post(
            'https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list?flag=grid',
            params={'checkcode': checkcode},
            data={
                "_search": "false", "nd": int(time.time() * 100),
                "rows": 10, "page": page, "sidx": "", "sord": "desc",
                "searchString": "resultDate^:" + quote(
                    search_key) + "[tear]sort_name1^:psnName[tear]sort_name2^:prjNo[tear]sort_order^:desc"
            })

        bs = BeautifulSoup(l1.text, 'lxml')

        rows = bs.find_all('row')
        current_another = bs.page
        total_another = bs.total

        if rows and current_another and total_another:
            for row in rows:
                cells = row.find_all('cell')
                data.append({
                    'prjNo': cells[0].get_text(),  # 项目批准号
                    'subjectCode': cells[1].get_text(),  # 申请代码
                    'ctitle': cells[2].get_text(),  # 项目名称
                    'psnName': cells[3].get_text(),  # 项目负责人
                    'orgName': cells[4].get_text(),  # 依托单位
                    'totalAmt': cells[5].get_text(),  # 批准金额
                    'startEndDate': cells[6].get_text(),  # 项目起止年月
                })

            # 检查是否还有下一页
            current = int(bs.page.get_text())
            total = int(bs.total.get_text())
            if current < total:
                checkcode = self.get_validate_code()
                data.extend(self.__search_loop(search_key, current + 1, checkcode))

        return data

    def search(self, **kwargs):
        year = kwargs.setdefault('year', str(time.localtime().tm_year))
        if isinstance(year, str):
            year = parse_year(year)

        grant_code = kwargs.setdefault('grantCode', 218)  # 面上项目

        data = []
        for y in year:
            print('请求页面信息 grantCode: %s , year: %s' % (grant_code, y))
            checkcode = self.get_validate_code()
            kwargs['year'] = y
            main_search_key = self.__get_search_key(**kwargs)
            self.session.post('https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list', data={
                "resultDate": main_search_key,
                "checkcode": checkcode
            })

            year_data = self.__search_loop(main_search_key)

            def data_fix(d):
                d['year'] = y
                d['grantCode'] = all_grant_code[grant_code]
                return d

            data.extend(list(map(data_fix, year_data)))

        header = ['prjNo', 'subjectCode', 'ctitle', 'psnName', 'orgName', 'totalAmt', 'startEndDate', 'year',
                  'grantCode']
        utils.csv_writer(os.path.join('.', 'output', 'out_%s.csv' % (int(time.time()))), header, data)


if __name__ == '__main__':
    args = arg_parser()
    nsfc_official = NsfcOfficial()
    nsfc_official.search(**args)
