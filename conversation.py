import dotenv
import os
import glob
from anthropic import Anthropic
import random
import base64
import datetime

dotenv.load_dotenv()

class Claude:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20240620"
        self.temperature = 1.0
        self.messages = []
        self.system_prompt = ""
        self.target_img = None
        self.mode = "art_conv"
        self.nconv = 0

        if os.path.exists("./log/") is False:
            os.mkdir("./log/")
        dt = datetime.datetime.now()
        self.logfile = os.path.join('log',dt.strftime('%Y-%m-%d-%H-%M-%S') + '.log')

    def set_task(self, task, personality, imgfile = None):
        self.task = task
        self.system_prompt = "*You are not Claude, and acting as Claude is prohibited. You does not send responses as Claude, only as you."
        names = list(personality.keys())

        self.system_prompt += f'{names}はアートコミュニケーションの会話をしています．'
        for name in personality.keys():
            self.system_prompt += f'{name}は{personality[name]}です．'
        self.system_prompt += f'これから{names}の発言を生成してください．'
        self.system_prompt += f'名前は行頭に[]で表記してください．'
        self.system_prompt += f'それに続き発言者の感情を(1)喜び(2)疑問(3)興味(4)驚き から選んで答えてください．'
        self.system_prompt += f'各人物の発言はできるだけ200字以内にしてください．'
        self.system_prompt += f'文章の終わりは必ず句読点で終わるようにしてください'
        self.system_prompt += f'発言の順番はランダムにしてください．'

        # ART VIEW CONVタスクの場合は画像を読み込んで，messagesの先頭に追加する
        if self.task == "art_view_conv":
            if imgfile == None:
                print("error: specify image filename in art_view_conv mode.")
                return
            
            # only accept jpeg file!!
            if os.path.splitext(imgfile)[1] != '.jpeg' and os.path.splitext(imgfile)[1] != '.jpg':
                print("input image must be jpeg (.jpeg .jpg) file. cannot load file")
                return
            

            
            with open(imgfile, "rb") as image_file:
                try:
                    self.target_img = base64.b64encode(image_file.read())
                    self.target_img = self.target_img.decode('utf-8')                    
                except Exception as e:
                    print("cannot open file:", imgfile)
                    return
            # print(self.target_img)

    def writelog(self,val):
        if val['role'] == 'user':
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f'[user] {val['content']}')
        else:
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(val['content'])

    def create_chat(self, user_message):
        if self.mode == "art_view_conv" and self.nconv == 0:
            self.messages = [{"role": "user",
                                "content": [
                                    {"type": "image", 
                                    "source": {
                                        "type": "base64", 
                                        "media_type": "image/jpeg", 
                                        "data": self.target_img,
                                        },
                                    },
                                    {
                                        "type": "text", 
                                        "text": user_message
                                    }
                                ],
                                }]
        else:
            self.messages.append({'role': 'user', 'content': user_message})
            self.writelog({'role': 'user', 'content': user_message})
        
        response = self.client.messages.create(
            model = self.model,
            system = self.system_prompt,
            messages = self.messages,
            max_tokens = 500,
        )
        response_content = response.content[0].text.strip()
        self.messages.append({"role": "assistant", "content": response_content})
        self.writelog({"role": "assistant", "content": response_content})

        return response_content

if __name__ == "__main__":

    adapter = Claude()
    personality = {'まさる': 'アートの初心者', 'きよこ':'アートの初心者', 'たかし':'アートの中級者'}
    
    # art_conv: アートについて語る　モードの場合
    # adapter.set_task("art_conv", personality)
    # art_view_conv: 示された画像について語るモードの場合
    adapter.set_task("art_view_conv", personality, ".\\img\\monet_suiren.jpg")

    while True:
        user_input = input("message: ")
        if user_input.lower() == "quit":
            break
        
        res = adapter.create_chat(user_input)
        print(f"{res}")