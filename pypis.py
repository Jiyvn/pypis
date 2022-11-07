import re
import requests
import sys

from bs4 import BeautifulSoup



base_uri = "https://pypi.org"
column_spacing = {'NAME':25, 'VERSION':10, 'LAST UPDATE': 10, 'ADDRESS':45, 'DESCRIPTION':40}

# s = requests.Session()
# s.get(base_uri)

def get_params():
    if len(sys.argv)<2:
        print("search keyword is must. pls deliver at least one param (keyword)")
        sys.exit(1)

    keyword = sys.argv[1]
    # print("keyword: {}".format(keyword))

    sort_by = "r"
    if len(sys.argv)>2:
        sort_by = sys.argv[2]
        if sort_by not in ('r', 'd', 't'):
            print('''"{}" is not expected. 'r' for relevance, 'd' for update date, 't' for trending.'''.format(sort_by))
            sys.exit(1)
    # print("sorted by: {}".format(sort_by))
    return keyword, sort_by


def parse_result_re(html_text:str) -> list:
    results = []
    re_pattern = r'(<a.*href="/project/.*">(?:(?:\r\n|\n)(?:(?!</a>).)*)+</a>)'
    # match_result = re_pattern.finditer(result_html, re.M|re.I)
    match_result = re.findall(re_pattern, html_text, re.M | re.I)
    # print(f"match_result: \n{match_result.__next__()}")

    re_pattern_name = r'package-snippet__name(?:(?!>).)*>((?:(?!>).)*)<'
    re_pattern_version = r'package-snippet__version(?:(?!>).)*>((?:(?!>).)*)<'
    re_pattern_date = r'package-snippet__created.*>\n((?:(?!>).)*)\n<'
    re_pattern_addr = r'href="((?:(?!").)*)"'
    re_pattern_desc = r'package-snippet__description(?:(?!>).)*>((?:(?!>).)*)<'
    for mr in match_result:
        proj = {}
        re_match = re.findall(re_pattern_name, mr, re.M|re.I)
        proj['NAME'] = re_match[0].strip()
        re_match = re.findall(re_pattern_version, mr, re.M|re.I)
        proj['VERSION'] = re_match[0].strip()
        re_match = re.findall(re_pattern_date, mr, re.M|re.I)
        proj['LAST UPDATE'] = re_match[0].strip()
        re_match = re.findall(re_pattern_addr, mr, re.M|re.I)
        proj['ADDRESS'] = base_uri+re_match[0].strip()
        re_match = re.findall(re_pattern_desc, mr, re.M|re.I)
        proj['DESCRIPTION'] = re_match[0].strip()
        results.append(proj)
    return results

def parse_result_bs4(html_text:str) -> list:
    results = []
    # soup = BeautifulSoup(open("request_search_result.html"), 'html.parser')
    soup = BeautifulSoup(html_text, 'html.parser')
    for a_tag in soup.find_all('a'):
        proj = {}
        if str(a_tag.get('href')).startswith('/project/'):
            proj['NAME'] = a_tag.h3.find("span", {"class": "package-snippet__name"}).text.strip()
            proj['VERSION'] = a_tag.h3.find("span", {"class": "package-snippet__version"}).text.strip()
            proj['LAST UPDATE'] = a_tag.h3.find("span", {"class": "package-snippet__created"}).text.strip()
            proj['ADDRESS'] = base_uri + a_tag.get('href')
            proj['DESCRIPTION'] = a_tag.find("p", {"class": "package-snippet__description"}).text.strip()
            results.append(proj)

    return results



def search(query_word:str, order:str="r")-> list:
    """
    relevance = ""
    last_update = "-created"
    trending = "-zscore"
    """
    sort_type = "" if order=="r" else "-created" if order=="d" else "-zscore"
    query_url = base_uri+"/search/?q={0}&o={1}".format(query_word, sort_type)
    header = {
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:99.0) Gecko/20100101 Firefox/99.0"
    }
    res = requests.get(url=query_url, headers=header)
    # res.encoding="gb2312"

    result_html = res.text
    # with open("./search_result.html", mode="w", encoding='utf-8') as f:
    #     f.write(result_html)

    results = parse_result_re(result_html)
    # results = parse_result_bs4(result_html)

    return results


def beautify_output(pkgs: list[dict], spacings:dict=None):
    if not pkgs:
        print("Nothing found.")
        return
    columns = list(pkgs[0].keys())
    formatter = ''
    column_formatter = ''
    column_formatter_params = {}
    for i in range(len(columns)):
        formatter = formatter + '{'+f'{columns[i]}'+f':<{(25 if not spacings else spacings[columns[i]])+len(columns[i])}'+'}'
        column_formatter = column_formatter + f'{columns[i]}'+'{'+f'{columns[i]}'+f':<{25 if not spacings else spacings[columns[i]]}'+'}'
        column_formatter_params[f'{columns[i]}'] = ''
    # print("formatter: {}".format(formatter))
    # print("column_formatter: {}".format(column_formatter))
    # print("column_formatter_params: {}".format(column_formatter_params))

    # print column
    print(column_formatter.format(**column_formatter_params))

    re_pattern = r'[^{].+:<\d+'
    matches = re.findall(re_pattern, formatter, re.M | re.I)
    lengths = [m[1:] for m in matches]

    for pkg in pkgs:
        lines = {}
        # print("pkg: {}".format(pkg))
        for col, col_string in pkg.items():
            space = len(col) + spacings[col]
            v_len = len(pkg[col])
            line_amount = v_len/space
            if line_amount >= 1:
                for i in range(int(line_amount)):
                    if str(i) not in lines.keys():
                        lines[str(i)] = {}
                    lines[str(i)].update({col:col_string[i*space:(i+1)*space-1]})
                if line_amount > int(line_amount):
                    if str(int(line_amount)) not in lines.keys():
                        lines[str(int(line_amount))] = {}
                    lines[str(int(line_amount))].update({col:col_string[int(line_amount)*space:]})

            else:
                if "0" not in lines.keys():
                    lines['0'] = {}
                lines['0'][col] = col_string

            # print("col: {}".format(col))
            # print("col_string: {}".format(col_string))

        if len(lines.keys()) > 1:
            for i in range(len(lines.keys())):
                for col, col_string in pkg.items():
                    if col not in lines[str(i)].keys():
                        lines[str(i)][col] = ""

        # print("lines-final: {}".format(lines))
        for k, v in lines.items():
            print(formatter.format(**v))

# search(*get_params())
beautify_output(search(*get_params()), column_spacing)

# ss = "{NAME:<29}{VERSION:<17}{LAST UPDATE:<21}{ADDRESS:<52}{DESCRIPTION:<51}"
# # re_pattern = r'[^{].+\:<\d+'
# re_pattern = r'((?!\{).)*:<\d+'
# matches = re.findall(r'(((?!\{).)*:<\d+)', ss, re.M|re.I)
# # matches = re.finditer(r'((?!\{).)*:<\d+', ss, re.M|re.I)
# # print(ss)
# print(matches)
# # print(matches.__next__())
# # print(matches.__next__())

# sss = '''<a class="package-snippet" href="/project/jenkins-validate/">
#     <h3 class="package-snippet__title">
#       <span class="package-snippet__name">jenkins-validate</span>
#       <span class="package-snippet__version">0.0.12</span>
#       <span class="package-snippet__created"><time datetime="2021-01-07T08:02:31+0000" data-controller="localized-time" data-localized-time-relative="true" data-localized-time-show-time="false">
#   Jan 7, 2021
# </time></span>
#     </h3>
#     <p class="package-snippet__description">An auto validate package about jenkins</p>
#   </a>
# '''
