from app.utils.comfyutils import load_workflow,generate_image_by_prompt
import os
import json
import random

def storyboard_creater(positve_prompt,root_path,negative_prompt=''):
    workflow_path = os.path.join(root_path,"resource", "workflow","sdxl_api.json")
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
        if value == 'KSamplerAdvanced':
            prompt.get(key)['inputs']['noise_seed'] = random.randint(10**14, 10**15 - 1)
    images = generate_image_by_prompt(prompt,root_path)
    path = os.path.join(root_path,"output","image",images[0]["file_name"])
    return(path)