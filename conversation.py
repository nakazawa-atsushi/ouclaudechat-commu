import dotenv
import os
import glob
import time
import sys
from anthropic import Anthropic
import random
import base64
import datetime
import argparse
import threading
import socket
from commu_claude_chat import CommuClaudeChat
from play_voicebox import play_voicebox

dotenv.load_dotenv()
 

if __name__ == "__main__":

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task")     # タスク
    parser.add_argument('-f', "--img_file")
    parser.add_argument('-v', '--voice',action='store_true',default=False,
                        help="指定したらvoicevoxを使用する(フラグ)")
    args = parser.parse_args()
    # print(args.task, args.img_file)

    print(args)

    if args.task is None:
        print("specify task by option -t [art|art_view|normal] -f image_file")
        sys.exit(0)

    # setup claude
    adapter = CommuClaudeChat()
    audio = play_voicebox()

    if args.task == "art":
        # art_conv: アートについて語る　モードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art", names, personalities)
    elif args.task == "art_view":
        # art_view_conv: 示された画像について語るモードの場合
        names = ['まさる','きよこ','たかし']
        personalities = ['アートの初心者','アートの初心者','アートの中級者']
        adapter.set_task("art_view", names, personalities, args.img_file)
    elif args.task == "normal":
        names = ['まさる','きよこ','たかし']
        personalities = ['average','selfcenter','average']
        adapter.set_task("normal", names, personalities)
    else:
        print("wrong task name.")
        sys.exit(0)

    # -vフラグが経てばvoice start
    if args.voice:
        print("voice start")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1",50021))
            s.close()
            print("通信成功")
            threading.Thread(target=audio.monitor, args=(adapter.q_speech,), daemon=True).start()
        except socket.error as e:
            print("エラー発生:",e)
            print("voicevoxを起動してください")
            print("音声出力無しで実行します")
            s.close()

    while True:
        user_input = input("message: ")
        if user_input.lower() == "quit":
            break

        res = adapter.create_chat(user_input)
        if adapter.streaming == False:
            print(f"{res}")