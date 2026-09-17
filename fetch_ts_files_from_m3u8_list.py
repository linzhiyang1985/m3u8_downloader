import re

import requests
import os
import sys
import time
import json
from pathlib import Path
from threading import Thread
from Crypto.Cipher import AES

DEBUG = False


FLAGS = {'stop': False}

HEADERS = {'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'}

if __name__ == '__main__':
    if DEBUG:
        m3u8_url = 'https://v.lzcdn27.com/20260910/16717_fb4aedfd/index.m3u8'
        local_dir = 'winter_murder_hunter/01'
        start_index = 0
        end_skip_count = 0
    else:
        if len(sys.argv) < 3:
            print('Usage: python fetch_ts_files_from_m3u8_list.py <m3u8_url> <local_dir> [start_index] [end_skip_count]')
            sys.exit(1)
        m3u8_url = sys.argv[1]
        local_dir = sys.argv[2]

        start_index = 0
        end_skip_count = 0
        if len(sys.argv) > 3:
            start_index = int(sys.argv[3])
        if len(sys.argv) > 4:
            end_skip_count = int(sys.argv[4])

def parse_home_url(m3u8_url):
    return '/'.join(m3u8_url.split('/')[:-1]) + '/'

def correct_download_link(segment_index, home_url, original_file_name, seg_str_len, local_dir):
    file_path = original_file_name
    if '/video/' in file_path:
        file_path = file_path.split('/')[-1]
    if '?' in file_path:
        file_path = file_path.split('?')[0]
    local_file_path = f'{local_dir}/{segment_index:0{seg_str_len}d}_{file_path.split('/')[-1]}'

    if os.path.exists(local_file_path):
        print(f'{local_file_path} already exists')
        file_url = ''
    else:
        if original_file_name.startswith('http'):
            file_url = original_file_name
        else:
            if '/video/' in original_file_name:
                file_url = home_url[:home_url.index('/video/')] + original_file_name
            else:
                file_url = home_url + original_file_name

    return file_url, local_file_path

def get_m3u8_file_content(url, save_path=''):
    global HEADERS

    content = '.m3u8'
    new_url = url

    while new_url:
        response = requests.get(new_url, headers=HEADERS)
        response.encoding='utf-8'
        content = response.text
        home_url = parse_home_url(new_url)

        if '.m3u8' in content:
            m3u8_links = [line for line in content.split() if '.m3u8' in line]
            if m3u8_links:
                m3u8_link = m3u8_links[0]
                new_url = home_url + m3u8_link
        else:
            new_url = ''
    
    ## support save to file
    if content and '.m3u8' not in content and save_path:
        os.makedirs(save_path, exist_ok=True)
        with open(os.path.join(save_path, 'm3u8.txt'), 'w') as fp:
            fp.writelines([home_url+os.linesep, content])

    return home_url, content

def parse_m3u8_file_content(content, home_url):
    enc_key = ''
    iv = b''
    lines = content.splitlines()
    file_names_in_order = []
    for line in lines:
        if line.startswith('#'):
            if 'EXT-X-KEY' in line:
                enc_key_uri = re.findall('URI="(.+)"', line)[0]
                # fetch key file and extract key content
                resp = requests.get(home_url + enc_key_uri, headers=HEADERS)
                if resp.status_code == 200:
                    enc_key = resp.content
                iv = bytes.fromhex(re.findall('IV=(.+)', line)[0][-32:])
            else:
                continue
        if 'adjump' in line:
            print('skip adjump:', line)
            continue
        if line.endswith('.ts') or '.ts?' in line:
            file_names_in_order.append(line)
    return file_names_in_order, enc_key, iv

def prepare_m3u8_file_content(m3u8_url, local_dir):
    if os.path.exists(os.path.join(local_dir, 'm3u8.txt')):
        with open(os.path.join(local_dir, 'm3u8.txt'), 'r') as fp:
            home_url = fp.readline().strip()
            m3u8_file_content = fp.read()
    else:
        home_url, m3u8_file_content = get_m3u8_file_content(m3u8_url, local_dir)
    file_names_in_order, enc_key, iv = parse_m3u8_file_content(m3u8_file_content, home_url)
    return file_names_in_order, enc_key, iv, home_url

def download_ts_file(url, local_file_path, enc_key, iv):
    global HEADERS

    response = requests.get(
        url,
        headers=HEADERS,
        allow_redirects=True,
        stream=True
    )
    if enc_key:
        # AES-128
        decipher = AES.new(enc_key, AES.MODE_CBC, iv)
    else:
        decipher = None

    with open(local_file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                if decipher:
                    chunk = decipher.decrypt(chunk)
                f.write(chunk)
    print(f'Downloaded {local_file_path}')

def backup_command(m3u8_url, local_dir, start_index=0, end_skip_count=0):
    os.makedirs(local_dir, exist_ok=True)
    command = f'python fetch_ts_files_from_m3u8_list.py {m3u8_url} {local_dir} {start_index} {end_skip_count}'
    if Path(os.path.abspath(local_dir)).is_relative_to(Path.cwd()):
        relative_path = Path(os.path.abspath(local_dir)).relative_to(Path.cwd())
    else:
        relative_path = ''
    with open(os.path.join(local_dir, 'exec.sh'), 'w') as f:
        if relative_path:
            f.write(f'cd {('..' + os.sep) * len(relative_path.parts)}'[:-1] + os.linesep)
        f.write(command + os.linesep)

def download_m3u8(m3u8_url, local_dir, start_index=0, end_skip_count=0):
    file_names_in_order, enc_key, iv, home_url = prepare_m3u8_file_content(m3u8_url, local_dir)
    
    os.makedirs(local_dir, exist_ok=True)
    
    total_segments = len(file_names_in_order)
    seg_str_len = len(str(total_segments))

    for l in range(3):
        segment_index = start_index # skip starting song
        threads = []
        new_download = False
        while segment_index < total_segments - end_skip_count: # skip ending caption
            original_file_name = file_names_in_order[segment_index]

            file_url, local_file_path = correct_download_link(segment_index, home_url, original_file_name, seg_str_len, local_dir)

            if file_url:
                new_download = True
                try:
                    t = Thread(target=download_ts_file, args=(file_url, local_file_path, enc_key, iv))
                    t.start()
                    threads.append(t)
                    print(f'Downloading segment {segment_index + 1}/{total_segments}')
                except requests.exceptions.ConnectionError:
                    print(f'Connection error: {file_url}')
                    time.sleep(3)
                    continue
            segment_index += 1

            if FLAGS['stop']:
                print('!!!!! stop download')
                break
            
            if len(threads) == 5:
                for t in threads:
                    t.join()
                threads = []

        if threads:
            for t in threads:
                t.join()


        if not new_download:
            print(f"loop {l}: No more file to download, end loop")
            break

if __name__ == '__main__':
    backup_command(m3u8_url, local_dir, start_index, end_skip_count)
    download_m3u8(m3u8_url, local_dir, start_index, end_skip_count)
    print('All segments downloaded')
    print('\a') # alarm sound
    
