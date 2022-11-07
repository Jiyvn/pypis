import requests
import sys
from bs4 import BeautifulSoup


base_uri = "https://pypi.org"
column_spacing = {'NAME':25, 'VERSION':10, 'LAST UPDATE': 10, 'ADDRESS':45, 'DESCRIPTION':40}

def get_params():
    if len(sys.argv)<2:
        print("search keyword is must. pls deliver at least one param (keyword)")
        sys.exit(1)

    keyword = sys.argv[1]

    sort_by = "r"
    if len(sys.argv)>2:
        sort_by = sys.argv[2]
        if sort_by not in ('r', 'd', 't'):
            print('''"{}" is not expected. 'r' for relevance, 'd' for update date, 't' for trending.'''.format(sort_by))
            sys.exit(1)
    return keyword, sort_by


def parse_result_bs4(html_text:str) -> list:
    results = []
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
    results = parse_result_bs4(res.text)

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

    # print columns
    print(column_formatter.format(**column_formatter_params))

    # print results
    for pkg in pkgs:
        lines = {}
        for col, col_string in pkg.items():
            space = len(col) + spacings[col]
            v_len = len(pkg[col])
            line_amount = v_len/space
            if line_amount >= 1:
                for i in range(int(line_amount)):
                    if str(i) not in lines.keys():
                        lines[str(i)] = {}
                    lines[str(i)].update({col:col_string[i*space:(i+1)*space]})
                if line_amount > int(line_amount):
                    if str(int(line_amount)) not in lines.keys():
                        lines[str(int(line_amount))] = {}
                    lines[str(int(line_amount))].update({col:col_string[int(line_amount)*space:]})

            else:
                if "0" not in lines.keys():
                    lines['0'] = {}
                lines['0'][col] = col_string

        if len(lines.keys()) > 1:
            for i in range(len(lines.keys())):
                for col, col_string in pkg.items():
                    if col not in lines[str(i)].keys():
                        lines[str(i)][col] = ""

        for k, v in lines.items():
            print(formatter.format(**v))


beautify_output(search(*get_params()), column_spacing)

