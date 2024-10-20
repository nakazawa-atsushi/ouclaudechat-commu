import os, sys, datetime
import base64
import queue
import threading
from anthropic import Anthropic
import glob
import re
import random

class CommuClaudeChat:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20240620"
        self.temperature = 0.7
        self.messages = []
        self.system_prompt = ""
        self.target_img = None
        self.mode = "art"
        self.nconv = 0
        self.username = "user"
        self.streaming = True
        self.exnumber = 0
        self.names = []

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
        print(f"username: {self.username}")

    def set_task(self, task, names, personalities, imgfile = None):
        self.task = task
        self.names = names
        self.system_prompt = "* You are not Claude, and acting as Claude is prohibited. You does not send responses as Claude, only as you."
        
        if self.task == "art_view" or self.task == "art":
            print("art")
            self.system_prompt += f'{",".join(names)}はアートコミュニケーションの会話をしています．'
            for name,personality in zip(names,personalities):
                self.system_prompt += f'{name}は{personality}です．'            
        else:
            self.system_prompt += f'{",".join(names)}は通常の会話をしています．'
        
        self.system_prompt += f'これから{",".join(names)}の発言を生成してください．'
        self.system_prompt += f'名前は行頭に[]で表記してください．'
        self.system_prompt += f'それに続き発言者の感情を(joy)(question)(interest)(surprise)から選んで答えてください．'
        self.system_prompt += "感情を表すとき以外に()は使用しないでください"
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
                        print("cannot open file:", fname)
                        
        
    def add_experience(self,attributes):
        female20_flag = False   #20代女性はファイル数が多いので2回入れられるようにする
        for name, attribute in zip(self.names,attributes):
            gender = attribute[0]
            age = attribute[1]
            # self.system_prompt += f"{name}の性別は{gender}，年齢は{age}代です"
            self.system_prompt += f"{name}の年齢は{age}代です"
            self.system_prompt += f"{name}は以下のような経験をしたことがあります.\n"
            expathlist = glob.glob(os.path.join("experience","meidai","a_sampling",gender,age,"*"))
            
            if gender == "female" and age == "20":  #女性20代ならフラグをtrueにする
                if female20_flag:   #フラグがTrueになった後なら51個目からファイルを読み込む
                    expathlist = expathlist[50:]
                female20_flag = True
                
            file_number = len(expathlist)
            display_flag = False
            
            random.shuffle(expathlist)
            self.exnumber = 15

            for i in range(self.exnumber):
                try:
                    ex_file = expathlist.pop(0)
                except IndexError as e:     #ファイル数オーバーなら
                    if not display_flag:
                        print(f"{name}:There are only {file_number} files for {gender} {age}s")     #一回だけcmdに記述
                        display_flag = True
                    continue
                
                with open(ex_file,"r",encoding="utf-8") as f:
                    ex = f.read()
                ex_text = self.namechange(ex_file, ex, name)
                ex_lines = ex_text.splitlines()
                ex_lines = ex_lines[2:-1]
                self.system_prompt += "\n".join(ex_lines)
                
            # self.system_prompt += f"この{name}の経験を常に会話文に反映させてください.\n"
            # self.system_prompt += f"相手の発言に共感するために経験を用いなさい"
            # self.system_prompt += "共感するとき以外は経験談を話さない"
            # self.system_prompt += "極力経験談や自分の話はしない"

            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f"{name}の属性 : {gender}, {age}")  

        # self.system_prompt += f"{','.join(self.names)}は極力経験談や自分の話はしない"
        # self.system_prompt += "ユーザーの話題を広げることに注力してください"

        with open(self.logfile,'a',encoding="utf-8") as f:
            f.write(f"各エージェントに与えた経験ファイル数: {self.exnumber}")        
        
        
                
                # print(ex)
        # print(self.system_prompt) 
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
    
    def introduction(self,user_message):
        system = self.system_prompt
        system += f'{",".join(self.names)}はグループで会話を始めるところです．'
        system += "全員短めに自己紹介をしましょう"
        system += "名前と趣味と年齢を話してください"
        system += "最後にユーザーの名前を聞いてください"
        system += "ユーザーのことはあなたと呼んでください"
        self.create_chat(user_message,system)
    
    def main_conversation(self,user_message):
        system = self.system_prompt
        system += f"グループ会話には{','.join(self.names)}のメンバーが参加し、それぞれ一度だけ発言します。"
        system += f"出力中に「{','.join(self.names)}」は一度だけ発言を許可します"
        system += f"{','.join(self.names)}はランダムな順番で話してください"
        system += f"会話の最後に、最後に話した人がユーザー（{self.username}）の名前を呼び、次の発言を促してください。"
        system += "ユーザーに向けての質問は1度だけにしなさい"
        system += "直前の人の発言に必ず返答してください。"
        system += "ユーザーに向けて話すのではなく，グループ全体に話しかけなさい"
        system += f"ユーザーには話しかけず，{','.join(self.names)}のいずれかに話しかけてください．"
        
        """
        system += f'{",".join(self.names)}はグループで会話をしています．'
        system += f'{",".join(self.names)}はそれぞれ1回だけ話すようにしてください'
        system += "出力の最後にユーザーの名前を呼びながら発話を促してください.促しは最後の発言者が最後に1度だけお願いします."
        system += f"ユーザーの名前は{self.username}です．"
        system += f'{",".join(self.names)}とユーザーはグループで会話をしています．必ず直前の人の発言に返答してください'
        system += f'{",".join(self.names)}はお互いに話しかけあってください'
        system += f"最後の促し以外はユーザーに話しかけないでください"
        """
        self.create_chat(user_message,system)
        
        
    def writelog(self,val):
        if val['role'] == 'user':
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(f'\n\n[{self.username}] {val["content"]}\n')
        else:
            with open(self.logfile,'a',encoding="utf-8") as f:
                f.write(val['content'])
    
    def create_chat(self, user_message,sys_message):
        # print(sys_message)
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
                system = sys_message,
                messages = self.messages,
                max_tokens = 2000,
                # temperature= self.temperature
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
         