import re
import sys
import time

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
            drawCount = 0
            dispatchCount = 0
            
            drawSecondaryCount = 0
            dispatchSecondaryCount = 0
            
            for i, line in enumerate(script_code.split('\n'), start=1):  
                if((cmdBuf + ',') in line and 'vkCmdDraw' in line):
                    drawCount = drawCount + 1
                if((cmdBuf + ',') in line and 'vkCmdDispatch' in line):
                    dispatchCount = dispatchCount + 1

            #check secondary command buffer
            secondaryCmdMatch = re.search(f'vkCmdExecuteCommands+\({cmdBuf}, (.*?), (.*?)\);', script_code)
            if(secondaryCmdMatch != None):
                print("\r")
                cmdGroupName = secondaryCmdMatch.group(2)
                secondartCmdBufListMatch = re.search(f'{cmdGroupName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                secondaryCmdList = secondartCmdBufListMatch.group(2).split(',')
                secondaryCmdNum = secondartCmdBufListMatch.group(1)
                
                #print(f"found secnondary command buffer num = {secondaryCmdNum}  list = {secondaryCmdList}")
                total_task = len(secondaryCmdList)
                now_task = 1
                for secondaryCmdBuffer in secondaryCmdList:
                    tempo = int(now_task / total_task * 100)
                    print("\r", end="")
                    print("sub process: {}%: ".format(tempo), "▓" * (tempo // 2), end="")
                    sys.stdout.flush()
                    now_task = now_task + 1
                    for i, line in enumerate(script_code.split('\n'), start=1): 
                        cmdbufStr = secondaryCmdBuffer.strip(' ') + ','
                        if(cmdbufStr in line and 'vkCmdDraw' in line):
                            drawSecondaryCount = drawSecondaryCount + 1
                        if(cmdbufStr in line and 'vkCmdDispatch' in line):
                            dispatchSecondaryCount = dispatchSecondaryCount + 1   
                    #print(f"{secondaryCmdBuffer} SecDrawCount = {drawSecondaryCount} , SecDispatchCount = {dispatchSecondaryCount}")
                print("\r")
    except FileNotFoundError:
        print("open file error")

    #print(f'{cmdBuf},drawCount = {drawCount} , dispatchCount = {dispatchCount} ,SecDrawCount = {drawSecondaryCount} , SecDispatchCount = {dispatchSecondaryCount}')

    return drawCount + dispatchCount , dispatchSecondaryCount + drawSecondaryCount

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
    cb_count = 1

    for submitInfo in submitInfoArray:
        #print(f'{submitInfo.lineNum},{submitInfo.cb}')
        cbList = submitInfo.cb.split(',')
        for cb in cbList:
            pri_ref_count,second_ref_count = analyze_cmdBuffer_draw_distapatch_count(file_path,cb.strip(' '))
            obj = cmdCountObj(cb.strip(' '),pri_ref_count + second_ref_count)
            array.append(obj)
            
            tempo = int(cb_count / totalLen * 101)
            print("\r", end="")
            print("main process: {}%: ".format(tempo), "▓" * (tempo // 2), end="")
            sys.stdout.flush()
            #time.sleep(0.05)
    
            #print(f"process {cb_count}/{totalLen}")
            cb_count = cb_count + 1
            #print(f'{obj.cb},ref_count = {obj.count}')
            
    sorted_objects = sorted(array, key=get_count)
    
    print("\r")
    for obj in sorted_objects:
        print(f'{obj.cb},ref_count = {obj.count}')
