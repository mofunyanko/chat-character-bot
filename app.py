import os
import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from collections import defaultdict

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# ユーザーごとのペルソナを保持する辞書
user_personas = defaultdict(dict)


def set_user_persona(user_id, persona_name):
    # ペルソナを辞書に保存する
    user_personas[user_id] = persona_name

def get_user_persona(user_id):
    # 辞書からユーザーのペルソナを取得する
    return user_personas.get(user_id, None)

def update_user_persona(user_id, new_persona):
    # 辞書からユーザーのペルソナを更新する
    user_personas[user_id] = new_persona


@app.route("/slack/events", methods=["POST"])
def slack_event():
    payload = request.json

    # URL認証の処理
    if payload.get('type') == 'url_verification':
        return jsonify({'challenge': payload.get('challenge')})


@app.route("/slack/setpersona", methods=["POST"])
def slack_setpersona():
    channel_id = request.form.get('channel_id')
    user_id = request.form.get('user_id')
    persona_name = request.form.get('text')

    # /setpersona persona で設定する
    set_user_persona(user_id, persona_name)
    client.chat_postMessage(channel=channel_id, text=f"ペルソナ'{persona_name}'が設定されました。")
    return jsonify({"status": "ok"})


@app.route("/slack/updatepersona", methods=["POST"])
def slack_updatepersona():
    channel_id = request.form.get('channel_id')
    user_id = request.form.get('user_id')
    new_persona = request.form.get('text')

    # /updatepersona new_persona で設定する
    try:
        update_user_persona(user_id, new_persona)
        client.chat_postMessage(channel=channel_id, text=f"ペルソナ'{new_persona}'に更新されました。")
    except ValueError:
        client.chat_postMessage(channel=channel_id, text="コマンドの形式が異なります。 /updatepersona new_persona という形式で入力してください。")

    return jsonify({"status": "ok"})


@app.route("/slack/usepersona", methods=["POST"])
def slack_usepersona():
    channel_id = request.form.get('channel_id')
    user_id = request.form.get('user_id')
    message_text = request.form.get('text')
    persona_description = get_user_persona(user_id)
    if persona_description is None:
        client.chat_postMessage(channel_id, text="ペルソナが指定されていません。/setpersona コマンドを使用してペルソナを設定してください。")
        return jsonify({"status": "ok"})
    else:
        # OpenAI Chat API integration
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a {persona_description}. You should respond to the user's message in a way that reflects this character. And your responses should be in Japanese."},
                {"role": "user", "content": message_text},
            ]
        )
        bot_response = response['choices'][0]['message']['content']
        try:
            client.chat_postMessage(channel=channel_id, text=bot_response)
        except SlackApiError as e:
            client.chat_postMessage(channel=channel_id, text=f"Error sending message: {e}")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=3000)
