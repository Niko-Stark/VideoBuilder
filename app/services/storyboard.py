import os
import json
import random

from app.utils import comfyutils,utils
from app.services.state import StepProgress

def storyboard_creator(directory,param,progress:StepProgress,video_style='sai-anime'):
    print(f"video_style: {video_style}")
    workflow_path = os.path.join(utils.workflow_dir(),"sdxl_turbo_api.json")
    workflow = comfyutils.load_workflow(workflow_path)
    if workflow==None:
        return None
    prompt = json.loads(workflow)
    id_class_type = {id: details['class_type'] for id, details in prompt.items()}
    progress.steps+=(len(id_class_type))
    for key, value in id_class_type.items():
        if value == 'SDXLPromptStyler':
            text_positive = param["positve_prompt"] if "positve_prompt" in param else ''
            prompt.get(key)['inputs']['text_positive'] = text_positive
            print(f"positve_prompt: {text_positive}")
            text_negative = param["negative_prompt"] if "negative_prompt" in param else ''
            prompt.get(key)['inputs']['text_negative'] = text_negative
            print(f"negative_prompt: {text_negative}")
            prompt.get(key)['inputs']['style'] = video_style
        if value == 'SamplerCustom':
            prompt.get(key)['inputs']['noise_seed'] = random.randint(10**14, 10**15 - 1)
        if value == 'SDTurboScheduler':
            sampler =  prompt.get(key)['inputs']
            progress.steps+=sampler['steps']

    images = comfyutils.generate_image_by_prompt(prompt,progress,directory)
    path = os.path.join(directory,images[0]["file_name"])
    return(path)