import re
import sys

class submitInfo:
    def __init__(self):
        # 实例变量
        self.lineNum = 0
        self.cb = 0

    def set_lineNum(self,lineNum):
        self.lineNum = lineNum;
    def set_cb(self,cb):
        self.cb = cb;

def analyze_submitlayout(file_path):
    submitInfoArray = []
    try:
        with open(file_path, 'r') as file:
            script_code = file.read()

            # 获取总行数
            total_lines = len(script_code.split('\n'))

            # 分析每一行代码
            info = submitInfo()
            for i, line in enumerate(script_code.split('\n'), start=1):  
                if("vkQueueSubmit" in line):
                    info.set_lineNum(i)
                    submitInfoNameMatch = re.search(r'vkQueueSubmit+\((.*?), (.*?), (.*?), (.*?)\);', line)
                    submitInfoName = submitInfoNameMatch.group(3)
                    
                    submitInfoMatch = re.search(f'{submitInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                    submitInfoStr = submitInfoMatch.group(2)
                    
                    #print(submitInfoStr)
                    cbMatch = re.search(r'pCommandBuffers\s*=\s*\[\d+\]\((.*?)\)', submitInfoStr)
                    #print(cbMatch.group(1))
                    info.set_cb(cbMatch.group(1))   
                    
                    submitInfoArray.append(info)
                    info = submitInfo()
    except FileNotFoundError:
        print("open file error")

    return submitInfoArray

def analyze_cmdBuffer_draw_distapatch_count(file_path,cmdBuf):
    try:
        with open(file_path, 'r') as file:
            script_code = file.read()
            count = 0
            for i, line in enumerate(script_code.split('\n'), start=1):  
                if(cmdBuf in line and 'vkCmdDraw' in line):
                    count = count + 1
                if(cmdBuf in line and 'vkCmdDispatch' in line):
                    count = count + 1
    except FileNotFoundError:
        print("open file error")

    return count

class cmdCountObj:
    def __init__(self,cb,count):
        # 实例变量
        self.cb = cb
        self.count = count
        
def get_count(obj):
    if isinstance(obj, cmdCountObj):
        return obj.count

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
    else:
        file_path = sys.argv[1]
        submitInfoArray = analyze_submitlayout(file_path)
        
    array = []
    totalLen = len(submitInfoArray)
    cb_count = 0
    for submitInfo in submitInfoArray:
        #print(f'{submitInfo.lineNum},{submitInfo.cb}')
        cbList = submitInfo.cb.split(',')
        for cb in cbList:
            ref_count = analyze_cmdBuffer_draw_distapatch_count(file_path,cb.strip(' '))
            obj = cmdCountObj(cb.strip(' '),ref_count)
            array.append(obj)
            print(f"process {cb_count}/{totalLen}")
            cb_count = cb_count + 1
            #print(f'{obj.cb},ref_count = {obj.count}')
            
    sorted_objects = sorted(array, key=get_count)
    
    for obj in sorted_objects:
        print(f'{obj.cb},ref_count = {obj.count}')