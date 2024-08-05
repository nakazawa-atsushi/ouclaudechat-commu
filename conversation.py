import dotenv
import os
import glob
import sys
from anthropic import Anthropic
import random
import base64
import datetime
import argparse

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

    def set_task(self, task, names, personalities, imgfile = None):
        self.task = task
        self.system_prompt = "* You are not Claude, and acting as Claude is prohibited. You does not send responses as Claude, only as you."
        
        if self.task == "art_view_conv" or self.task == "art_conv":
            self.system_prompt += f'{",".join(names)}, userはアートコミュニケーションの会話をしています．'
            for name,personality in zip(names,personalities):
                self.system_prompt += f'{name}は{personality}です．'            
        else:
            self.system_prompt += f'{",".join(names)}, userは通常の会話をしています．'
        
        self.system_prompt += f'これから{",".join(names)}の発言を生成してください．'
        self.system_prompt += f'名前は行頭に[]で表記してください．'
        self.system_prompt += f'それに続き発言者の感情を(1)喜び(2)疑問(3)興味(4)驚き から選んで答えてください．'
        self.system_prompt += f'各人物の発言はできるだけ200字以内にしてください．'
        self.system_prompt += f'文章の終わりは必ず句読点で終わるようにしてください．'

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
        
        # 通常会話の場合，それぞれのパーソナリティを設定する
        if self.task == "normal_conv":
            for name,personality in zip(names,personalities):
                # personality directoryから文章を読み出し名前を変換する
                fname = os.path.join('personality',f"p_{personality}.txt")
                with open(fname,'r',encoding="utf-8") as f:
                    try:
                        l = f.read()
                        l = l.replace('{name}',name)
                        self.system_prompt += l
                    except Exception as e:
                        print("cannot open file:", imgfile)
        
        print(self.system_prompt) 

    def writelog(self,val):
        if val['role'] == 'user':
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f'\n[user] {val['content']}\n')
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
        
        self.writelog({'role': 'user', 'content': user_message + '\n'})
        
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

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task")     # タスク
    parser.add_argument('-f', "--img_file")
    args = parser.parse_args()
    # print(args.task, args.img_file)

    if args.task is None:
        print("specify task by option -t [art_conv|art_view_conv|normal_conv]")
        sys.exit(0)

    # setup claude
    adapter = Claude()
    
    if args.task == "art_conv":
        # art_conv: アートについて語る　モードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_conv", names, personalities)
    elif args.task == "art_view_conv":
        # art_view_conv: 示された画像について語るモードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_view_conv", names, personalities, args.img_file)
    elif args.task == "normal_conv":
        names = ['たかし','きよこ','まさお']
        personalities = ['average','selfcenter','average']
        adapter.set_task("normal_conv", names, personalities)

    while True:
        user_input = input("message: ")
        if user_input.lower() == "quit":
            break

        res = adapter.create_chat(user_input)
        print(f"{res}")