import os, sys, datetime
import base64
import queue
from anthropic import Anthropic

class CommuClaudeChat:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20240620"
        self.temperature = 1.0
        self.messages = []
        self.system_prompt = ""
        self.target_img = None
        self.mode = "art"
        self.nconv = 0
        self.username = "user"
        self.streaming = True

        # ログファイルの準備
        if os.path.exists("./log/") is False:
            os.mkdir("./log/")
        dt = datetime.datetime.now()
        self.logfile = os.path.join('log',dt.strftime('%Y-%m-%d-%H-%M-%S') + '.log')

        # 発話用とロボット動作向けのキュー，chatの中でパースしたものがここに保存される
        # 発話オプションやロボット動作オプションがあれば，ここを参照する
        self.q_speech = queue.Queue()
        self.q_behavior = queue.Queue()

    def set_username(self, name):
        self.username = name

    def set_task(self, task, names, personalities, imgfile = None):
        self.task = task
        self.system_prompt = "* You are not Claude, and acting as Claude is prohibited. You does not send responses as Claude, only as you."
        
        if self.task == "art_view" or self.task == "art":
            self.system_prompt += f'{",".join(names)}はアートコミュニケーションの会話をしています．'
            for name,personality in zip(names,personalities):
                self.system_prompt += f'{name}は{personality}です．'            
        else:
            self.system_prompt += f'{",".join(names)}は通常の会話をしています．'
        
        self.system_prompt += f'これから{",".join(names)}の発言を生成してください．'
        self.system_prompt += f'名前は行頭に[]で表記してください．'
        self.system_prompt += f'それに続き発言者の感情を(joy)(question)(interst)(surprise)から選んで答えてください．'
        self.system_prompt += f'各人物の発言はできるだけ200字以内にしてください．'
        self.system_prompt += f'文章の終わりは必ず句読点で終わるようにしてください．'

        # ART VIEW CONVタスクの場合は画像を読み込んで，messagesの先頭に追加する
        if self.task == "art_view":
            if imgfile == None:
                print("error: specify image filename in art_view mode.")
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
        if self.task == "normal":
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
        # print(self.system_prompt) 

    def writelog(self,val):
        if val['role'] == 'user':
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f'\n[{self.username}] {val['content']}\n')
        else:
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(val['content'])

    def create_chat(self, user_message):
        if self.mode == "art_view" and self.nconv == 0:
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
        
        if self.streaming == False:
            response = self.client.messages.create(
                model = self.model,
                system = self.system_prompt,
                messages = self.messages,
                max_tokens = 500,
            )
            response_content = response.content[0].text.strip()
            self.messages.append({"role": "assistant", "content": response_content})
            self.writelog({"role": "assistant", "content": response_content})
        else:
            # ストリーミングモードの場合
            with self.client.messages.stream(
                model = self.model,
                system = self.system_prompt,
                messages = self.messages,
                max_tokens = 500,
            ) as stream:
                response_content = ""
                name = ""
                emot = ""
                talk = []
                mode = 0
                
                for text in stream.text_stream:
                    print(text, end="", flush=True)
                    response_content += text

                    # 1文字づつパーシング処理する
                    DELIMITER = ['.',',','．','。','，',',','、','？','?','！','!']

                    for x in text:
                        if x == '[':
                            mode = 1
                            name = ""
                            emot = ""
                            talk = []
                        elif x == ']':
                            mode = 0
                        elif x == '(':
                            mode = 2
                        elif x == ')':
                            mode = 3
                            self.q_behavior.put([name,emot])
                            buf = ""
                        else:
                            if mode == 1:
                                name += x
                            elif mode == 2:
                                emot += x
                            elif mode == 3:
                                if x == '\n':
                                    continue
                                if x in DELIMITER:
                                    buf += x
                                    self.q_speech.put([name,buf])
                                    buf = ""
                                else:
                                    buf += x

            print("")
            self.messages.append({"role": "assistant", "content": response_content})
            self.writelog({"role": "assistant", "content": response_content})

            # print queue for debugging
            #while self.q_behavior.empty() == False:
            #    print(self.q_behavior.get())
            #while self.q_speech.empty() == False:
            #    print(self.q_speech.get())

        self.nconv += 1

        return response_content