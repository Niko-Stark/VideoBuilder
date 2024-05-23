import io
import json
from PIL import Image
import urllib
import uuid
import websocket
import os
from requests_toolbelt import MultipartEncoder

from app.services.state import StepProgress
from app.utils import utils

#todo 配置文件获取url
def open_websocket_connection():
    server_address='192.168.1.50:9956'
    client_id=str(uuid.uuid4())
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))

    return ws, server_address, client_id

def load_workflow(workflow_path):
    try:
        with open(workflow_path, 'r', encoding='utf-8') as file:
            workflow = json.load(file)
            return json.dumps(workflow)
    except FileNotFoundError:
        print(f"The file {workflow_path} was not found.")
        return None
    except json.JSONDecodeError:
        print(f"The file {workflow_path} contains invalid JSON.")
        return None
    
def get_history(prompt_id, server_address):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())
    
def get_image(filename, subfolder, folder_type, server_address):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()
    
def get_images(prompt_id, server_address,directory):
    output_images = []

    history = get_history(prompt_id, server_address)[prompt_id]
    # print(history)
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        output_data = {}
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'], server_address)
                image_file = Image.open(io.BytesIO(image_data))
                image_file.save(os.path.join(directory, image['filename']))
                output_data['file_name'] = image['filename']
                output_data['type'] = image['type']
                output_images.append(output_data)

    return output_images
def upload_image(input_path,server_address, image_type="input", overwrite=True):
    filename = os.path.basename(input_path)
    with open(input_path, 'rb') as file:
        multipart_data = MultipartEncoder(
            fields= {
                'image': (filename, file, 'image/png'),
                'type': image_type,
                'overwrite': str(overwrite).lower()
            }
    )

        data = multipart_data
        headers = { 'Content-Type': multipart_data.content_type }
        request = urllib.request.Request("http://{}/upload/image".format(server_address), data=data, headers=headers)
        with urllib.request.urlopen(request) as response:
            return response.read()
        
def get_video(filename, subfolder, folder_type, server_address):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()
    
def get_videos(prompt_id, server_address,directory):
    output_videos = []

    history = get_history(prompt_id, server_address)[prompt_id]
    # print(history)
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        output_data = {}
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                video_data = get_video(video['filename'], video['subfolder'], video['type'], server_address)
                output_file_path = os.path.join(directory,video['filename'])
                with open(output_file_path, "wb") as file:
                    file.write(video_data)
                output_data['file_name'] = video['filename']
                output_data['type'] = video['type']
                output_videos.append(output_data)

    return output_videos

def queue_prompt(prompt, client_id, server_address):
    p = {"prompt": prompt, "client_id": client_id}
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req).read())

def track_progress(prompt, ws, prompt_id,progress:StepProgress):
    node_ids = list(prompt.keys())
    finished_nodes = []
    finished_step = 0
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
        if message['type'] == 'progress':
            data = message['data']
            current_step = data['value']
            progress.update_progress(len(finished_nodes)+finished_step+current_step)
            if(current_step ==  data['max']):
                finished_step += data['max']
        if message['type'] == 'execution_cached':
            data = message['data']
            for itm in data['nodes']:
                if itm not in finished_nodes:
                    finished_nodes.append(itm)
                    print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                    progress.update_progress(len(finished_nodes)+finished_step)
        if message['type'] == 'executing':
            data = message['data']
            if data['node'] not in finished_nodes:
                finished_nodes.append(data['node'])
                print('Progess: ', len(finished_nodes), '/', len(node_ids), ' Tasks done')
                progress.update_progress(len(finished_nodes)+finished_step)
            if data['node'] is None and data['prompt_id'] == prompt_id:
                break #Execution is done
        else:
            continue
    return

def generate_image_by_prompt(prompt,progress:StepProgress,directory):
    try:
        ws, server_address, client_id = open_websocket_connection()
        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
        track_progress(prompt, ws, prompt_id,progress)
        images = get_images(prompt_id, server_address,directory)
        return images
    finally:
        ws.close()

def generate_video_by_image(inputpath,prompt,progress,directory):
    try:
        ws, server_address, client_id = open_websocket_connection()
        upload_image(inputpath,server_address)
        prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
        track_progress(prompt, ws, prompt_id,progress)
        videos = get_videos(prompt_id, server_address,directory)
        return videos
    finally:
        ws.close()