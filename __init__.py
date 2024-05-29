import hashlib
import json
import time
import requests
import os
import comfy.utils

import folder_paths
comfy_path = os.path.dirname(folder_paths.__file__)

gen_video_url = " https://openman.weta365.com/metaman/open/image/toman/cmp"
get_video_url = "https://openman.weta365.com/metaman/open/image/toman/cmp/result/"

def gen_video_with_url(appkey,secret,imageUrl,text):
    timestamp = str(int(time.time()))
    message = '+'.join([appkey, secret, timestamp])
    m = hashlib.md5()
    m.update(message.encode('utf-8'))
    signature = m.hexdigest()
    req = {
        "imageUrl": imageUrl,
        "audioUrl": '',
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

class MobvoiOpenapiMetaman:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "appkey":("STRING",{"default":"08729F3204B2CF104B70EB0587E7AF13"}),
                "secret":("STRING",{"default":"498EDA176F801CD6C52BA1B24213466B"}),
                "imageurl":("STRING",{"default":"http://glj.snrcsoft.com:30002/test.webp"}),
                "text":("STRING",{"default":"测试生成数字人，测试生成数字人1234566","multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "MobvoiOpenapi"

    def run(self,appkey,secret,imageurl,text):
        pbar = comfy.utils.ProgressBar(10)
        video_url='https://mobvoi-digitalhuman-video-public.weta365.com/1795659856343478272.mp4'
        video_id = gen_video_with_url(appkey,secret,imageurl,text)
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
    "MobvoiOpenapiMetaman":MobvoiOpenapiMetaman,
    "HtmlViewer":HtmlViewer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MobvoiOpenapiMetaman": "MobvoiOpenapiMetaman",
    "MobvoiOpenapiMetaman": "MobvoiOpenapiMetaman"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']