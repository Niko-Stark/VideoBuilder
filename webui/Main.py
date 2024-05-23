import sys
import os
import time
import pandas as pd
import json

# Add the root directory of the project to the system path to allow importing modules from the project
root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)
    print("******** sys.path ********")
    print(sys.path)
    print("")

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx

import os
from uuid import uuid4
import platform
import time

st.set_page_config(page_title="AutoVideoGeneration",
                   page_icon="🎞️",
                   layout="wide",
                   initial_sidebar_state="auto",
                   menu_items={
                    'Get help': None,
                    'Report a bug': None,
                    'About': None
                   })


from app.services import llm,storyboard,video,voice,task
from app.utils import utils
from app.models.schema import VideoParams,VideoGenerationMode
from app.services.state import TaskProgress,StepProgress

hide_streamlit_style = """
<style>#root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.title(f"AutoVideoGeneration v0.1.1")
def task_init():
    st.session_state['task_id'] = str(uuid4())
    print(st.session_state['task_id'])
    st.session_state['script_data'] = {}
    st.session_state["video_file"] = ''
    st.session_state["error"]=''
    st.session_state['status'] = {
        "storyboard":0,
        "video":0,
        "script":False,
        "add_storyboard":False
    }
    
def session_state_init():
    st.session_state['script_data'] = {}
    st.session_state["video_file"] = ''
    st.session_state["error"]=''
    st.session_state['status'] = {
        "storyboard":0,
        "video":0,
        "script":False,
        "add_storyboard":False
    }
if 'video_subject' not in st.session_state:
    st.session_state['video_subject'] = ''
    st.session_state['task_id'] = ''
    session_state_init()
if 'ui_language' not in st.session_state:
    st.session_state['ui_language'] = "zh"

def scroll_to_bottom():
    js = f"""
    <script>
        console.log("scroll_to_bottom");
        function scroll(dummy_var_to_force_repeat_execution){{
            var sections = parent.document.querySelectorAll('section.main');
            console.log(sections);
            for(let index = 0; index<sections.length; index++) {{
                sections[index].scrollTop = sections[index].scrollHeight;
            }}
        }}
        scroll(1);
    </script>
    """
    st.components.v1.html(js, height=0, width=0)


# def init_log():
#     _lvl = "DEBUG"

#     def format_record(record):
#         # 获取日志记录中的文件全路径
#         file_path = record["file"].path
#         # 将绝对路径转换为相对于项目根目录的路径
#         relative_path = os.path.relpath(file_path, root_dir)
#         # 更新记录中的文件路径
#         record["file"].path = f"./{relative_path}"
#         # 返回修改后的格式字符串
#         # 您可以根据需要调整这里的格式
#         record['message'] = record['message'].replace(root_dir, ".")

#         _format = '<green>{time:%Y-%m-%d %H:%M:%S}</> | ' + \
#                   '<level>{level}</> | ' + \
#                   '"{file.path}:{line}":<blue> {function}</> ' + \
#                   '- <level>{message}</>' + "\n"
#         return _format

# init_log()

locales = utils.load_locales(utils.i18n_dir())


def tr(key):
    loc = locales.get(st.session_state['ui_language'], {})
    return loc.get("Translation", {}).get(key, key)

params = VideoParams()
with st.container(border=True):
    st.subheader(tr("Video Script Settings"))
    with st.container(border=False):
        script_setting_panels = st.columns(2)
        script_setting_panel0 = script_setting_panels[0]
        script_setting_panel1 = script_setting_panels[1]
        with script_setting_panel0:
            params.video_subject = st.text_input(tr("Video Subject"),value="")
            if st.session_state['video_subject']!=params.video_subject:
                st.session_state['video_subject'] = params.video_subject
                task_init()
        with script_setting_panel1:
            video_languages = [
                (tr("Auto Detect"), ""),
            ]
            for code in ["zh-CN", "en-US"]:
                video_languages.append((code, code))

            selected_index = st.selectbox(tr("Script Language"),
                                      index=0,
                                      options=range(len(video_languages)),  # 使用索引作为内部选项值
                                      format_func=lambda x: video_languages[x][0]  # 显示给用户的是标签
                                      )
            params.video_language = video_languages[selected_index][1]



                
with st.container(border=True):
    st.subheader(tr("Video Settings"))
    video_setting_panels = st.columns([0.5,0.25,0.25])
    with video_setting_panels[0]:
        video_generation_modes = [
            (tr("text2video"), "text2video"),
            (tr("image2video"), "image2video"),
        ]
        selected_index = st.selectbox(tr("Video Concat Mode"),
                                      index=1,
                                      options=range(len(video_generation_modes)),  # 使用索引作为内部选项值
                                      format_func=lambda x: video_generation_modes[x][0]  # 显示给用户的是标签
                                      )
        params.video_generation_modes = VideoGenerationMode(video_generation_modes[selected_index][1])
    with video_setting_panels[1]:
        video_style = []
        for style in video.get_style():
            video_style.append((style,style))
        selected_video_style = st.selectbox("视频风格",
                                      index=7,
                                      options=range(len(video_style)),  # 使用索引作为内部选项值
                                      format_func=lambda x: video_style[x][0]  # 显示给用户的是标签
                                      )
        params.video_style = video_style[selected_video_style][1]
    with video_setting_panels[2]:
        storyboard_num = st.number_input("分镜数量",min_value=1,max_value=20,value = 5,step =1,format = '%d')
        params.storyboard_num = f"{storyboard_num}"
    if st.button(tr("Generate Video Script and Keywords"), key="auto_generate_script"):
        if st.session_state['video_subject'] == "":
            st.error("请输入视频主题",icon="🚨")
            st.stop()
        session_state_init()
        with st.spinner(tr("Generating Video Script and Keywords")):
            for i in range(3):
                print(params.storyboard_num)
                script_text = llm.generate_script(params.video_subject,storyboard_number=params.storyboard_num)
                if script_text !="":
                    break
            if script_text =="":
                st.error("视频脚本生成异常，请重试。。。",icon="🚨")
                st.stop()
            st.session_state['script_data'] = json.loads(script_text)
            st.session_state['status']["script"] = True

    if st.session_state['status']["script"]:
        script_col = st.columns([0.05,0.15,0.71,0.03,0.03,0.03])
        with script_col[0]:
            st.markdown("###### 分镜序号")
        with script_col[1]:
            st.markdown("###### 字幕内容")
        with script_col[2]:
            st.markdown("###### 画面描述")
        for index,(key,value)in enumerate(st.session_state['script_data'].items()):
            script_col = st.columns([0.05,0.15,0.71,0.03,0.03,0.03])
            with script_col[0]:
                st.text_input("分镜序号", value=key,disabled=True,label_visibility = "collapsed")
            with script_col[1]:
                new_subtitle = st.text_input("字幕内容", value=value["字幕内容"],label_visibility = "collapsed")
                if new_subtitle != value["字幕内容"]:
                    value["字幕内容"] = new_subtitle
            with script_col[2]:
                new_description = st.text_input("画面描述", value=value["画面描述"],label_visibility = "collapsed")
                if new_description != value["画面描述"]:
                    value["画面描述"] = new_description
            with script_col[3]:
                if st.button("⬆️",key = f"move_up_{index}"):
                    st.session_state['script_data'] = utils.dic_move_up(st.session_state['script_data'],index)
                    st.rerun()
            with script_col[4]:
                if st.button("⬇️",key = f"move_down_{index}"):
                    st.session_state['script_data'] = utils.dic_move_down(st.session_state['script_data'],index)
                    st.rerun()
            with script_col[5]:
                if st.button("❌",key = f"delete_{index}"):
                    st.session_state['script_data'] = utils.dic_remove_item(st.session_state['script_data'],index)
                    st.rerun()
    if st.button("添加分镜"):
        st.session_state['status']["add_storyboard"] = True
    if st.session_state['status']["add_storyboard"]:
        add_script_col = st.columns([0.15,0.20,0.65])
        with add_script_col[0]:
            save_index = len(st.session_state['script_data'])+1
            new_scene = st.number_input("分镜序号",min_value=1,max_value=save_index,value = save_index,step =1,format = '%d')
        with add_script_col[1]:
            new_subtitle = st.text_input("字幕内容")
        with add_script_col[2]:
            new_description = st.text_input("画面描述")
        add_script_button_col = st.columns([0.05,0.05,0.9])
        with add_script_button_col[0]:
            if st.button('✔️ 确认'):
                st.session_state['script_data'] = utils.dic_add_item(st.session_state['script_data'],f"分镜{save_index}",{"字幕内容": new_subtitle, "画面描述": new_description},new_scene-1)
                if st.session_state['video_subject'] == "":
                    task_init()
                    st.session_state['status']["script"] = True
                st.session_state['status']["add_storyboard"] = False
                st.rerun()
        with add_script_button_col[1]:
            if st.button('❌ 取消'):
                st.session_state['status']["add_storyboard"] = False
                st.rerun()

    # st.json(json.dumps(st.session_state['script_data']))
    storyboard_generate = st.button(tr("Generate storyboard"), key="auto_generate_storyboard")
    if storyboard_generate:
        if st.session_state['status']["script"]:
            st.session_state['status']["video"] = 0
            st.session_state['status']["storyboard"] = 1
        else:
            st.warning('未生成视频脚本', icon="⚠️")


    if st.session_state['status']["storyboard"]!=0:

        tasks = len(st.session_state['script_data'])
    
        if st.session_state['status']["storyboard"]==1:
            word_storyboard=st.empty()
            progress = TaskProgress()
            sub_progresses = []
            for i in range(tasks):
                sub_progresses.append(TaskProgress(weight = 1))
            progress.set_sub_progress(sub_progresses)
            bar_storyboard=st.progress(progress.progress)
            columns = st.columns(5)
            for index,(key,value)in enumerate(st.session_state['script_data'].items()):
                value["video"] = ""
                with columns[index % 5]: 
                    with st.spinner("生成分镜中..."):
                        prompt_progresses = StepProgress(steps=2,weight=1)
                        creator_progresses = StepProgress(weight=1)
                        sub_progresses[index].set_sub_progress([prompt_progresses,creator_progresses])
                        def creator():
                            prompts = llm.generate_prompt(value["画面描述"])
                            prompt_progresses.update_progress(2)
                            value["positve_prompt"] = prompts[0]
                            value["negative_prompt"] = prompts[1]
                            storyboard_dir = utils.make_sub_dir(utils.task_dir(f"{st.session_state['task_id']}"),"storyboard")
                            value["storyboard"] = storyboard.storyboard_creator(storyboard_dir,value,creator_progresses,video_style=params.video_style)
                        th = utils.run_in_background_st(creator)
                        while th.is_alive():
                            word_storyboard.text(f"{progress.progress*100:.2f}%")
                            bar_storyboard.progress(progress.progress)
                            time.sleep(2)
                    if value["storyboard"]!="":
                        st.image(value["storyboard"])
            st.session_state['status']["storyboard"]=2
            st.rerun()

        if st.session_state['status']["storyboard"]==2:
            columns = st.columns(5)
            for index,(key,value)in enumerate(st.session_state['script_data'].items()):
                with columns[index % 5]: 
                    st.image(value["storyboard"])
                    sub_columns = st.columns(2)
                    with sub_columns[0]:
                        retry = st.button("retry", key=f"retry_{index}_storyboard")
                    if retry:
                        with sub_columns[1]:
                            with st.spinner("生成分镜图中..."):
                                value["storyboard"] = ""
                                value["video"] = ""
                                # prompts = llm.generate_prompt(value["画面描述"])
                                # print(value["画面描述"])
                                # value["positve_prompt"] = prompts[0]
                                # value["negative_prompt"] = prompts[1]
                                storyboard_dir = utils.make_sub_dir(utils.task_dir(f"{st.session_state['task_id']}"),"storyboard")
                                value["storyboard"] = storyboard.storyboard_creator(storyboard_dir,value,StepProgress(weight=1),video_style=params.video_style)
                                st.rerun()
        
    video_generate = st.button("生成分镜视频", key="generate_videos") 
    if video_generate:
        if st.session_state['status']["script"]:
            if st.session_state['status']["storyboard"]!=2:
                st.session_state['status']["storyboard"]==1
            st.session_state['status']["video"] = 1
            st.rerun()
        else:
            st.warning('未生成视频脚本', icon="⚠️")
        
    if st.session_state['status']["video"] != 0:
        tasks = len(st.session_state['script_data'])
        if st.session_state['status']["video"] == 1:
            word_video=st.empty()
            progress = TaskProgress()
            sub_progresses = []
            for i in range(tasks):
                sub_progresses.append(TaskProgress(weight = 1))
            progress.set_sub_progress(sub_progresses)
            bar_video=st.progress(progress.progress)
            columns = st.columns(5)
            for index,(key,value)in enumerate(st.session_state['script_data'].items()):
                with columns[index % 5]: 
                    with st.spinner("生成分镜视频中..."):
                        prompt_progresses = StepProgress(steps=2,weight=0.1)
                        creator_progresses = StepProgress(weight=1)
                        sub_progresses[index].set_sub_progress([prompt_progresses,creator_progresses])
                        def creator():
                            # prompts = llm.generate_prompt(value["画面描述"])
                            prompt_progresses.update_progress(2)
                            # value["positve_prompt"] = prompts[0]
                            # value["negative_prompt"] = prompts[1]
                            video_dir = utils.make_sub_dir(utils.task_dir(f"{st.session_state['task_id']}"),"video")
                            value["video"] = video.video_creator(video_dir,value["storyboard"],creator_progresses)
                        th = utils.run_in_background_st(creator)
                        while th.is_alive():
                            word_video.text(f"{progress.progress*100:.2f}%")
                            bar_video.progress(progress.progress)
                            time.sleep(2)
                    st.video(value["video"])
            st.session_state['status']["video"]=2
            st.rerun()
        if st.session_state['status']["video"] == 2:
            columns = st.columns(5)
            for index,(key,value)in enumerate(st.session_state['script_data'].items()):
                with columns[index % 5]: 
                    if value["video"] != "":
                        st.video(value["video"])
                    sub_columns = st.columns(2)
                    with sub_columns[0]:
                        retry = st.button("retry", key=f"retry_{index}_video")
                    if retry:
                        with sub_columns[1]:
                            with st.spinner("生成分镜视频中..."):
                                value["subvideo"] = ""
                                # prompts = llm.generate_prompt(value["画面描述"])
                                # value["positve_prompt"] = prompts[0]
                                # value["negative_prompt"] = prompts[1]
                                video_dir = utils.make_sub_dir(utils.task_dir(f"{st.session_state['task_id']}"),"video")
                                value["video"] = video.video_creator(video_dir,value["storyboard"],StepProgress(weight=1))
                                st.rerun()

with st.container(border=True):
    st.subheader(tr("Audio Settings"))
    audio_setting_panels = st.columns(4)
    with audio_setting_panels[0]:
        voices = voice.get_all_voices()
    
        selected_voice_name = st.selectbox(tr("Speech Synthesis"),
                                           options=range(len(voices)),  # 使用索引作为内部选项值
                                           format_func=lambda x: voices[x][0]  # 显示给用户的是标签
                                           )

        params.voice_name = voices[selected_voice_name][1]
        
    with audio_setting_panels[1]:
        params.voice_volume = st.selectbox(tr("Speech Volume"),
                                           options=[0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0], index=3)
        
    with audio_setting_panels[2]:
        bgm_options = [
            (tr("No Background Music"), ""),
            (tr("Random Background Music"), "random"),
            # (tr("Custom Background Music"), "custom"),
        ]
        selected_index = st.selectbox(tr("Background Music"),
                                      index=0,
                                      options=range(len(bgm_options)),  # 使用索引作为内部选项值
                                      format_func=lambda x: bgm_options[x][0]  # 显示给用户的是标签
                                      )
        params.bgm_options = bgm_options[selected_index][1]


        if params.bgm_options == "custom":
            custom_bgm_file = st.text_input(tr("Custom Background Music File"))
            if custom_bgm_file and os.path.exists(custom_bgm_file):
                params.bgm_file = custom_bgm_file
    
    with audio_setting_panels[3]:
        params.bgm_volume = st.selectbox(tr("Background Music Volume"),
                                         options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], index=2)

with st.container(border=True):
    st.subheader(tr("Subtitle Settings"))
    params.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=True)
    if(params.subtitle_enabled):
        subtitle_setting_panels = st.columns(4)
        with subtitle_setting_panels[0]:
            font_names = utils.get_all_fonts()
            saved_font_name_index = 0
            params.font_name = st.selectbox(tr("Font"), font_names, index=0)
        
        with subtitle_setting_panels[1]:
            subtitle_positions = [
                (tr("Top"), "top"),
                (tr("Center"), "center"),
                (tr("Bottom"), "bottom"),
            ]
            selected_index = st.selectbox(tr("Position"),
                                        index=2,
                                        options=range(len(subtitle_positions)),  # 使用索引作为内部选项值
                                        format_func=lambda x: subtitle_positions[x][0]  # 显示给用户的是标签
                                        )
            params.subtitle_position = subtitle_positions[selected_index][1]
        
        with subtitle_setting_panels[2]:
            font_cols = st.columns([0.2, 0.7,0.1])
            with font_cols[0]:
                saved_text_fore_color ="#FFFFFF"
                params.text_fore_color = st.color_picker(tr("Font Color"), saved_text_fore_color)

            with font_cols[1]:
                saved_font_size =40
                params.font_size = st.slider(tr("Font Size"), 10, 150, saved_font_size)
        
        with subtitle_setting_panels[3]:
            stroke_cols = st.columns([0.2, 0.7,0.1])
            with stroke_cols[0]:
                params.stroke_color = st.color_picker(tr("Stroke Color"), "#000000")
            with stroke_cols[1]:
                params.stroke_width = st.slider(tr("Stroke Width"), 0.0, 10.0, 2.0)

start_button = st.button(tr("Generate Video"), use_container_width=True, type="primary")
if start_button:
    st.session_state["video_file"]=""
    if not params.video_subject or st.session_state['script_data'] == {}:
        st.error(tr("Video Script and Subject Cannot Both Be Empty"))
        scroll_to_bottom()
        st.stop()
    
    scroll_to_bottom()

    video_bar_word=st.empty()
    video_bar=st.progress(0)
    task_progress = TaskProgress()
    params.video_script = st.session_state['script_data']

    def start_task():
        try:
            cur_task = task.task(st.session_state["task_id"],task_progress,params)
            st.session_state["video_file"]=cur_task.start()
            print("start task end -------------------------")
        except Exception as e:
            st.session_state["video_file"] = ""
            st.session_state["error"] = str(e)
    task_thread = utils.run_in_background_st(start_task)
    while task_thread.is_alive():
        video_bar_word.text(f"{task_progress.progress*100:.2f}%")
        video_bar.progress(task_progress.progress)
    
    task_thread.join()
    if st.session_state["video_file"] == "":
        st.error(st.session_state["error"])
        scroll_to_bottom()
        st.stop()
    else:
        st.success(tr("Video Generation Completed"))
        st.video(st.session_state["video_file"])

    
  
