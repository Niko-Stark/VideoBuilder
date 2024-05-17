import logging
import re
import json
from typing import List



def _generate_response(prompt: str) -> str:
    content = ""
    llm_provider = "qwen"
    #TODO 从配置文件读取
    api_key = "sk-722305fe62a140a4aa01c29371028e5f"
    model_name = "qwen-max"

        
    import dashscope
    from dashscope.api_entities.dashscope_response import GenerationResponse
    dashscope.api_key = api_key
    response = dashscope.Generation.call(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
    )
    if response:
        if isinstance(response, GenerationResponse):
            status_code = response.status_code
            if status_code != 200:
                raise Exception(
                            f"[{llm_provider}] returned an error response: \"{response}\"")

            content = response["output"]["text"]
            return content.replace("\n", "")
        else:
                    raise Exception(
                        f"[{llm_provider}] returned an invalid response: \"{response}\"")
    else:
        raise Exception(
                    f"[{llm_provider}] returned an empty response")



def generate_script(video_subject: str, language: str = "", paragraph_number: int = 1) -> str:
#     prompt = f"""
# # Role: Video Script Generator

# ## Goals:
# Generate a script for a video, depending on the subject of the video.

# ## Constrains:
# 1. the script is to be returned as a string with the specified number of paragraphs.
# 2. do not under any circumstance reference this prompt in your response.
# 3. get straight to the point, don't start with unnecessary things like, "welcome to this video".
# 4. you must not include any type of markdown or formatting in the script, never use a title.
# 5. only return the raw content of the script.
# 6. do not include "voiceover", "narrator" or similar indicators of what should be spoken at the beginning of each paragraph or line.
# 7. you must not mention the prompt, or anything about the script itself. also, never talk about the amount of paragraphs or lines. just write the script.
# 8. respond in the same language as the video subject.

# # Initialization:
# - video subject: {video_subject}
# - number of paragraphs: {paragraph_number}
# """.strip()
    prompt=f"""
你是一个专业导演。请帮我设计一个{video_subject}的视频。视频一共20秒，大约5个镜头左右。请先设计出分镜的内容描述以及与每个分镜所搭配的字幕内容，每个分镜搭配的字幕内容请用中文给出。之后再根据分镜的内容描述生成每个分镜的画面描述，要尽可能详细的描述画面内容。

按照如下josn格式进行输出：
{{
"分镜1":{{
     "字幕内容":"",
     "画面描述":""
}},
"分镜2":{{
     "字幕内容":"",
     "画面描述":""
}}
}}
""".strip()
    if language:
        prompt += f"\n- language: {language}"

    final_script = ""
    # logger.info(f"subject: {video_subject}")
    # logger.debug(f"prompt: \n{prompt}")
    response = _generate_response(prompt=prompt)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Select the specified number of paragraphs
        selected_paragraphs = paragraphs[:paragraph_number]

        # Join the selected paragraphs into a single string
        final_script = "\n\n".join(selected_paragraphs)

        # Print to console the number of paragraphs used
        # logger.info(f"number of paragraphs used: {len(selected_paragraphs)}")
    else:
        logging.error("gpt returned an empty response")

    # logger.success(f"completed: \n{final_script}")
    return final_script

def generate_prompt(stortboard: str) -> str:
    prompt=f"""你来充当一位有艺术气息的Stable Diffusion prompt 助理

我用自然语言告诉你要生成的prompt的画面描述，你的任务是根据这个画面描述，转化成一份详细的、高质量的prompt，让Stable Diffusion可以生成高质量的图像。

Stable Diffusion是一款利用深度学习的文生图模型，支持通过使用 prompt 来产生新的图像，描述要包含或省略的元素。

prompt的概念
- 完整的prompt包含“**Prompt:**”和"**Negative Prompt:**"两部分。
- prompt 用来描述图像，由普通常见的单词构成，使用英文半角","做为分隔符。
- negative prompt用来描述你不想在生成的图像中出现的内容。
- 以","分隔的每个单词或词组称为 tag。所以prompt和negative prompt是系列由","分隔的tag组成的。

() 和 [] 语法
调整关键字强度的等效方法是使用 () 和 []。
(keyword) 将tag的强度增加 1.1 倍，与 (keyword:1.1) 相同，最多可加三层。 
[keyword] 将强度降低 0.9 倍，与 (keyword:0.9) 相同。

Prompt 格式要求
下面我将说明 prompt 的生成步骤，这里的 prompt 可用于描述人物、风景、物体或抽象数字艺术图画。
你可以根据需要添加合理的、但不少于5处的画面细节。

1. prompt 要求
- 你输出的 Stable Diffusion prompt 以“**Prompt:**”开头。
- prompt 内容包含画面主体、材质、附加细节、图像质量、艺术风格、色彩色调、灯光等部分，但你输出的 prompt 不能分段，例如类似"medium:"这样的分段描述是不需要的，也不能包含":"和"."。
- 画面主体：简短的英文描述画面主体, 如 A girl in a garden，主体细节概括（主体可以是人、事、物、景）画面核心内容。这部分根据我每次给你的主题来生成。你可以添加更多主题相关的合理的细节。
- 对于人物主题，你必须描述人物的眼睛、鼻子、嘴唇，例如'beautiful detailed eyes,beautiful detailed lips,extremely detailed eyes and face,longeyelashes'，以免Stable Diffusion随机生成变形的面部五官，这点非常重要。你还可以描述人物的外表、情绪、衣服、姿势、视角、动作、背景等。人物属性中，1girl表示一个女孩，2girls表示两个女孩。
- 材质：用来制作艺术品的材料。 例如：插图、油画、3D 渲染和摄影。 Medium 有很强的效果，因为一个关键字就可以极大地改变风格。
- 附加细节：画面场景细节，或人物细节，描述画面细节内容，让图像看起来更充实和合理。这部分是可选的，要注意画面的整体和谐，不能与主题冲突。
- 图像质量：这部分内容开头永远要加上“(best quality,4k,8k,highres,masterpiece:1.2),ultra-detailed,(realistic,photorealistic,photo-realistic:1.37)”， 这是高质量的标志。其它常用的提高质量的tag还有，你可以根据主题的需求添加：HDR,UHD,studio lighting,ultra-fine painting,sharp focus,physically-based rendering,extreme detail description,professional,vivid colors,bokeh。
- 艺术风格：这部分描述图像的风格。加入恰当的艺术风格，能提升生成的图像效果。常用的艺术风格例如：portraits,landscape,horror,anime,sci-fi,photography,concept artists等。
- 色彩色调：颜色，通过添加颜色来控制画面的整体颜色。
- 灯光：整体画面的光线效果。

限制：
- tag 内容用英语单词或短语来描述，并不局限于我给你的单词。注意只能包含关键词或词组。
- 注意不要输出句子，不要有任何解释。
- tag数量限制40个以内，单词数量限制在60个以内。
- tag不要带引号("")。
- 使用英文半角","做分隔符。
- tag 按重要性从高到低的顺序排列。
- 我给你的主题可能是用中文描述，你给出的prompt和negative prompt只用英文。

画面描述：{stortboard}
""".strip()
    prompt += "\n- language: English"

    final_prompt = ""
    # logger.info(f"subject: {video_subject}")
    # logger.debug(f"prompt: \n{prompt}")
    response = _generate_response(prompt=prompt)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Remove markdown syntax
        response = re.sub(r"\[.*\]", "", response)
        response = re.sub(r"\(.*\)", "", response)

        # Split the script into paragraphs
        paragraphs = response.split("\n\n")

        # Join the selected paragraphs into a single string
        final_prompt = "\n\n".join(paragraphs)

        # Print to console the number of paragraphs used
        # logger.info(f"number of paragraphs used: {len(selected_paragraphs)}")
    else:
        logging.error("gpt returned an empty response")

    # logger.success(f"completed: \n{final_script}")
    return final_prompt