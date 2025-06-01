import os
import json
from flask import Flask, request
import requests
import openai

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# 获取记忆文件路径
def get_memory_file(chat_id):
    return f"memory_{chat_id}.json"

# 读取记忆
def load_memory(chat_id):
    filename = get_memory_file(chat_id)
    if not os.path.exists(filename):
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

# 保存记忆
def save_memory(chat_id, memory):
    filename = get_memory_file(chat_id)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(memory[-20:], f, ensure_ascii=False, indent=2)

# 添加一条对话记录
def add_message(chat_id, role, content):
    memory = load_memory(chat_id)
    memory.append({"role": role, "content": content})
    save_memory(chat_id, memory)

# 与 OpenAI 对话
def get_chatgpt_reply(chat_id, user_input):
    memory = load_memory(chat_id)
    add_message(chat_id, "user", user_input)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory
    )
    reply = response.choices[0].message["content"]
    add_message(chat_id, "assistant", reply)
    return reply

# Telegram webhook 接口
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        user_text = data['message']['text']

        reply = get_chatgpt_reply(chat_id, user_text)

        requests.post(TELEGRAM_API_URL, json={
            "chat_id": chat_id,
            "text": reply
        })

    return "ok"

# 根目录健康检测
@app.route('/')
def home():
    return "星辰已上线 ✨"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
