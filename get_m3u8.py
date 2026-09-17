import requests
import re
import sys
from urllib.parse import quote

DEBUG = False

if __name__ == '__main__':
    if DEBUG:
        start_page_url = 'https://www.wfhchuang.com/vodplay/46169-1-2.html'
    else:
        if len(sys.argv) <= 1:
            print('USAGE: python get_m3u8.py <start_page_url>')
            sys.exit(1)

        start_page_url = sys.argv[1]

def parse_host(url):
    return re.findall(r'(http[s]?://[^/]+)', url)[0]

def get_title(page_text):
    title = re.findall(r'<title>(.*?)</title>', page_text)[0]
    try:
        return '_'.join(title.split('_')[:2])
    except:
        return title


session = requests.Session()
session.headers.update({'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'})

def get_m3u8_and_next_page(host, url):
    global session

    response = session.get(url)
    if response.status_code >= 400:
        print(response.status_code)
        response = session.get(url) # request again with cookies
    if response.status_code == 200:
        script_fragment = re.findall(r'.*(<script.*?m3u8.*?</script>).*', response.text)
        if script_fragment:
            script_fragment = script_fragment[0]
            # link = re.findall(r'"link":"(.*?)"', script_fragment)[0].replace('\\', '')
            m3u8_url = re.findall(r'"url":"(.*?/index.m3u8)"', script_fragment)[0].replace('\\/', '/')

            # process unicode
            unicodes = re.findall(r'\\u[0-9a-f]{4}', m3u8_url)
            if unicodes:
                for match_code in unicodes:
                    m3u8_url = m3u8_url.replace(match_code, chr(int(match_code[-4:], 16)))
                m3u8_url = quote(m3u8_url).replace('%3A', ':')
            # process unicode end

            # if r'"link_next":""' in script_fragment:
            #     link_next = ''
            # else:
            try:
                link_next =  re.findall(r'"link_next":"(.*?)"', script_fragment)[0].replace('\\', '')
                if link_next:
                    link_next = host + link_next
            except:
                link_next = ''

            if not link_next:
                try:
                    link_next = re.findall(r'"next":"(.*?)"', script_fragment)[0].replace('\\', '')
                except:
                    link_next = ''
            title = get_title(response.text)
            return title, m3u8_url, link_next
    return '', '', ''


if __name__ == '__main__':
    page_url = start_page_url
    host = parse_host(start_page_url)
    while True:
        title, m3u8_url, link_next = get_m3u8_and_next_page(host, page_url)
        print(title)
        print(link_next)
        print(m3u8_url)
        if link_next:
            page_url = link_next
        else:
            break
