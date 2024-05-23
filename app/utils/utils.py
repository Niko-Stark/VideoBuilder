from datetime import datetime
import locale
import os
import threading
from typing import Any
from loguru import logger
import json
from uuid import uuid4
import urllib3
from streamlit.runtime.scriptrunner import add_script_run_ctx

urllib3.disable_warnings()


def get_response(status: int, data: Any = None, message: str = ""):
    obj = {
        'status': status,
    }
    if data:
        obj['data'] = data
    if message:
        obj['message'] = message
    return obj


def get_uuid(remove_hyphen: bool = False):
    u = str(uuid4())
    if remove_hyphen:
        u = u.replace("-", "")
    return u


def root_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

def make_sub_dir(dir,sub_dir):
    d = os.path.join(dir,sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def storage_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), "storage")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def resource_dir(sub_dir: str = ""):
    d = os.path.join(root_dir(), "resource")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    return d


def task_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "tasks")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def temp_dir(sub_dir: str = ""):
    d = os.path.join(storage_dir(), "temp")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def font_dir(sub_dir: str = ""):
    d = resource_dir(f"fonts")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def i18n_dir(sub_dir: str = ""):
    d = resource_dir(f"i18n")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def song_dir(sub_dir: str = ""):
    d = resource_dir(f"songs")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def public_dir(sub_dir: str = ""):
    d = resource_dir(f"public")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def workflow_dir(sub_dir: str = ""):
    d = resource_dir(f"workflow")
    if sub_dir:
        d = os.path.join(d, sub_dir)
    if not os.path.exists(d):
        os.makedirs(d)
    return d

def random_filename(dir,suffix):
    if not os.path.exists(dir):
        os.makedirs(dir)
    filename = get_uuid()+suffix
    filepath = os.path.join(dir, filename)
    return filepath

def run_in_background(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}")

    thread = threading.Thread(target=run)
    thread.start()
    
    return thread

def run_in_background_st(func, *args, **kwargs):
    def run():
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(f"run_in_background error: {e}")

    thread = threading.Thread(target=run)
    add_script_run_ctx(thread)
    thread.start()
    
    return thread


def time_convert_seconds_to_hmsm(seconds) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    seconds = int(seconds % 60)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, seconds, milliseconds)


def text_to_srt(idx: int, msg: str, start_time: float, end_time: float) -> str:
    start_time = time_convert_seconds_to_hmsm(start_time)
    end_time = time_convert_seconds_to_hmsm(end_time)
    srt = """%d
%s --> %s
%s
        """ % (
        idx,
        start_time,
        end_time,
        msg,
    )
    return srt

def md5(text):
    import hashlib
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def get_system_locale():
    try:
        loc = locale.getdefaultlocale()
        # zh_CN, zh_TW return zh
        # en_US, en_GB return en
        language_code = loc[0].split("_")[0]
        return language_code
    except Exception as e:
        return "en"


def load_locales(i18n_dir):
    _locales = {}
    for root, dirs, files in os.walk(i18n_dir):
        for file in files:
            if file.endswith(".json"):
                lang = file.split(".")[0]
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    _locales[lang] = json.loads(f.read())
    return _locales

def _format_duration_to_offset(duration) -> int:    
    if isinstance(duration, str):
        time_obj = datetime.strptime(duration, "%H:%M:%S.%f")
        milliseconds = (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (
                time_obj.microsecond // 1000)
        return milliseconds * 10000

    if isinstance(duration, int):
        return duration

    return 0

def get_all_fonts():
    fonts = []
    for root, dirs, files in os.walk(font_dir()):
        for file in files:
            if file.endswith(".ttf") or file.endswith(".ttc"):
                fonts.append(file)
    fonts.sort()
    return fonts


def get_all_songs():
    songs = []
    for root, dirs, files in os.walk(song_dir()):
        for file in files:
            if file.endswith(".mp3"):
                songs.append(file)
    return songs

def dic_add_item(data,newkey,newvalue,insert_index):
    cur_data = {}
    term_value = None
    if insert_index >= len(data):
        data[newkey]=newvalue
        return data
    for index,(key,value) in enumerate(data.items()):
        if index == insert_index:
            cur_data[key]=newvalue
            term_value = value
        if index<insert_index:
            cur_data[key]=value
        if index>insert_index:
            cur_data[key]=term_value
            term_value = value
    cur_data[newkey]=term_value
    return cur_data
def dic_remove_item (data,rm_index):
    cur_data = {}
    cur_key = None
    for index,(key,value) in enumerate(data.items()):
        if index == rm_index:
            cur_key = key
            continue
        if index > rm_index:
            cur_data[cur_key]=value
            cur_key = key
        else:
            cur_data[key]=value
    return cur_data

def dic_move_down(data,cur_index):
    if cur_index==len(data)-1:
        return data
    cur_data = {}
    cur_key = None
    cur_value = None
    for index,(key,value) in enumerate(data.items()):
        if index == cur_index:
            cur_key = key
            cur_value = value
            continue
        if index == cur_index+1:
            cur_data[cur_key]=value
            cur_data[key]=cur_value
        else:
            cur_data[key]=value
    return cur_data

def dic_move_up(data,cur_index):
    if cur_index==0:
        return data
    cur_data = {}
    cur_key = None
    cur_value = None
    for index,(key,value) in enumerate(data.items()):
        if index == cur_index-1:
            cur_key = key
            cur_value = value
            continue
        if index == cur_index:
            cur_data[cur_key]=value
            cur_data[key]=cur_value
        else:
            cur_data[key]=value

    return cur_data