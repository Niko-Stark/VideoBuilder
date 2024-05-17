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


from app.services import llm,storyboard,video
from app.utils import utils
from app.models.schema import VideoParams,VideoConcatMode

hide_streamlit_style = """
<style>#root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.title(f"AutoVideoGeneration v0.1.1")

font_dir = os.path.join(root_dir, "resource", "fonts")
song_dir = os.path.join(root_dir, "resource", "songs")
i18n_dir = os.path.join(root_dir, "webui", "i18n")
workflow_dir = os.path.join(root_dir, "resource", "workflow")
config_file = os.path.join(root_dir, "webui", ".streamlit", "webui.toml")

if 'video_subject' not in st.session_state:
    st.session_state['video_subject'] = ''
if 'video_script' not in st.session_state:
    st.session_state['video_script'] = ''
if 'script_data' not in st.session_state:
    st.session_state['script_data'] = {}
if 'images' not in st.session_state:
    st.session_state['images'] = []
if 'videos' not in st.session_state:
    st.session_state['videos'] = []
if 'ui_language' not in st.session_state:
    st.session_state['ui_language'] = "zh"
if 'video_url' not in st.session_state:
    st.session_state['video_url'] = ''
if 'status' not in st.session_state:
    st.session_state['status'] = {
        "storyboard":0,
        "script":False
    }


def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs


def open_task_folder(task_id):
    try:
        sys = platform.system()
        path = os.path.join(root_dir, "storage", "tasks", task_id)
        if os.path.exists(path):
            if sys == 'Windows':
                os.system(f"start {path}")
            if sys == 'Darwin':
                os.system(f"open {path}")
    except Exception as e:
        return


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

locales = utils.load_locales(i18n_dir)


def tr(key):
    loc = locales.get(st.session_state['ui_language'], {})
    return loc.get("Translation", {}).get(key, key)

# def change_script():
#     state = st.session_state["script_editor"]
#     print(state)
#     for index,updates in state["edited_rows"].items():
#         for key, value in updates.items():
#             st.session_state["script_data"].loc[st.session_state["script_data"].index == index, key] = value
#     for index in state["deleted_rows"]:
#         st.session_state["script_data"].drop(index=index,inplace=True)
#     for item in state["added_rows"]:
#         st.session_state["script_data"].append(item)
#     print(st.session_state["script_data"])
#     return
params = VideoParams()
with st.container(border=True):
    st.write(tr("Video Script Settings"))
    with st.container(border=False):
        script_setting_panels = st.columns(2)
        script_setting_panel0 = script_setting_panels[0]
        script_setting_panel1 = script_setting_panels[1]
        with script_setting_panel0:
            params.video_subject = st.text_input(tr("Video Subject"),value=st.session_state['video_subject']).strip()
        with script_setting_panel1:
            video_languages = [
                (tr("Auto Detect"), ""),
            ]
            for code in ["zh-CN", "zh-TW", "de-DE", "en-US"]:
                video_languages.append((code, code))

            selected_index = st.selectbox(tr("Script Language"),
                                      index=0,
                                      options=range(len(video_languages)),  # 使用索引作为内部选项值
                                      format_func=lambda x: video_languages[x][0]  # 显示给用户的是标签
                                      )
            params.video_language = video_languages[selected_index][1]



                
with st.container(border=True):
    st.write(tr("Video Settings"))
    # video_setting_panels = st.columns(3)
    # video_setting_panel0 = video_setting_panels[0]
    # video_setting_panel1 = video_setting_panels[1]
    # video_setting_panel2 = video_setting_panels[2]
    # with video_setting_panel0:
    video_concat_modes = [
            (tr("Sequential"), "sequential"),
            (tr("Random"), "random"),
        ]
    selected_index = st.selectbox(tr("Video Concat Mode"),
                                      index=1,
                                      options=range(len(video_concat_modes)),  # 使用索引作为内部选项值
                                      format_func=lambda x: video_concat_modes[x][0]  # 显示给用户的是标签
                                      )
    params.video_concat_mode = VideoConcatMode(video_concat_modes[selected_index][1])
    if st.button(tr("Generate Video Script and Keywords"), key="auto_generate_script"):
        with st.spinner(tr("Generating Video Script and Keywords")):
            script_text = llm.generate_script(params.video_subject)
#             script_text ="""{
# "分镜1":{
# "字幕内容":"清晨，城市的苏醒",
# "画面描述":"画面缓缓拉开，淡蓝色的晨曦穿透薄雾，城市天际线渐渐清晰。空旷的街道上，一两盏路灯还亮着，远处的建筑群开始反射出柔和的日光。轻轨列车悄悄滑过静谧的城市，留下轻微的轰鸣。街边，一朵小花在微风中轻轻摇曳，预示着新的一天开始。"
# },
# "分镜2":{
# "字幕内容":"忙碌的脚步，生活的节奏",
# "画面描述":"镜头切换至繁忙的十字路口，人群穿着各式服装，步伐匆匆。上班族手持咖啡，学生背着书包，老人悠闲散步，各色人物交织成一幅生动的生活画卷。阳光已完全升起，洒在每个人的脸上，给画面增添了温暖的色调。"
# },
# "分镜3":{
# "字幕内容":"创意空间，思维的碰撞",
# "画面描述":"进入一个充满现代感的开放式办公区，镜头掠过一个个专注工作的年轻人，他们或在白板前激烈讨论，或独自对着电脑屏幕沉思。桌上散落的设计稿、笔记本和咖啡杯，展现了一个创意涌动的工作环境。背景音乐轻快，营造出积极向上的氛围。"
# },
# "分镜4":{
# "字幕内容":"城市绿洲，心灵的栖息",
# "画面描述":"画面转至城市中心的一片绿色公园，参天大树下，人们或坐或卧，享受午后的宁静。孩子们在喷泉旁嬉戏，水珠在阳光下闪烁，形成一道道彩虹。一位老人在喂鸽子，脸上洋溢着平和的笑容。这个镜头传递出在都市快节奏中寻找宁静与和谐的信息。"
# },
# "分镜5":{
# "字幕内容":"夜幕降临，城市的另一面",
# "画面描述":"夜色渐浓，霓虹灯逐一亮起，镜头缓慢拉高，展现出灯火辉煌的城市夜景。高楼大厦的灯光在夜空中勾勒出迷人的轮廓，车流在街道上形成流动的光带。人们在露天餐厅享受美食，笑声与谈话声交织在一起，展现出城市夜晚的活力与魅力。最后画面定格在一片璀璨的夜空，星星点点，寓意着希望与梦想永不熄灭。"
# }
# }"""
            st.session_state['script_data'] = json.loads(script_text)
            st.session_state['status']["script"] = True

    if st.session_state['status']["script"]:
        st.json(st.session_state['script_data'])
    #     mycolumn_config={
    #     "字幕内容":st.column_config.TextColumn(
    #         None,
    #         default="",
    #         width="small",
    #     ),
    #     "画面描述": st.column_config.TextColumn(
    #         None,
    #         default="",
    #         width=None,
    #     )
    # }
    #     st.data_editor(st.session_state['script_data'],key ="script_editor", column_config = mycolumn_config,use_container_width=True,hide_index=True,num_rows="dynamic",on_change=change_script)
    storyboard_generate = st.button(tr("Generate storyboard"), key="auto_generate_terms")
    if storyboard_generate:
        # st.session_state['images'] = [".//output//image//ComfyUI_temp_yjbsy_00003_.png",
        #                               ".//output//image//ComfyUI_temp_yjbsy_00004_.png",
        #                               ".//output//image//ComfyUI_temp_yjbsy_00005_.png",
        #                               ".//output//image//ComfyUI_temp_yjbsy_00006_.png",
        #                               ".//output//image//ComfyUI_temp_yjbsy_00007_.png",]
        st.session_state['images'] = []
        st.session_state['status']["storyboard"] = 1


    if st.session_state['status']["storyboard"]!=0:
        images=st.session_state['images']
        step = len(images)
        tasks = len(st.session_state['script_data'])
        
        if st.session_state['status']["storyboard"]==1:
            word0=st.empty()
            print(len(st.session_state['script_data']))
            word0.text(f"{len(st.session_state['images'])}/{5}")
            bar0=st.progress((1.0/tasks)*(len(st.session_state['images'])))
        columns = st.columns(5)
        for i, img_path in enumerate(st.session_state['images']):
            with columns[i % 5]: 
                st.image(img_path)
                if st.session_state['status']["storyboard"] == 2:
                    if st.button("retry", key=f"return_{i}_storyboard"):
                        prompt = llm.generate_prompt(list(st.session_state['script_data'].values())[i]["画面描述"])
                        images[i]=storyboard.storyboard_creater(prompt,root_dir)
                        st.session_state['images'] = images
                        print("retry")
        if step!=tasks:
            with columns[step % 5]: 
                with st.spinner("生成分镜图"):
                    prompt = llm.generate_prompt(list(st.session_state['script_data'].values())[step]["画面描述"])
                    print(prompt)
                    images.append(storyboard.storyboard_creater(prompt,root_dir))
                    st.session_state['images'] = images
                    st.rerun()
        else:
            if st.session_state['status']["storyboard"]==1:
                st.session_state['status']["storyboard"] = 2
                st.rerun()
            
        
        
        
                
with st.expander(tr("Audio Settings"), expanded=False):
    audio_setting_panels = st.columns(4)
    audio_setting_panel0 = audio_setting_panels[0]
    audio_setting_panel1 = audio_setting_panels[1]
    audio_setting_panel2 = audio_setting_panels[2]
    audio_setting_panel3 = audio_setting_panels[3]
    # with audio_setting_panel0:
    #     voices = voice.get_all_azure_voices(filter_locals=["zh-CN", "zh-HK", "zh-TW", "de-DE", "en-US", "fr-FR"])
    #     friendly_names = {
    #         v: v.
    #         replace("Female", tr("Female")).
    #         replace("Male", tr("Male")).
    #         replace("Neural", "") for
    #         v in voices}
    #     saved_voice_name = config.ui.get("voice_name", "")
    #     saved_voice_name_index = 0
    #     if saved_voice_name in friendly_names:
    #         saved_voice_name_index = list(friendly_names.keys()).index(saved_voice_name)
    #     else:
    #         for i, v in enumerate(voices):
    #             if v.lower().startswith(st.session_state['ui_language'].lower()):
    #                 saved_voice_name_index = i
    #                 break
    
    #     selected_friendly_name = st.selectbox(tr("Speech Synthesis"),
    #                                           options=list(friendly_names.values()),
    #                                           index=saved_voice_name_index)

    #     voice_name = list(friendly_names.keys())[list(friendly_names.values()).index(selected_friendly_name)]
    #     params.voice_name = voice_name
        
    # with audio_setting_panel1:
    #     config.ui['voice_name'] = voice_name
    #     if voice.is_azure_v2_voice(voice_name):
    #         saved_azure_speech_region = config.azure.get(f"speech_region", "")
    #         saved_azure_speech_key = config.azure.get(f"speech_key", "")
    #         azure_speech_region = st.text_input(tr("Speech Region"), value=saved_azure_speech_region)
    #         azure_speech_key = st.text_input(tr("Speech Key"), value=saved_azure_speech_key, type="password")
    #         config.azure["speech_region"] = azure_speech_region
    #         config.azure["speech_key"] = azure_speech_key

        # params.voice_volume = st.selectbox(tr("Speech Volume"),
        #                                    options=[0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0, 4.0, 5.0], index=2)
        
    with audio_setting_panel2:
        bgm_options = [
            (tr("No Background Music"), ""),
            (tr("Random Background Music"), "random"),
            (tr("Custom Background Music"), "custom"),
        ]
        selected_index = st.selectbox(tr("Background Music"),
                                      index=1,
                                      options=range(len(bgm_options)),  # 使用索引作为内部选项值
                                      format_func=lambda x: bgm_options[x][0]  # 显示给用户的是标签
                                      )
        # 获取选择的背景音乐类型
        bgm_type = bgm_options[selected_index][1]

        # 根据选择显示或隐藏组件
        if bgm_type == "custom":
            custom_bgm_file = st.text_input(tr("Custom Background Music File"))
            if custom_bgm_file and os.path.exists(custom_bgm_file):
                params.bgm_file = custom_bgm_file
                # st.write(f":red[已选择自定义背景音乐]：**{custom_bgm_file}**")
    
    with audio_setting_panel3:
        params.bgm_volume = st.selectbox(tr("Background Music Volume"),
                                         options=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], index=2)

with st.expander(tr("Subtitle Settings"), expanded=False):
    params.subtitle_enabled = st.checkbox(tr("Enable Subtitles"), value=True)
    subtitle_setting_panels = st.columns(4)
    subtitle_setting_panel0 = subtitle_setting_panels[0]
    subtitle_setting_panel1 = subtitle_setting_panels[1]
    subtitle_setting_panel2 = subtitle_setting_panels[2]
    subtitle_setting_panel3 = subtitle_setting_panels[3]
    with subtitle_setting_panel0:
        font_names = get_all_fonts()
        # saved_font_name = config.ui.get("font_name", "")
        saved_font_name_index = 0
        # if saved_font_name in font_names:
        #     saved_font_name_index = font_names.index(saved_font_name)
        # params.font_name = st.selectbox(tr("Font"), font_names, index=saved_font_name_index)
        # config.ui['font_name'] = params.font_name
    
    with subtitle_setting_panel1:
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
    
    with subtitle_setting_panel2:
        font_cols = st.columns([0.2, 0.7,0.1])
        with font_cols[0]:
            saved_text_fore_color ="#FFFFFF"
            params.text_fore_color = st.color_picker(tr("Font Color"), saved_text_fore_color)

        with font_cols[1]:
            saved_font_size = 60
            params.font_size = st.slider(tr("Font Size"), 30, 100, saved_font_size)
    
    with subtitle_setting_panel3:
        stroke_cols = st.columns([0.2, 0.7,0.1])
        with stroke_cols[0]:
            params.stroke_color = st.color_picker(tr("Stroke Color"), "#000000")
        with stroke_cols[1]:
            params.stroke_width = st.slider(tr("Stroke Width"), 0.0, 10.0, 1.5)







start_button = st.button(tr("Generate Video"), use_container_width=True, type="primary")
if start_button:
    # video.video_creater(".//temp//ComfyUI_temp_bnpmv_00006_.png","./")
    # config.save_config()
    task_id = str(uuid4())
    # if not params.video_subject:
    #     st.error(tr("Video Script and Subject Cannot Both Be Empty"))
    #     scroll_to_bottom()
    #     st.stop()
    
    # log_container = st.empty()
    # log_records = []


    # def log_received(msg):
    #     with log_container:
    #         log_records.append(msg)
    #         st.code("\n".join(log_records))


    # logger.add(log_received)

    # st.toast(tr("Generating Video"))
    # logger.info(tr("Start Generating Video"))
    # logger.info(utils.to_json(params))
    # scroll_to_bottom()
    video_bar_word=st.empty()
    video_bar=st.progress(0)
    tasks = len(st.session_state['images'])+1
    for i,  in enumerate(st.session_state['images']):
        st.session_state['videos'] = []
        video_prompt = list(st.session_state['script_data'].values())[i]["画面描述"]
        print (video_prompt)
        video_path = video.video_creater(img_path,"",root_dir)
        st.session_state['videos'].append(video_path)
        video_bar.progress((1.0/tasks*(i+1)))
        video_bar_word.text(f"{100/tasks*(i+1)}%")
    # open_task_folder(task_id)
    # logger.info(tr("Video Generation Completed"))
    # scroll_to_bottom()
    from moviepy.editor import VideoFileClip, concatenate_videoclips



    # clips = [VideoFileClip(path) for path in st.session_state['videos']]
    video_clip_paths  = st.session_state['videos']
    clips = [VideoFileClip(path) for path in video_clip_paths]
    final_clip = concatenate_videoclips(clips)


    output_path = os.path.join(root_dir,"output","result",f"video_{task_id}.mp4")
    final_clip.write_videofile(output_path, codec="libx264")


    final_clip.close()
    for clip in clips:
        clip.close()
    video_bar.progress(1.0)
    video_bar_word.text("100.0%")
    st.session_state['video_url'] = output_path
    st.video(st.session_state['video_url'])
