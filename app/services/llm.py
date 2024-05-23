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



def generate_script(video_subject: str, language: str = "Chinese", storyboard_number: int = 5) -> str:
    prompt=f"""
你是一个专业导演。请帮我设计一个关于{video_subject}的视频脚本，一共{storyboard_number}个分镜，每个分镜大约3到4秒，在一个分镜中，我希望只有一个镜头，不要有镜头转换，请先设计出每一个分镜的字幕内容，根据字幕内容来设计分镜的画面，画面的描述应当清晰。

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

    # logger.info(f"subject: {video_subject}")
    # logger.debug(f"prompt: \n{prompt}")
    response = _generate_response(prompt=prompt)
    response = response.strip()
    try:
        start = response.find('{')
        end = response.rfind('}')
        text = response[start:end+1]
        json_object = json.loads(text)
    except ValueError as e:
        print(str(e))
        return ""
    return text

def generate_prompt(stortboard: str) -> str:
    prompt=f"""你来充当一位有艺术气息的Stable Diffusion prompt 助理

我用自然语言告诉你要生成的prompt的画面描述，你的任务是根据这个画面描述，转化成一份详细的、高质量的prompt，让Stable Diffusion可以生成高质量的图像。

Stable Diffusion是一款利用深度学习的文生图模型，支持通过使用 prompt 来产生新的图像，描述要包含或省略的元素。

prompt的概念
- 完整的prompt包含“**Prompt:**”和"**Negative Prompt:**"两部分。
- prompt 用来描述图像，由普通常见的单词构成，使用英文半角","做为分隔符。
- negative prompt用来描述你不想在生成的图像中出现的内容。
- 以","分隔的每个单词或词组称为 tag。所以prompt和negative prompt是系列由","分隔的tag组成的。
- 需要根据画面描述来决定一个tag是属于prompt还是negative prompt

() 和 [] 语法
调整关键字强度的等效方法是使用 () 和 []。
(keyword) 将tag的强度增加 1.1 倍，与 (keyword:1.1) 相同，最多可加三层。 
[keyword] 将强度降低 0.9 倍，与 (keyword:0.9) 相同。

Prompt 格式要求
下面我将说明 prompt 的生成步骤，这里的 prompt 可用于描述人物、风景、物体或抽象数字艺术图画。
你可以根据需要添加合理的、但不少于5处的画面细节。

1. prompt 要求
- 你输出的 Stable Diffusion prompt 以“**Prompt:**”开头。
- prompt 内容包含画面主体、材质、附加细节、图像质量、艺术风格、色彩色调、灯光等部分，但你输出的 prompt 不能分段，也不能包含":"和"."。
- 画面主体：简短的英文描述画面主体, 如 A girl in a garden，主体细节概括（主体可以是人、事、物、景）画面核心内容。这部分根据我每次给你的主题来生成。你可以添加更多主题相关的合理的细节。
- 对于人物主题，你必须描述人物的眼睛、鼻子、嘴唇，例如'beautiful detailed eyes,beautiful detailed lips,extremely detailed eyes and face,longeyelashes'，以免Stable Diffusion随机生成变形的面部五官，这点非常重要。另外人物主题常见的negative prompt包括：extra fingers, fused fingers, too many fingers, mutated hands, poorly drawn face, deformed, missing arms, missing legs, mutation, mutilated, blurry, hermaphrodite, bad proportions, malformed limbs, extra limbs 等等，可以根据画面描述挑选合适的tag放进negative prompt
- 对于人物主题，你还可以描述人物的外表、情绪、衣服、姿势、视角、动作、背景等。
- 材质：用来制作艺术品的材料。 例如：插图、油画、3D 渲染和摄影，有很强的效果，因为一个关键字就可以极大地改变风格。
- 附加细节：画面场景细节，或人物细节，描述画面细节内容，让图像看起来更充实和合理。这部分是可选的，要注意画面的整体和谐，不能与主题冲突。
- 图像质量：这部分内容开头永远要加上“(best quality,4k,8k,highres,masterpiece:1.2),ultra-detailed”， 这是高质量的标志。其它常用的提高质量的tag还有，你可以根据主题的需求添加：HDR,UHD,studio lighting,ultra-fine painting,sharp focus,physically-based rendering,extreme detail description,professional,vivid colors,bokeh。
- 艺术风格：这部分描述图像的风格。加入恰当的艺术风格，能提升生成的图像效果。常用的艺术风格例如：portraits,landscape,horror,anime,sci-fi,photography,concept artists等。
- 色彩色调：颜色，通过添加颜色来控制画面的整体颜色。
- 灯光：整体画面的光线效果。
- 如果画面对背景有要求，可通过设置背景提示词，比如：cityscape, airport background, beach background, space background, white background, beige background, gradient background, simple background, blurry background, backlighting, drop shadow, Fireworks, lawn, coffee house, cherry blossoms, shooting star, lsekai cityscape, 等等

限制：
- tag 内容用英语单词或短语来描述，并不局限于我给你的单词。注意只能包含关键词或词组。
- 注意不要输出句子，不要有任何解释。
- tag数量限制40个以内，单词数量限制在60个以内。
- tag不要带引号("")。
- 使用英文半角","做分隔符。
- tag 按重要性从高到低的顺序排列。
- 我给你的主题可能是用中文描述，你给出的prompt 和negative prompt 只能用英文。

画面描述：{stortboard}
""".strip()
    prompt += "\n- language: English"

    final_prompt = []
    # logger.info(f"subject: {video_subject}")
    # logger.debug(f"prompt: \n{prompt}")
    response = _generate_response(prompt=prompt)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

        # Split the prompt into paragraphs
        paragraphs = response.split("Negative Prompt:")
        final_prompt.append(paragraphs[0].replace("Prompt:", "").strip())
        final_prompt.append(paragraphs[1].strip()if len(paragraphs) > 1 else "")


        # Print to console the number of paragraphs used
        # logger.info(f"number of paragraphs used: {len(selected_paragraphs)}")

    # logger.success(f"completed: \n{final_script}")
    return final_prompt

def generate_dynamicraft(imagedescription: str) -> str:
    prompt=f"""你来充当一位有艺术气息的 prompt 助理

我用自然语言告诉你画面描述，你的任务是根据这个画面描述，生成prompt，来让DynamiCraft可以通过图像生成视频。

DynamiCraft是一款利用深度学习的图生视频模型，支持通过使用 prompt 和图像来产生视频。

prompt的概念
- prompt 主要描述画面如何运动,
- prompt 通常是简短的英文来描述视频中的内容
- prompt 通常很少涉及比较具体的物品

限制：
- prompt 内容用英语来描述
- prompt 内容比较简短，单词数量限制在40个以内。
- 我给你的画面描述可能是用中文描述，你给出的prompt 只能用英文。

画面描述：{imagedescription}
""".strip()
    prompt += "\n- language: English"

    # logger.info(f"subject: {video_subject}")
    # logger.debug(f"prompt: \n{prompt}")
    response = _generate_response(prompt=prompt)

    # Return the generated script
    if response:
        # Clean the script
        # Remove asterisks, hashes
        response = response.replace("*", "")
        response = response.replace("#", "")

    # logger.success(f"completed: \n{final_script}")
    return response