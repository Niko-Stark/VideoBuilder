from app.services.task import merge_voice_2_video
from app.services.state import StepProgress
from app.utils import utils
import os
data = {}
data["text"] = "测试"
data["voice_volume"] = 0.5
data["subtitle_enabled"] = True
full_path = os.path.join(utils.font_dir(),"STHeitiLight.ttc")

data["font_name"] = full_path.replace("\\", "/")
data["subtitle_position"] = "bottom"
data["text_fore_color"] = "#FFFFFF"
data["font_size"] = 100
data["stroke_color"] = "#000000"
data["stroke_width"] = 6

print(data)
data = utils.dic_remove_item(data,2)
print(data)
# from app.services import storyboard
# from app.services import video
# test_dir = ".\\test"
# storyboard_dir = ".\\test\\ComfyUI_temp_snajd_00007_.png"
# video.video_creator(test_dir,storyboard_dir,StepProgress(weight=1))