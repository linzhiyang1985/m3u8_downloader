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
    root_folder = 'jiao_feng'
    num_dir = 1









    url_list = (
'https://v.lfthirtytwo.com/20260906/10215_743533c9/index.m3u8',
'https://v.lfthirtytwo.com/20260906/10214_05e3c9a4/index.m3u8',
'https://v.lfthirtytwo.com/20260906/10213_f5fee75d/index.m3u8',
'https://v.lfthirtytwo.com/20260906/10221_9af9bd2d/index.m3u8',
'https://v.lfthirtytwo.com/20260907/10273_73bc3f3d/index.m3u8',
'https://v.lfthirtytwo.com/20260907/10272_c6900d24/index.m3u8',
'https://v.lfthirtytwo.com/20260908/10335_e8523b2d/index.m3u8',
'https://v.lfthirtytwo.com/20260908/10336_c8548851/index.m3u8',
'https://v.lzcdn27.com/20260909/16664_cd31263b/index.m3u8',
'https://v.lzcdn27.com/20260909/16669_48737468/index.m3u8',
'https://v.lzcdn27.com/20260910/16736_0e5632a9/index.m3u8',
'https://v.lzcdn27.com/20260910/16760_a28b5736/index.m3u8',
'https://v.lzcdn27.com/20260911/16808_0136f2ce/index.m3u8',
'https://v.lzcdn27.com/20260911/16811_841c9f4b/index.m3u8',
'https://v.lzcdn27.com/20260912/16862_6ad3385a/index.m3u8',
'https://v.lzcdn27.com/20260912/16865_2031cf7a/index.m3u8',
'https://v.lzcdn27.com/20260913/16898_749a7ec4/index.m3u8',
'https://v.lzcdn27.com/20260913/16900_790d0aaa/index.m3u8',
'https://v.lzcdn27.com/20260914/16939_1a765b7b/index.m3u8',
'https://v.lzcdn27.com/20260914/16941_496f75c5/index.m3u8',
    )

    url_dir_pairs = []
    for url in url_list:
        url_dir_pairs.append((url, f'{root_folder}{'/' if root_folder else ''}{num_dir:02d}'))
        num_dir += 1
    ######

    ### batch parse m3u8 ###
    for url, path in url_dir_pairs:
        prepare_m3u8(url, path, start_index=0, end_skip_count=0)

    ### Download ###
    for url, path in url_dir_pairs:
        print(f'==== Downloading {path} ====')
        download_one(url, path)
    ######