import os
import sys
import subprocess

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])

ad_md5sum_list = (
    '253eeb83328ce5350c8572cc470498a8',
    '43f63583a70df7d3e52fc84a975adabd',
    '55ec588b184dfb561f5eeabdcd7b7c4b',
    '576bfb474cc221eb3b1f345ea76fd23f',
    '586e2700be73de2bc6e509129c85704f',
    '61b4e405ef4bc9697bf3760c73b1f6b3',
    '6d553f551f3ddcab1048a9aeaf2c27f6',
    '822dc8f66836b5f05bc6c7ddfc0bdee1',
    '8a01af08240cb3fc56d976985650e8f5',
    'a1f9a9ac417a60774079cfdbb31d9432',
    'cc4ce468030820f7dbdbd2794ad941df',
    'dd174d6df1f4ebabde3ba67de4a75455',
    'e20dca7f38c7799fc6c7ef7444308025',
    'f7d79d73b5d368e67d93716672e61492',
    'c6f7e428dadce8dc820474722f68a728',
    '4ae66cc31f23a184d35a53fcc87bc5e2',
    '6156a13caeb99f8ddff76b7743aa5252',
    'bd5d74ccbb8480e799f3a25b5cc17256',
    '2ee512a54329fc7e03591213fb9a1881',
    '6f213cadb7eb780ed22c247e0b3e5058',
    'be8a7d23df4ed30d080108eb0632f303',
    '50e33bf199be3a505242f5a368545286',
    '33c74f24c78f35341a1882e459d6e78e',
    'c57c21baaf1b7cbbb25e0c171c7fd364',
    '33f14b9e1465556e1a3ded31f47aef61',
    '9ba826db4215b6920ca3035882bd4e35',
    'ea52124e69a45a94b50200e21eb737d2',
    'c769fcff760727375b497390d10723ba',
    '02bf42f9e79344d4392fc8059ed5fe22',
    'c865a1d722df83fe30954a47fbbaf8c1',
    'e3f54ee03c07b2dffb4a80ba601deb40',
    'a2b332c8b212750b3ed2965c932e54f6',
)

p = subprocess.Popen('md5sum *.ts', shell=True, stdout=subprocess.PIPE)
out = p.stdout.readlines()

for line in out:
    line = line.decode().strip()
    md5, file = line.split()
    if md5 in ad_md5sum_list:
        print('delete file: ', line)
        os.system(f'rm {file}')