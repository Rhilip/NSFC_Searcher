import os
import io
import csv
import json
import requests
import pytesseract
from PIL import Image

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.34 Safari/537.36'


def json_cache(cache_file: str, func: callable):
    if os.path.exists(cache_file):
        print('缓存 %s 存在，从缓存中读取' % (cache_file,))
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print('缓存 %s 不存在，开始获取' % (cache_file,))
        data = func()
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print('数据写入缓存 %s 成功' % (cache_file,))

        return data


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT
    })
    return session


def validate_code_ocr(img_content: bytes) -> str:
    i = Image.open(io.BytesIO(img_content))
    img = i.convert("L")
    return pytesseract.image_to_string(img)


def get_main_grant() -> dict:
    cache_file = os.path.join('.', 'cache', 'official_grand_code_main.json')

    def main_grant():
        return {
            "630": "青年科学基金项目",
            "631": "地区科学基金项目",
            "218": "面上项目",
            "632": "海外及港澳学者合作研究基金",
            "220": "重点项目",
            "222": "重大项目",
            "339": "重大研究计划",
            "429": "国家杰出青年科学基金",
            "432": "创新研究群体项目",
            "433": "国际(地区)合作与交流项目",
            "649": "专项基金项目",
            "579": "联合基金项目",
            "70": "应急管理项目",
            "7161": "科学中心项目",
            "635": "国家基础科学人才培养基金",
            "2699": "优秀青年科学基金项目",
            "8531": "专项项目",
            "51": "国家重大科研仪器设备研制专项",
            "52": "国家重大科研仪器研制项目",
            "2733": "海外或港、澳青年学者合作研究基金"
        }

    return json_cache(cache_file, main_grant)


def get_sub_grant(grand_code, type_='grant') -> list:
    """
    获取所有资助类别的 亚类说明 (grant) 以及 附注说明 (sub)，返回结果例如如下
    [
        {"subGrantName":"面上项目","subGrantCode":340},
        ...
    ]
    """
    cache_file = os.path.join('.', 'cache', 'official_grand_code_%s_%s.json' % (type_, grand_code))

    def get_support_date_remote():
        return create_session().get('https://isisn.nsfc.gov.cn/egrantindex/funcindex/get-allSubGrant', params={
            "grantCode": grand_code, "type": type_
        }).json()

    return json_cache(cache_file, get_support_date_remote)


def csv_writer(path, header, data):
    with open(path, 'w', encoding='utf-8-sig') as f:
        f_csv = csv.DictWriter(f, header, dialect=csv.unix_dialect)
        f_csv.writeheader()
        f_csv.writerows(data)
