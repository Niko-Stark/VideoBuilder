from app.services.task import merge_voice_2_video
from app.services.state import StepProgress
data = {}
data["text"] = "TEST"
data["voice_volume"] = 0.5
data["subtitle_enabled"] = True
data["font_name"] = "STHeitiMedium.ttc"
data["subtitle_position"] = "bottom"
data["text_fore_color"] = "#FFFFFF"
data["font_size"] = 60
data["stroke_color"] = "#000000"
data["stroke_width"] = 1.5
merge_voice_2_video("./storage//tasks/3e06d4f1-0b5b-40d2-a185-96f0d589cde0/video/AnimateLCMSVD_00065.mp4", "./storage/tasks/3e06d4f1-0b5b-40d2-a185-96f0d589cde0/voice/1e04d55b-4ff1-4e99-bf11-23445a3e1065.mp3","./",data,StepProgress())
# from app.utils import utils
# import os
# data = {}
# data["text"] = "测试"
# data["voice_volume"] = 0.5
# data["subtitle_enabled"] = True
# full_path = os.path.join(utils.font_dir(),"STHeitiLight.ttc")

# data["font_name"] = full_path.replace("\\", "/")
# data["subtitle_position"] = "bottom"
# data["text_fore_color"] = "#FFFFFF"
# data["font_size"] = 100
# data["stroke_color"] = "#000000"
# data["stroke_width"] = 6

# print(data)
# data = utils.dic_remove_item(data,2)
# print(data)
# from app.services import storyboard
# from app.services import video
# test_dir = ".\\test"
# storyboard_dir = ".\\test\\ComfyUI_temp_snajd_00007_.png"
# video.video_creator(test_dir,storyboard_dir,StepProgress(weight=1))