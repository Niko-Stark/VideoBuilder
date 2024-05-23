import os
import json
import random
import streamlit as st

from app.utils import comfyutils,utils
from app.services.state import StepProgress

def video_creator(directory,imagefile,progress:StepProgress,video_style='sai-anime'):
    workflow_path = os.path.join(utils.workflow_dir(),"svd_LCM_I2V_api.json")
    workflow = comfyutils.load_workflow(workflow_path)
    if workflow==None:
        return None
    prompt = json.loads(workflow)
    id_class_type = {id: details['class_type'] for id, details in prompt.items()}
    progress.steps+=(len(id_class_type))
    for key, value in id_class_type.items():
        # if value == 'SDXLPromptStyler':
        #     text_positive = param["video_positve_prompt"] if "video_positve_prompt" in param else ''
        #     prompt.get(key)['inputs']['text_positive'] = text_positive
        #     print(f"video_positve_prompt: {text_positive}")
        #     text_negative = param["video_negative_prompt"] if "video_negative_prompt" in param else ''
        #     prompt.get(key)['inputs']['text_negative'] = text_negative
        #     print(f"video_negative_prompt: {text_negative}")
        #     prompt.get(key)['inputs']['style'] = video_style 
        if value == 'KSampler':
            prompt.get(key)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
            prompt.get(key)['inputs']['cfg'] = 2.0
            progress.steps+= prompt.get(key)['inputs']['steps']
        if value == 'LoadImage':
            filename = os.path.basename(imagefile)
            prompt.get(key)['inputs']['image'] = filename
        if value == 'SVD_img2vid_Conditioning':
            prompt.get(key)['inputs']['motion_bucket_id'] = random.randint(10, 190)
            prompt.get(key)['inputs']['augmentation_level'] = 0.05
    videos = comfyutils.generate_video_by_image(imagefile,prompt,progress,directory)
    path = os.path.join(directory,videos[0]["file_name"])
    return(path)

@st.cache_data
def get_style():
    styles = [
        "artstyle-steampunk",
        "artstyle-abstract",
        "futuristic-sci-fi",
        "game-mario",
        "photo-hdr",
        "photo-tilt-shift",
        "sai-analog film",
        "sai-anime",
        "sai-cinematic",
        "sai-comic book",
        "sai-digital art",
        "sai-fantasy art",
        "sai-line art",
        "sai-neonpunk",]
    return styles