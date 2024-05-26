import os
import json
import random
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip,CompositeVideoClip,concatenate_videoclips,CompositeAudioClip
from app.models.schema import VideoParams
from app.services import llm, storyboard,voice, video
from app.services.state import TaskProgress,StepProgress
from app.utils import utils

def move_file(src, dst):
    filename = os.path.basename(src)
    
    if not os.path.isfile(dst):
        dst = os.path.join(dst, filename)

    try:
        shutil.move(src, dst)
        print(f"文件已成功移动从 {src} 到 {dst}")
        return dst  # 成功移动后返回目标路径
    except FileNotFoundError:
        print(f"错误: 源文件 {src} 未找到。")
        return None
    except Exception as e:
        print(f"移动文件时发生错误: {e}")
        return None

def merge_voice_2_video(video_path, audio_path,output_path,param,merge_state:StepProgress):

    merge_state.set_steps(4)
    video_clip = VideoFileClip(video_path)
    video_clip = video_clip.without_audio()
    audio_clip = AudioFileClip(audio_path)
   
    video_duration = video_clip.duration
    audio_duration = audio_clip.duration
    print(audio_duration)
    
    print(video_duration)
    if video_duration < audio_duration:
        adjusted_video = video_clip.speedx(factor=audio_duration / video_duration)
    else:
        adjusted_video = video_clip.subclip(0, audio_duration)
    audio_clip = audio_clip.volumex(param["voice_volume"])

    adjusted_video = adjusted_video.set_audio(audio_clip)
    merge_state.update_progress(2)
    if param["subtitle_enabled"]:
        font_name=os.path.join(utils.font_dir(),param["font_name"])
        font_name = font_name.replace("\\", "/")
        text_clip = TextClip(param["text"], fontsize=param["font_size"], font=font_name, color=param["text_fore_color"], stroke_color=param["stroke_color"], stroke_width=param["stroke_width"])
        video_width, video_height = adjusted_video.size
        if param["subtitle_position"] == "bottom":
            text_clip = text_clip.set_position(('center', video_height * 0.95 - text_clip.h))
        if param["subtitle_position"] == "center":
            text_clip = text_clip.set_position(('center','center'))
        if param["subtitle_position"] == "top":
            text_clip = text_clip.set_position(('center', video_height * 0.1))
        text_clip = text_clip.set_duration(audio_duration)
        final_clip= CompositeVideoClip([adjusted_video, text_clip])
    filename = os.path.basename(video_path)
    filepath = os.path.join(output_path,filename)
    final_clip.write_videofile(filepath, codec="libx264", audio_codec="aac")
    merge_state.update_progress(2)
    return filepath

class task:
    def __init__(self,task_id,state:TaskProgress,params: VideoParams) -> None:
        self._task_id = task_id
        self._state = state
        self.task_dir = utils.task_dir(f"{task_id}")
        self.storyboard_dir = utils.make_sub_dir(self.task_dir,"storyboard")
        self.video_dir = utils.make_sub_dir(self.task_dir,"video")
        self.subvideo_dir = utils.make_sub_dir(self.task_dir,"subvideo")
        self.voice_dir = utils.make_sub_dir(self.task_dir,"voice")
        self._params = params
        self.merge_video_state =StepProgress(1,1)
        
        self._state.set_sub_progress([self.merge_video_state])

    def start(self):
        
        video_script = self._params.video_script
        if video_script == {}:
            generate_script_state =StepProgress(1,1)
            self._state.append_sub_progress(generate_script_state)
            for i in range(3):
                script_text = llm.generate_script(self._params.video_subject,self._params.storyboard_num)
                if script_text !="":
                    break
            if script_text =="":
                raise Exception("Video Script Generation Error")
            generate_script_state.update_progress(1)
            video_script = json.loads(script_text)
            self._params.video_script = video_script
        
        self.mian_task(video_script)
        print("main task end")
        videos = []
        for key,value in video_script.items():
            videos.append(value["subvideo"])

        clips = [VideoFileClip(path) for path in videos]
        final_clip = concatenate_videoclips(clips)
        if self._params.bgm_options == "random":
            songs = utils.get_all_songs()
            song = random.choice(songs)
            bgm_clip = AudioFileClip(os.path.join(utils.song_dir(),song))
            video_duration = final_clip.duration
            audio_duration = bgm_clip.duration
            if audio_duration < video_duration:  
                bgm_clip = bgm_clip.loop(duration=video_duration)
            elif audio_duration > video_duration: 
                bgm_clip = bgm_clip.subclip(0, video_duration)
            bgm_clip = bgm_clip.volumex(self._params.bgm_volume)
            if video.audio is not None:
                original_audio = final_clip.audio
                combined_audio = CompositeAudioClip([original_audio, bgm_clip])
                final_clip = final_clip.set_audio(combined_audio)
            else:  # 否则直接设置新音频
                final_clip = final_clip.set_audio(bgm_clip)
        elif self._params.bgm_options == "custom" and self._params.bgm_file != "" and self._params.bgm_file != None:
            bgm_clip = AudioFileClip(self._params.bgm_file)
            video_duration = final_clip.duration
            audio_duration = bgm_clip.duration
            if audio_duration < video_duration:  
                bgm_clip = bgm_clip.loop(duration=video_duration)
            elif audio_duration > video_duration: 
                bgm_clip = bgm_clip.subclip(0, video_duration)
            bgm_clip = bgm_clip.volumex(self._params.bgm_volume)
            if video.audio is not None:
                original_audio = final_clip.audio
                combined_audio = CompositeAudioClip([original_audio, bgm_clip])
                final_clip = final_clip.set_audio(combined_audio)
            else:  # 否则直接设置新音频
                final_clip = final_clip.set_audio(bgm_clip)
        output_path = utils.random_filename(self.task_dir,".mp4")
        final_clip.write_videofile(output_path, codec="libx264")
        final_clip.close()
        for clip in clips:
            clip.close()
        self.merge_video_state.update_progress(1)
        return output_path

    def mian_task(self,video_script):
        tasks=[]
        for key in video_script.keys():
            sub_state = TaskProgress(weight = 4)
            self._state.append_sub_progress(sub_state)
            # self.sub_task(key,sub_state)
            tk = utils.run_in_background(task.sub_task,self,key,sub_state)
            tasks.append(tk)
        for t in tasks:
            t.join()
            print("------------------thread end")

        
    def sub_task(self,key,sub_state):
        sub_param = self._params.video_script[key]
        video_state = StepProgress(weight = 2)
        voice_state = StepProgress(weight = 1)
        merge_state = StepProgress(weight = 1)
        sub_state.set_sub_progress([video_state,voice_state,merge_state])
        if 'storyboard' not in sub_param or sub_param["storyboard"] == "":
            storyboard_state = TaskProgress(weight = 4)
            prompt_state = StepProgress(steps = 1,weight = 1)
            sdxl_state = StepProgress(weight = 1)
            storyboard_state.set_sub_progress([prompt_state,sdxl_state])
            sub_state.append_sub_progress(storyboard_state)
            prompts = llm.generate_prompt(sub_param["画面描述"])
            sub_param["positve_prompt"] = prompts[0]
            sub_param["negative_prompt"] = prompts[1]
            prompt_state.update_progress(1)
            sub_param["storyboard"] = storyboard.storyboard_creator(sub_param["positve_prompt"], sub_param["negative_prompt"],sdxl_state,video_style=self._params.video_style)
        
        if "video" not in sub_param or sub_param["video"] == "":
            sub_param["video"] = video.video_creator(self.video_dir,sub_param["storyboard"],video_state)
        else:
            video_state.set_steps(2)
            video_state.update_progress(2)

        voice_state.set_steps(1)
        sub_param["audio"] = voice.tts(sub_param["字幕内容"],self._params.voice_name,self.voice_dir)
        voice_state.update_progress(1)
        merge_state
        data = {}
        data["text"] = sub_param["字幕内容"]
        data["voice_volume"] = self._params.voice_volume
        data["subtitle_enabled"] = self._params.subtitle_enabled
        data["font_name"] = self._params.font_name
        data["subtitle_position"] = self._params.subtitle_position
        data["text_fore_color"] = self._params.text_fore_color
        data["font_size"] = self._params.font_size
        data["stroke_color"] = self._params.stroke_color
        data["stroke_width"] = self._params.stroke_width
        sub_param["subvideo"] = merge_voice_2_video(sub_param["video"],sub_param["audio"],self.subvideo_dir,data,merge_state)
        

