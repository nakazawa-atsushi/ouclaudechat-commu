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
from commu_claude_chat import CommuClaudeChat

dotenv.load_dotenv()

# test of threading
# queueを監視するスレッド
def monitor(x):
    print("Thread start")
    print(x)
    print(x.empty())
    while(True):
        if x.empty() == True:
            time.sleep(0.01)
        else:
            val = x.get()
            print("value = ", val)

if __name__ == "__main__":

    # コマンドライン引数を解釈する
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', "--task")     # タスク
    parser.add_argument('-f', "--img_file")
    args = parser.parse_args()
    # print(args.task, args.img_file)

    print(args)

    if args.task is None:
        print("specify task by option -t [art|art_view|normal] -f image_file")
        sys.exit(0)

    # setup claude
    adapter = CommuClaudeChat()

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

    # begin thread
    # threading.Thread(target=monitor, args=(adapter.q_speech,), daemon=True).start()

    while True:
        user_input = input("message: ")
        if user_input.lower() == "quit":
            break

        res = adapter.create_chat(user_input)
        if adapter.streaming == False:
            print(f"{res}")