from datetime import datetime

import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from app.utils import utils

@st.cache_data
def get_all_voices() -> list[str]:
    voices = [
        ("zh-CN-XiaoxiaoNeural（女）", "zh-CN-XiaoxiaoNeural",),
        ("zh-CN-YunxiNeural（男）", "zh-CN-YunxiNeural",),
        ("zh-CN-YunjianNeural（男）", "zh-CN-YunjianNeural",),
        ("zh-CN-XiaoyiNeural（女）", "zh-CN-XiaoyiNeural",),
        ("zh-CN-YunyangNeural（男）", "zh-CN-YunyangNeural",),
        ("zh-CN-XiaochenNeural（女）", "zh-CN-XiaochenNeural",),
        ("zh-CN-XiaohanNeural（女）", "zh-CN-XiaohanNeural",),
        ("zh-CN-XiaomengNeural（女）", "zh-CN-XiaomengNeural",),
        ("zh-CN-XiaomoNeural（女）", "zh-CN-XiaomoNeural",),
        ("zh-CN-XiaoqiuNeural（女）", "zh-CN-XiaoqiuNeural",),
        ("zh-CN-XiaoruiNeural（女）", "zh-CN-XiaoruiNeural",),
        ("zh-CN-XiaoshuangNeural（女性、儿童）", "zh-CN-XiaoshuangNeural",),
        ("zh-CN-XiaoyanNeural（女）", "zh-CN-XiaoyanNeural",),
        ("zh-CN-XiaoyouNeural（女性、儿童）", "zh-CN-XiaoyouNeural",),
        ("zh-CN-XiaozhenNeural（女）", "zh-CN-XiaozhenNeural",),
        ("zh-CN-YunfengNeural（男）", "zh-CN-YunfengNeural",),
        ("zh-CN-YunhaoNeural（男）", "zh-CN-YunhaoNeural",),
        ("zh-CN-YunxiaNeural（男）", "zh-CN-YunxiaNeural",),
        ("zh-CN-YunyeNeural（男）", "zh-CN-YunyeNeural",),
        ("zh-CN-YunzeNeural（男）", "zh-CN-YunzeNeural",),
        ("zh-CN-XiaochenMultilingualNeural（女）", "zh-CN-XiaochenMultilingualNeural",),
        ("zh-CN-XiaorouNeural（女）", "zh-CN-XiaorouNeural",),
        ("zh-CN-XiaoxiaoDialectsNeural（女）", "zh-CN-XiaoxiaoDialectsNeural",),
        ("zh-CN-XiaoxiaoMultilingualNeural（女）", "zh-CN-XiaoxiaoMultilingualNeural",),
        ("zh-CN-XiaoyuMultilingualNeural（女）", "zh-CN-XiaoyuMultilingualNeural",),
        ("zh-CN-YunjieNeural（男）", "zh-CN-YunjieNeural",),
        ("zh-CN-YunyiMultilingualNeural（男）","zh-CN-YunyiMultilingualNeural")]
    return voices

def _format_duration_to_offset(duration) -> int:
        if isinstance(duration, str):
            time_obj = datetime.strptime(duration, "%H:%M:%S.%f")
            milliseconds = (time_obj.hour * 3600000) + (time_obj.minute * 60000) + (time_obj.second * 1000) + (
                    time_obj.microsecond // 1000)
            return milliseconds * 10000

        if isinstance(duration, int):
            return duration

        return 0

def tts(text:str, voice_name: str, voice_file_dir: str):
    
    #TODO 从config获取
    speech_key = "07377bdc722f4cb38d02853abe118ad6"
    service_region = "eastus"
    speech_config = speechsdk.SpeechConfig(subscription=speech_key,region=service_region)
    
    text = text.strip()
    voice_file = utils.random_filename(voice_file_dir,".mp3")
    for i in range(3):
        try:
            audio_config = speechsdk.audio.AudioOutputConfig(filename=voice_file, use_default_speaker=True)
            
            speech_config.speech_synthesis_voice_name = voice_name
            speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
            speech_synthesizer = speechsdk.SpeechSynthesizer(audio_config=audio_config,speech_config=speech_config)
            result = speech_synthesizer.speak_text_async(text).get()
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # logger.success(f"azure v2 speech synthesis succeeded: {voice_file}")
                return voice_file
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"azure v2 speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"azure v2 speech synthesis error: {cancellation_details.error_details}")
                return ""
            print(f"completed, output file: {voice_file}")
        except Exception as e:
            print(f"failed, error: {str(e)}")
    return ""
