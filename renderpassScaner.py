'''
renderpass sancer的基本功能要求
1, 扫描所有renderpass,以beginrenderpass 到 endrenderpass为一个单元，输出的文档里面要求能获得每一个扫出来的renderpass起始行号和结束行号
2, 扫描每个begin renderpass插入的fb和rp，获得每个renderpass操作的ds attachement name
3, 输出相同ds attachement 的分布
4, tbd 绘制cmdBuf 以及 submit 对应renderpass的分布
'''
import re
import sys

class renderpassInfo:
    def __init__(self):
        # 实例变量
        self.beginLine = 0
        self.endLine = 0
        self.drawNum = 0
        self.dispatchNum = 0
        self.rp = ""
        self.fb = ""
        self.dsImageName = ""
        self.colorImageNameList = []
        self.cb = ""

    def set_beginLine(self,beginLine):
        self.beginLine = beginLine;
    def set_endLine(self,endLine):
        self.endLine = endLine;
    def set_drawNum(self,drawNum):
        self.drawNum = drawNum;
    def set_dispatchNum(self,dispatchNum):
        self.dispatchNum = dispatchNum;
    def set_rp(self,rp):
        self.rp = rp;
    def set_fb(self,fb):
        self.fb = fb;
    def set_dsImageName(self,dsImageName):
        self.dsImageName = dsImageName;
    def set_cb(self,cb):
        self.cb = cb;
    def set_colorImageName(self,colorImageName):
        self.colorImageNameList.append(colorImageName);

def count_draw_dispatch_lines_between(script_code, start_line, end_line,cb):
    draw_lines = 0
    dispatch_lines = 0
    #print(f'{start_line} - {end_line}')
    for i, line in enumerate(script_code.split('\n'), start=1): 
        if(i >= start_line and i <= end_line):
            if "vkCmdDraw" in line and cb in line:
                draw_lines = draw_lines + 1
            if "vkCmdDispatch" in line and cb in line:
                dispatch_lines = dispatch_lines + 1
    return draw_lines, dispatch_lines

def analyze_renderpasses(file_path):
    begin_renderpass_lines = []
    end_renderpass_lines = []
    renderpassInfoArray = []
    
    try:
        with open(file_path, 'r') as file:
            script_code = file.read()

            # 获取总行数
            total_lines = len(script_code.split('\n'))

            # 分析每一行代码
            info = renderpassInfo()
            for i, line in enumerate(script_code.split('\n'), start=1):              
                if "vkCmdBeginRenderPass" in line:
                    begin_renderpass_lines.append(i)

                    match = re.search(f'vkCmdBeginRenderPass(?:2)?\((.*?), (.*?), (.*?)\);', line)
                    if match:
                        beginInfoName = match.group(2).strip()
                        beginCB = match.group(1)
                        info.set_cb(beginCB)
                        beginInfoName_match = re.search(f'{beginInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                        if beginInfoName_match:
                            render_pass_match = re.search(r'renderPass\s*=\s*([^,]+)', beginInfoName_match.group(2))
                            framebuffer_match = re.search(r'framebuffer\s*=\s*([^,]+)', beginInfoName_match.group(2))

                            if render_pass_match and framebuffer_match:
                                render_pass_value = render_pass_match.group(1).strip()
                                framebuffer_value = framebuffer_match.group(1).strip()

                                #print(f"Analyzing Renderpass pair {len(begin_renderpass_lines)} of {total_lines} lines:")
                                #print(f"   BeginRenderPass line: {i}")
                                #print(f"   renderPass value: {render_pass_value}")
                                #print(f"   framebuffer value: {framebuffer_value}")
                                
                                info.set_beginLine(i)
                                info.set_rp(render_pass_value)
                                info.set_fb(framebuffer_value)

                elif "vkCmdEndRenderPass(" + info.cb in line:
                    end_renderpass_lines.append(i)
                    #print(f"   EndRenderPass line: {end_renderpass_lines[-1] if end_renderpass_lines else 'N/A'}")
                    info.set_endLine(i)

                    #搜索renderpass中有多少个draw/dispatch
                    draw_lines, dispatch_lines = count_draw_dispatch_lines_between(script_code,info.beginLine,info.endLine,info.cb)
                    info.set_drawNum(draw_lines)
                    #info.set_dispatchNum(dispatch_lines)
                    
                    #搜索每个renderpass使用的depth img name
                    #搜索创建rb的create函数，获知rb create info 
                    #print(info.rp)
                    escaped_info_rp = re.escape(info.rp)
                    rb_definition = re.search(f'vkCreateRenderPass\d+\((.*?), (.*?), (.*?), {escaped_info_rp}\);', script_code)
                    
                    rb_createInfoName = rb_definition.group(2)
                    #print(rb_definition.group(2))
                    #通过create info name 确定subpass数量，以及每个subpass的ds attachement id
                    rb_definitionMatch = re.search(f'{rb_createInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                    #print(rb_definitionMatch.group(2))
                    rb_definition = rb_definitionMatch.group(2)
                    if(rb_definition):
                        #获取subpass数量
                        #TBD 暂时只考虑一个subpass count的情况
                        subpass_count_match = re.search(r'subpassCount\s*=\s*([^,]+)', rb_definition)
                        subpass_match = re.search(r'pSubpasses\s*=\s*([^,]+)', rb_definition)
                        subpass_count = subpass_count_match.group(1)
                        subpass = subpass_match.group(1)
                        if(int(subpass_count) != 1):
                                print(f"Error: only support one subpass. but has {subpass_count}")
                                sys.exit(1) 
                        #print(subpass)
                        if(subpass):
                            #寻找subpass的定义
                            subpass_match = re.search(f'{subpass}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                            if(subpass_match):
                                dsAttachmentId = None
                                subpass_createInfo = subpass_match.group(2)
                                #print(subpass_createInfo)
                                if("pDepthStencilAttachment = NULL," in subpass_createInfo):
                                    #print("NULL")
                                    pass
                                else:
                                    #print(subpass_createInfo)
                                    depthAttachmentId_match = re.search(r'pDepthStencilAttachment\s*=\s*\[1\]\((.*?)\)', subpass_createInfo, re.DOTALL)
                                    dsAttDes = depthAttachmentId_match.group(1)
                                    #print(dsAttDes)
                                    dsAttachmentIdMatch = re.search(r'attachment\s*=\s*(\d+)', dsAttDes)
                                    dsAttachmentId = dsAttachmentIdMatch.group(1)
                                    #print(dsAttachmentId)
                                    if(dsAttachmentId == None):
                                        print("get ds attachment id failed")
                                        sys.exit(1) 
                                    #print(dsAttachment.group(1))

                                colorAttachmentId = []
                                if("pColorAttachments = NULL," in subpass_createInfo):
                                    pass
                                else:
                                    #print(subpass_createInfo)
                                    if("attachment = (" in subpass_createInfo):
                                        color_attachment_match = re.search(r'attachment\s*=\s*\((\s*\d+\s*(?:,\s*\d+\s*)*)\)\s*,', subpass_createInfo, re.DOTALL)
                                        #print(color_attachment_match.group(0))
                                        colorAttachmentIdMatch = re.search(r'attachment\s*=\s*\((\d+(?:,\s*\d+)*)\)', color_attachment_match.group(0))
                                        #print(colorAttachmentIdMatch.group(1))
                                        colorAttachmentId = colorAttachmentIdMatch.group(1).split(',')
                                    else:
                                        colorAttachmentIdMatch = re.search(r'attachment\s*=\s*(\d+)', subpass_createInfo)
                                        colorAttachmentId.append(colorAttachmentIdMatch.group(1))
                                   
                    if(dsAttachmentId):
                        #通过ds id 到对应的framebuffer去找到对应的ImageView，最终确定imagename
                        escaped_info_fb = re.escape(info.fb)
                        fb_definition = re.search(f'vkCreateFramebuffer+\((.*?), (.*?), (.*?), {escaped_info_fb}\);', script_code)
                        fb_createInfoName = fb_definition.group(2)
                        #print(fb_create)
                        fb_createInfo_match = re.search(f'{fb_createInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                        fb_createInfo = fb_createInfo_match.group(0)
                        
                        attachementInfoMatch = re.search(r'pAttachments\s*=\s*\[\d+\]\((.*?)\)', fb_createInfo)
                        attachmentList = attachementInfoMatch.group(1).split(',')
                        
                        try:
                            ds_imageView = attachmentList[int(dsAttachmentId)]
                            ds_imageView = ds_imageView.replace(' ','')
                                #found imageView related image name
                            #print(ds_imageView)
                            ds_imageView_definition = re.search(f'vkCreateImageView+\((.*?), (.*?), (.*?), {ds_imageView}\);', script_code)
                            imageCreateInfoName = ds_imageView_definition.group(2)
                            
                            imageViewCreateMatch = re.search(f'{imageCreateInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                            imageViewCreateInfo = imageViewCreateMatch.group(0)
                            
                            imageNameMatch = re.search(r'image\s*=\s*([^,]+)', imageViewCreateInfo)
                            #print(imageNameMatch.group(1))
                            imageNameMatch = imageNameMatch.group(1)
                            info.set_dsImageName(imageNameMatch)
                        except:
                            print("get vk image failed")
                            sys.exit(1) 
                    else:
                        info.set_dsImageName("NULL")
                        #print("null ds attachment")
                    
                    if(len(colorAttachmentId)):
                        #print(colorAttachmentId)
                        #通过color attachment id 到对应framebuffer去中对应的imgeView，最终确定imagename
                        for colorId in colorAttachmentId:
                            #通过ds id 到对应的framebuffer去找到对应的ImageView，最终确定imagename
                            escaped_info_fb = re.escape(info.fb)
                            fb_definition = re.search(f'vkCreateFramebuffer+\((.*?), (.*?), (.*?), {escaped_info_fb}\);', script_code)
                            fb_createInfoName = fb_definition.group(2)
                            #print(fb_create)
                            fb_createInfo_match = re.search(f'{fb_createInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                            fb_createInfo = fb_createInfo_match.group(0)
                            
                            attachementInfoMatch = re.search(r'pAttachments\s*=\s*\[\d+\]\((.*?)\)', fb_createInfo)
                            attachmentList = attachementInfoMatch.group(1).split(',')
                            
                            try:
                                color_imageView = attachmentList[int(colorId)]
                                color_imageView = color_imageView.replace(' ','')
                                    #found imageView related image name
                                #print(ds_imageView)
                                color_imageView_definition = re.search(f'vkCreateImageView+\((.*?), (.*?), (.*?), {color_imageView}\);', script_code)
                                colorImageCreateInfoName = color_imageView_definition.group(2)
                                
                                colorImageViewCreateMatch = re.search(f'{colorImageCreateInfoName}+\[(\d+)\]\s*=\s*\((.*?)\);', script_code, re.DOTALL)
                                colorImageViewCreateInfo = colorImageViewCreateMatch.group(0)
                                
                                colorImageNameMatch = re.search(r'image\s*=\s*([^,]+)', colorImageViewCreateInfo)
                                #print(imageNameMatch.group(1))
                                colorImageNameMatch = colorImageNameMatch.group(1)
                                info.set_colorImageName(colorImageNameMatch)
                            except:
                                print("get vk image failed")
                                sys.exit(1) 
                        else:
                            pass
                            #info.set_dsImageName("NULL")
                            #print("null ds attachment")     
                        
                    renderpassInfoArray.append(info)
                    info = renderpassInfo()
        
        return renderpassInfoArray
        
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")


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

def get_line_num(obj):
    if isinstance(obj, renderpassInfo):
        return obj.beginLine
    elif isinstance(obj, submitInfo):
        return obj.lineNum
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
    else:
        file_path = sys.argv[1]
        renderpassInfoArray = analyze_renderpasses(file_path)
        submitInfoArray = analyze_submitlayout(file_path)
        
    all_objects = renderpassInfoArray + submitInfoArray
    sorted_objects = sorted(all_objects, key=get_line_num)
    
    for obj in sorted_objects:
        if isinstance(obj, renderpassInfo):
            print(f"Renderpass({obj.beginLine} - {obj.endLine}) cb {obj.cb}  drawNum {obj.drawNum} ColorImage {obj.colorImageNameList} DsImage {obj.dsImageName}")
        elif isinstance(obj, submitInfo):
            print(f"submitLine {obj.lineNum} cb {obj.cb}")