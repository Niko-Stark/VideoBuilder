from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel
import warnings

# 忽略 Pydantic 的特定警告
warnings.filterwarnings("ignore", category=UserWarning, message="Field name.*shadows an attribute in parent.*")


class VideoGenerationMode(str, Enum):
    text2video = "text2video"
    image2video = "image2video"


class VideoParams:
    video_subject: Optional[str] = ""
    video_language: Optional[str] = ""
    storyboard_num= 1
    video_generation_modes:VideoGenerationMode
    video_style: Optional[str] = ""

    voice_name: Optional[str] = ""
    voice_volume:float = 0.5
    bgm_options: Optional[str] = ""
    bgm_file: Optional[str] = ""
    bgm_volume:float = 0.0

    subtitle_enabled:bool
    font_name: Optional[str] = "bottom"
    subtitle_position: Optional[str] = "STHeitiMedium.ttc"
    text_fore_color: Optional[str] = "#FFFFFF"
    font_size:int = 24
    stroke_color: Optional[str] = "#000000"
    stroke_width: float = 1.5

    video_script = {}
