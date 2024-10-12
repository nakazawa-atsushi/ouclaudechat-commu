import threading
import os
import base64
import glob
import datetime
import queue
import re
from anthropic import Anthropic
from commu_claude_chat import CommuClaudeChat
from play_voicebox import play_voicebox
from local_whisper_mic import WhisperMic

class extract_name():
    def __init__(self) -> None:
        self.client = Anthropic()

    def tool(self):
        with open("tool_description.txt","r",encoding="utf-8") as f:
            description = f.read()
        tools = [
            {
                "name": "name_extraction",
                "description": description,
                "input_schema":{
                    "type": "object",
                    "properties":{
                        "speaker_name":{
                            "type": "string",
                            "description": "Names extracted from conversational text"
                        }
                    },
                    "required": ["speaker_name"]
                },
            }
        ]
        return tools

    def extract_claude(self,text):
        tools = self.tool()
        res = self.client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            tools=tools,
            messages=[{"role":"user","content":text}]
        )
        print(res)
        if not res.stop_reason == "tool_use":
            return "", res.stop_reason

        return res.content[1].input["speaker_name"], res.stop_reason

class intro_chat():
    def __init__(self) -> None:
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20240620"
        self.temperature = 1.0
        self.messages = []
        self.system_prompt = ""
        self.target_img = None
        self.mode = "art"
        self.nconv = 0
        self.username = "user"
        self.streaming = True
        self.exnumber = 0
        if os.path.exists("./log/") is False:
            os.mkdir("./log/")
        dt = datetime.datetime.now()
        self.logfile = os.path.join('log',dt.strftime('%Y-%m-%d-%H-%M-%S') + '.log')
        self.q_speech = queue.Queue()
        self.q_behavior = queue.Queue()
        
    def initial_set(self, task, names, personalities, attributes, imgfile = None, experience_flag:bool = False):
        self.task = task
        self.system_prompt = "* You are not Claude, and acting as Claude is prohibited. You does not send responses as Claude, only as you."
        print(experience_flag)
        
        if self.task == "art_view" or self.task == "art":
            print("art")
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
            print("normal")
            #expathlist = [["data001","data002","data007"],["data003","data004","data008"],["data005","data006","data010"]]

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
          
        if experience_flag:
            self.exnumber = 30
            female20_flag = False
            for name, personality, attribute in zip(names,personalities,attributes):
                gender = attribute[0]
                age = attribute[1]
                # self.system_prompt += f"{name}の性別は{gender}，年齢は{age}代です"
                self.system_prompt += f"{name}の年齢は{age}代です"
                self.system_prompt += f"{name}は以下のような経験をしたことがあります.\n"
                expathlist = glob.glob(os.path.join("experience","meidai","a_sampling",gender,age,"*"))
                
                if gender == "female" and age == "20":
                    if female20_flag:
                        expathlist = expathlist[50:]
                    female20_flag = True
                    
                file_number = len(expathlist)
                display_flag = False
                for i in range(self.exnumber):
                    try:
                        ex_file = expathlist.pop(0)
                    except IndexError as e:
                        if not display_flag:
                            print(f"{name}:There are only {file_number} files for {gender} {age}s")
                            display_flag = True
                        continue
                    
                    with open(ex_file,"r",encoding="utf-8") as f:
                        ex = f.read()
                    ex_text = self.namechange(ex_file, ex, name)
                    ex_lines = ex_text.splitlines()
                    ex_lines = ex_lines[2:-1]
                    self.system_prompt += "\n".join(ex_lines)
                    
                self.system_prompt += f"この{name}の経験を踏まえて会話文を出力してください.\n"
                                
        with open(self.logfile,'a',encoding="utf-8") as f:
            f.write(f"各エージェントに与えた経験ファイル数: {self.exnumber}")        
        
            
        self.system_prompt += f'{",".join(names)}はグループで会話を始めるところです．'
        self.system_prompt += "全員短めに自己紹介をしましょう"
        self.system_prompt += "最後にユーザーの名前を聞いてください"
        self.system_prompt += "ユーザーのことはあなたと呼んでください"
        
        
        # self.system_prompt += f'{",".join(names)}の会話文はなるべく1回ずつ出力してください.'
        # # self.system_prompt += "まずは短く自己紹介してください"
        # self.system_prompt += "出力の最後にユーザーの名前を呼びながら発話を促すようにしてください"
        # self.system_prompt += "ユーザーの名前が分からないときは名前を聞いてください"
    
    def namechange(self,path,text,name):
        file_name = os.path.basename(path)
        ori_name_match = re.match(r"^\w+_(\w+)\.txt$",file_name)
        if ori_name_match:
            ori_name = ori_name_match.group(1)
        else:
            print("failed replace name")
            return text
        re_text = text.replace(ori_name,name)
        return re_text
    
    def writelog(self,val):
        if val['role'] == 'user':
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f'\n[{self.username}] {val["content"]}\n')
        else:
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(val['content'])

    def initial_chat(self, user_message):
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
        with self.client.messages.stream(
            model = self.model,
            system = self.system_prompt,
            messages = self.messages,
            max_tokens = 2000,
        ) as stream:
            response_content = ""
            name = ""
            emot = ""
            talk = []
            mode = 0
            self.q_speech.put(["*chatstart*","*signal*"]) 
            
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
            # self.q_speech.put([name,f"{self.username}さんはどう思いますか？"])
            self.q_speech.put(["*chatend*","*signal*"]) #出力が終わったら[0]に*chatend*,[1]に*signal*をput
            print("")
            self.messages.append({"role": "assistant", "content": response_content})
            self.writelog({"role": "assistant", "content": response_content})

        self.nconv += 1

        return response_content
    
if __name__ == "__main__":
    text = "沖田です"
    user,reason = intro_chat.extract_claude(text)
    print(user)
    print(reason)