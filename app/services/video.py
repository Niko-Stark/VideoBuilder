from app.utils.comfyutils import load_workflow,generate_video_by_image
import os
import json
import random
#todo 从配置读取workflow_path

def video_creater(image_path,positve_prompt,root_path,negative_prompt=''):
    
    workflow_path = os.path.join(root_path,"resource", "workflow","dynamicraft_api.json")
    workflow = load_workflow(workflow_path)
    if workflow==None:
        return None
    prompt = json.loads(workflow)
    id_class_type = {id: details['class_type'] for id, details in prompt.items()}
    for key, value in id_class_type.items():
        if value == 'SDXLPromptStyler':
            prompt.get(key)['inputs']['text_positive'] = positve_prompt
            if negative_prompt != '':
                prompt.get(key)['inputs']['text_negative'] = negative_prompt
        if value == 'KSampler':
            prompt.get(key)['inputs']['seed'] = random.randint(10**14, 10**15 - 1)
        if value == 'LoadImage':
            filename = image_path.split('/')[-1]
            prompt.get(key)['inputs']['image'] = filename
    
    videos =  generate_video_by_image( image_path, filename,prompt,'./')
    path = os.path.join(root_path,"output","video",videos[0]["file_name"])
    return(path)
    