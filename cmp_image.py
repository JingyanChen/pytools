import argparse
import multiprocessing
import os
import pathlib
import shutil
import subprocess
import sys

src_path= 'E:\\lambertliu\\weekly\\OGL_Benchmark\\heaven_640x480_tess_enable\\ReplayDump\\'
#src_path= 'D:\\log\LogVK\\deqp-vk_2023.10.07_10.34\\data'
dst_path= 'E:\\lambertliu\\weekly\\OGL_Benchmark\\heaven_640x480_tess_enable-\\ReplayDump\\'

ext_name='ivk'

def main():
    for file in os.listdir(src_path):
        if file.endswith(ext_name):
            src_file = src_path + "\\" + file
            dst_file = dst_path + "\\" + file
            cmd = 'qReplay.exe --intE 0 --floatE 0.00 --r0 i --r1 i  --i0 '
            cmd = cmd + src_file
            cmd = cmd + '  --i1 '
            cmd = cmd + dst_file
            os.system(cmd)



if __name__ == '__main__':
    main()
