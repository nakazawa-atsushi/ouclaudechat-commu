import threading
from anthropic import Anthropic
from commu_claude_chat import CommuClaudeChat
from play_voicebox import play_voicebox
from local_whisper_mic import WhisperMic

client = Anthropic()

def tool():
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

def extract_claude(text):
    tools = tool()
    res = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        tools=tools,
        messages=[{"role":"user","content":text}]
    )
    print(res)
    if not res.stop_reason == "tool_use":
        return "", res.stop_reason

    return res.content[1].input["speaker_name"], res.stop_reason


if __name__ == "__main__":
    text = "沖田です"
    user,reason = extract_claude(text)
    print(user)
    print(reason)