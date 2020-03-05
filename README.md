# MSFC Searcher

帮助你在 [项目检索 |国家自然科学基金管理信息系统](https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list) 检索，并生成CSV格式的报告。
**实现验证码识别，支持官网所有查询参数，直接支持跨年度查询。**

> 国自然结题报告下载： [Rhilip/NSFC_conclusion_downloader](https://github.com/Rhilip/NSFC_conclusion_downloader)

## 核心思路

1. 通过 `https://isisn.nsfc.gov.cn/egrantindex/validatecode.jpg` 获得验证码图片，使用pytesseract识别，并通过接口 `https://isisn.nsfc.gov.cn/egrantindex/funcindex/validate-checkcode` 验证OCR结果是否正确。
2. 构造并请求 `https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list` 获取额外的cookies信息。
3. 使用回调的形式，依次构造并请求 `https://isisn.nsfc.gov.cn/egrantindex/funcindex/prjsearch-list?flag=grid` 获得xml信息，并将其整理形成CSV文件。

## 使用说明

1. 安装 Python3 , pip , 以及 tesseract （例子为 在Powershell中使用scoop安装 ）

    ```powershell
    iwr -useb get.scoop.sh | iex
    scoop install python tesseract
    ```

2. 下载项目，并安装 Python 依赖

    ```powershell
    git clone https://github.com/Rhilip/NSFC_Searcher.git
    cd NSFC_Searcher
    pip install -r requirements.txt
    ```

3. 运行项目，并替换相关参数 （例子为 检索 `2005年及2010-2020年间` 在 `E0407.矿山修复工程` 的所有`面上项目` ）

    ```powershell
    python official.py --subjectCode E0407 --grantCode 218 --year 2005,2010-2020
    ```
 
    你也可以在其他项目中使用如下示例代码进行批量下载
    ```python
    from official import NsfcOfficial
    
    nsfc_official = NsfcOfficial()
    year='2008,2010-2019'
    for subjectCode in ['E0407','D070107']:
        for grantCode in [218,630]:
            nsfc_official.search(subjectCode=subjectCode, grantCode=grantCode, year=year)
    ```

4. 你会在当前目录 得到类似 `out_.csv` 文件，使用Excel打开即可

## 命令行使用

```
(venv) .\NSFC_Searcher>python official.py --help
缓存 .\cache\official_grand_code_main.json 存在，从缓存中读取
usage: official.py [-h] [--prjNo PRJNO] [--ctitle CTITLE] [--psnName PSNNAME]
                   [--orgName ORGNAME] --subjectCode SUBJECTCODE --grantCode
                   GRANTCODE [--subGrantCode SUBGRANTCODE]
                   [--helpGrantCode HELPGRANTCODE] [--keyWords KEYWORDS]
                   --year YEAR

在国自然官网 https://isisn.nsfc.gov.cn/ 搜索并整理成CSV格式的工具

optional arguments:
  -h, --help            show this help message and exit
  --prjNo PRJNO         批准号
  --ctitle CTITLE       项目名称
  --psnName PSNNAME     项目负责人
  --orgName ORGNAME     单位名称
  --subjectCode SUBJECTCODE
                        申请代码（必填） 例如 E0407
  --grantCode GRANTCODE
                        资助类别（必填） 例如 218 （即面上项目）
  --subGrantCode SUBGRANTCODE
                        亚类说明
  --helpGrantCode HELPGRANTCODE
                        附注说明
  --keyWords KEYWORDS   项目主题词
  --year YEAR           批准年度 默认为当前年度 ，多年度或跨年度使用英文 , - 连接 ， 例如 2004,2009-2019
```

## 其他

- 本项目会在 `./cache` 目录下留下缓存信息 `*.json`， 里面所有文件皆可删除，但该文件夹请勿删除，如果不小心删除请新建同名空白文件夹。
- 资助类别对应关系如下，见 `./cache/official_grand_code_main.json`
    ```json
    {
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
    ```