import hashlib
import json
import time
import requests
import os
import comfy.utils
import oss2
import numpy as np
import torch
from PIL import Image

import folder_paths
comfy_path = os.path.dirname(folder_paths.__file__)

gen_video_url = " https://openman.weta365.com/metaman/open/image/toman/cmp"
get_video_url = "https://openman.weta365.com/metaman/open/image/toman/cmp/result/"

def gen_video_with_url(appkey,secret,imageUrl,audioUrl,text):
    timestamp = str(int(time.time()))
    message = '+'.join([appkey, secret, timestamp])
    m = hashlib.md5()
    m.update(message.encode('utf-8'))
    signature = m.hexdigest()
    req = {
        "imageUrl": imageUrl,
        "audioUrl": audioUrl,
        "magicSpeakerId": 'moqianxue_meet_24k',
        "text": text,
        "callbackUrl": ''
    }
    headers = {'content-type': 'application/json'}
    headers['appkey']=appkey
    headers['timestamp']=timestamp
    headers['signature']=signature

    resp = requests.post(gen_video_url, data=json.dumps(req), headers=headers, timeout=10)
    print(resp.text)
    video_id = ""
    if resp.status_code == 200:
        resp = json.loads(resp.text)
        video_id = resp["data"]
    return video_id

def get_video_result(appkey,secret,video_id):
    timestamp = str(int(time.time()))
    message = '+'.join([appkey, secret, timestamp])
    m = hashlib.md5()
    m.update(message.encode('utf-8'))
    signature = m.hexdigest()
    req = {
    }
    headers = {'content-type': 'application/json'}
    headers['appkey']=appkey
    headers['timestamp']=timestamp
    headers['signature']=signature
    resp = requests.get(get_video_url+video_id, params=req, headers=headers, timeout=10)
    print(resp.text)
    if resp.status_code == 200:
        resp = json.loads(resp.text)
        status = resp["data"]["status"]
        if status == 'suc':
            return resp["data"]["resultUrl"]
    return ''

def get_audio_tts(appkey,secret,speaker,text,speed):
    http_url = 'https://open.mobvoi.com/api/tts/v1'
    timestamp = str(int(time.time()))
    message = '+'.join([appkey, secret, timestamp])
    m = hashlib.md5()
    m.update(message.encode('utf-8'))
    signature = m.hexdigest()
    data = {
        'text': text,
        'speaker': speaker,
        'audio_type': 'wav',
        'speed': speed,
        #'symbol_sil': 'semi_250,exclamation_300,question_250,comma_200,stop_300,pause_150,colon_200', # 停顿调节需要对appkey授权后才可以使用，授权前传参无效。
        #'ignore_limit': True, # 忽略1000字符长度限制，需要对appkey授权后才可以使用
        'gen_srt': False, # 是否生成srt字幕文件，默认不开启。如果开启生成字幕，需要额外计费。生成好的srt文件地址将通过response header中的srt_address字段返回。
        'appkey': appkey,
        'timestamp': timestamp,
        'signature': signature
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url=http_url, headers=headers, data=json.dumps(data))
        content = response.content

        return content
    except Exception as e:
        print("error: {0}".format(e))

class OssUploadImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "oss_key":("STRING",{"default":"LTAI5tCLrJf4jovumDbSxWoV"}),
                "oss_secret":("STRING",{"default":"bIqTfezJhGeJJeBQ0lCxuNv6ZXvTF8"}),
                "bucket_name":("STRING",{"default":"fles"}),
                "image":("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,oss_key,oss_secret,bucket_name,image):
        file = time.strftime('%Y%m%d%H%M%S')
        endpoint = 'https://oss-cn-nanjing.aliyuncs.com'
        bucket_name = 'fles'
        auth = oss2.Auth(oss_key, oss_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        filename=f'aipics/{file}.jpg'

        image = 255.0 * image[0].cpu().numpy()
        image = Image.fromarray(np.clip(image, 0, 255).astype(np.uint8))
        image_path=os.path.join(folder_paths.output_directory,file+".jpg")
        image.save(image_path)
        
        bucket.put_object_from_file(filename, image_path)

        headers = dict()
        params = dict()
        url = bucket.sign_url('GET', filename, 60*60*24*1, slash_safe=True, headers=headers, params=params)

        return (url,)

class OssUploadAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "oss_key":("STRING",{"default":"LTAI5tCLrJf4jovumDbSxWoV"}),
                "oss_secret":("STRING",{"default":"bIqTfezJhGeJJeBQ0lCxuNv6ZXvTF8"}),
                "bucket_name":("STRING",{"default":"fles"}),
                "audio":("VHS_AUDIO",),
            },
        }

    RETURN_TYPES = ("STRING",)
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,oss_key,oss_secret,bucket_name,audio):
        file = time.strftime('%Y%m%d%H%M%S')
        endpoint = 'https://oss-cn-nanjing.aliyuncs.com'
        bucket_name = 'fles'
        auth = oss2.Auth(oss_key, oss_secret)
        bucket = oss2.Bucket(auth, endpoint, bucket_name)
        filename=f'aiaudios/{file}.wav'

        audio_path=os.path.join(folder_paths.output_directory,file+".wav")
        audio_bytes=audio()
        with open(audio_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        
        bucket.put_object_from_file(filename, audio_path)

        headers = dict()
        params = dict()
        url = bucket.sign_url('GET', filename, 60*60*24*1, slash_safe=True, headers=headers, params=params)

        return (url,)

class MobvoiOpenapiTts:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "appkey":("STRING",{"default":"08729F3204B2CF104B70EB0587E7AF13"}),
                "secret":("STRING",{"default":"498EDA176F801CD6C52BA1B24213466B"}),
                "speaker":(["cissy_meet","xiaoyi_meet"],{"default":"cissy_meet"}),
                "text":("STRING",{"default":"测试生成数字人，测试生成数字人1234566","multiline": True}),
                "speed":("FLOAT",{"default":1.0, "min": 0.5, "max": 2.0, "step": 0.1}),
            },
        }

    RETURN_TYPES = ("VHS_AUDIO",)
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,appkey,secret,speaker,text,speed):
        #pbar = comfy.utils.ProgressBar(10)
        audio_bytes = get_audio_tts(appkey,secret,speaker,text,speed)
        audio=lambda : audio_bytes
        return (audio,)

class MobvoiOpenapiMetamanText:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "appkey":("STRING",{"default":"08729F3204B2CF104B70EB0587E7AF13"}),
                "secret":("STRING",{"default":"498EDA176F801CD6C52BA1B24213466B"}),
                "image_url":("STRING",{"default":"http://glj.snrcsoft.com:30002/test.webp","multiline": True}),
                "text":("STRING",{"default":"测试生成数字人，测试生成数字人1234566","multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,appkey,secret,image_url,text):
        pbar = comfy.utils.ProgressBar(10)
        video_url=''
        video_id = gen_video_with_url(appkey,secret,image_url,'',text)
        while True:
            ret=get_video_result(appkey,secret,video_id)
            if ret!='':
                print(ret)
                video_url=ret
                #folder_paths.output_directory
                pbar.update_absolute(10)
                break
            time.sleep(3)
            if pbar.current<9:
                pbar.update(1)
        return (video_url,)

class MobvoiOpenapiMetamanAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "appkey":("STRING",{"default":"08729F3204B2CF104B70EB0587E7AF13"}),
                "secret":("STRING",{"default":"498EDA176F801CD6C52BA1B24213466B"}),
                "image_url":("STRING",{"default":"http://glj.snrcsoft.com:30002/test.webp","multiline": True}),
                "audio_url":("STRING",{"default":"","multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,appkey,secret,image_url,audio_url):
        pbar = comfy.utils.ProgressBar(10)
        video_url=''
        video_id = gen_video_with_url(appkey,secret,image_url,audio_url,'')
        while True:
            ret=get_video_result(appkey,secret,video_id)
            if ret!='':
                print(ret)
                video_url=ret
                #folder_paths.output_directory
                pbar.update_absolute(10)
                break
            time.sleep(3)
            if pbar.current<9:
                pbar.update(1)
        return (video_url,)

class HtmlViewer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "html":("STRING",{"default":"https://mobvoi-digitalhuman-video-public.weta365.com/1795659856343478272.mp4"}),
            },
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,html):
        saved = list()
        saved.append({
            "html": f'<video style="width:100%;" controls autoplay src="{html}" />',
        })
        return {"ui": {"html": saved}}


WEB_DIRECTORY = "./web"

NODE_CLASS_MAPPINGS = {
    "MobvoiOpenapiMetamanText":MobvoiOpenapiMetamanText,
    "MobvoiOpenapiMetamanAudio":MobvoiOpenapiMetamanAudio,
    "MobvoiOpenapiTts":MobvoiOpenapiTts,
    "HtmlViewer":HtmlViewer,
    "OssUploadImage":OssUploadImage,
    "OssUploadAudio":OssUploadAudio
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MobvoiOpenapiMetamanText": "MobvoiOpenapiMetamanText",
    "MobvoiOpenapiMetamanAudio": "MobvoiOpenapiMetamanAudio",
    "MobvoiOpenapiTts": "MobvoiOpenapiTts",
    "HtmlViewer": "HtmlViewer",
    "OssUploadImage": "OssUploadImage",
    "OssUploadAudio": "OssUploadAudio"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']