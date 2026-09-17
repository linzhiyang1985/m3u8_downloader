import os
from fetch_ts_files_from_m3u8_list import backup_command, download_m3u8, get_m3u8_file_content

def prepare_m3u8(m3u8_url, local_dir, start_index=0, end_skip_count=0):
    backup_command(m3u8_url, local_dir, start_index, end_skip_count)

    if not os.path.exists(os.path.join(local_dir, 'm3u8.txt')):
        print(f'Preparing m3u8 {local_dir}')
        get_m3u8_file_content(m3u8_url, local_dir)

def download_one(m3u8_url, local_dir, start_index=0, end_skip_count=0):
    download_m3u8(m3u8_url, local_dir, start_index, end_skip_count)

if __name__ == '__main__':
    ### Settings ###
    root_folder = 'dongcheng_liexiong'

    m3u8_list = '''
01,冬城猎凶第01集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260910/16717_fb4aedfd/index.m3u8
02,冬城猎凶第02集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260910/16722_18a06202/index.m3u8
03,冬城猎凶第03集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260910/16721_6eb4a96f/index.m3u8
04,冬城猎凶第04集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260910/16723_a532bcbe/index.m3u8
05,冬城猎凶第05集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260911/16797_e6f8b907/index.m3u8
06,冬城猎凶第06集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260911/16802_d6d8adb6/index.m3u8
07,冬城猎凶第07集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260912/16855_30c5e8b3/index.m3u8
08,冬城猎凶第08集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260912/16859_a162d1c4/index.m3u8
09,冬城猎凶第09集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260913/16896_4f60a32f/index.m3u8
10,冬城猎凶第10集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260914/16937_a74f5c6f/index.m3u8
11,冬城猎凶第11集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260915/16995_214c2d93/index.m3u8
12,冬城猎凶第12集在线观看-电视剧-西瓜影视,https://v.lzcdn27.com/20260916/17032_6f8eb8d0/index.m3u8
'''.splitlines()

    url_list = [line.split(',') for line in m3u8_list if line.strip()]
    url_dir_pairs = []
    for id, title, url in url_list:
        url_dir_pairs.append((url, f'{root_folder}{'/' if root_folder else ''}{id}'))
    ######

    ### batch parse m3u8 ###
    for url, path in url_dir_pairs:
        prepare_m3u8(url, path, start_index=0, end_skip_count=0)

    ### Download ###
    for url, path in url_dir_pairs:
        print(f'==== Downloading {path} ====')
        download_one(url, path)
    ######
