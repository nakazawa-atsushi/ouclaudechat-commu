import re
from anthropic import Anthropic
import os
import glob

# ChatGPT APIのセットアップ

# テキストファイルの読み込み
def read_text_file(file_path):
    print("read text")
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def all_read(path):
    path_list = glob.glob(path + '\*')
    path_list2 = []
    for i in range(len(path_list)):
        path_list2.append(path_list[i].replace("\\", "/"))
    return path_list2

# 参加者ごとの発言を抽出
def extract_participant_data(text):
    print("extract_participant_data")
    participant_dict = {}
    lines = text.splitlines()
    
    current_participant = None
    for line in lines:
        # 参加者IDの行を探す
        match = re.match(r'＠参加者(\w+)', line)
        match2 = re.match(r'(.*?)：(.*)', line)
        if match:
            if match.group(1) == "の関係":
                print("の関係なのでcontinue")
                continue
            participants = match.group(1)
            participant_dict[participants] = []
        if match2 and match2.group(1) in list(participant_dict):
            current_participant = match2.group(1)
            # print(current_participant)
            participant_dict[current_participant].append(line.strip())
        
        """
        elif current_participant:
            # 現在の参加者の発言を追加
            participant_dict[current_participant].append(line.strip())
        """

    print(participant_dict.keys())
    print(type(participant_dict.keys()))
    print(list(participant_dict))
    print(type(list(participant_dict)))
    # print(f"key:{participant_dict['F128']}")
    return participant_dict

# ChatGPTに発言を送信し、体験を抽出
def extract_experiences(text):
    print("client")
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",  # モデルを選択
        system="以下の発言から個人の体験やエピソードを抜き出してください。",
        messages=[
            {"role": "user", "content": text}
        ],
        max_tokens=500
    )
    # print(response)
    return response.content[0].text.strip()

# メイン処理
def main():
    # テキストファイルのパス
    path = "experience/meidai/original"
    data = "data023"
    path2 = path.replace("\\", "/")
    path3 = path.replace("original", "sampling")
    
    # テキスト読み込み
    # text = read_text_file(f"{path2}/{data}.txt")
    file_list = all_read(path2)
    
    for i in range(len(file_list)):
        sampling_path = file_list[i].replace("original", "sampling")
        text = read_text_file(file_list[i])


        # 参加者ごとの発言抽出
        participant_data = extract_participant_data(text)
        
        # 各参加者の体験抽出
        print("Processing participant data")
        for participant_id, statements in participant_data.items():
            full_text = "\n".join(statements)
            
            if not full_text.strip():  # 空のテキストをチェック
                print(f"Participant {participant_id} has no valid content.")
                continue  # 空のテキストの場合はスキップ

            ex_text = extract_experiences(full_text)  # 体験を抽出
            # print(write_text)

            write_text = ex_text.replace(participant_id,"[name]")
            
            # 出力ファイルに書き込み
            with open(f"{sampling_path}_{participant_id}.txt", "w", encoding="utf-8") as f:
                f.write(write_text)
        
        print(f"{file_list[i]} : Processing complete.")


if __name__ == "__main__":
    main()
