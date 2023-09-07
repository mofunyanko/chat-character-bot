# fastapiの方
import os
import openai
import uvicorn
import requests
from fastapi import FastAPI, BackgroundTasks, Form, Response
from pydantic import BaseModel
from dotenv import load_dotenv
from slack_sdk import WebClient

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

app = FastAPI()

user_personas = dict()

class SlackEvent(BaseModel):
    type: str = None
    challenge: str = None

class PersonaData(BaseModel):
  channel_id: str
  user_id: str
  text: str

class SlackCommandForm(BaseModel):
  channel_id: str
  user_id: str
  text: str
  response_url: str

def set_user_persona(user_id, persona_name):
  user_personas[user_id] = persona_name

def get_user_persona(user_id):
  return user_personas.get(user_id, None)

def update_user_persona(user_id, new_persona):
  if user_id in user_personas:
    user_personas[user_id] = new_persona
    return True
  else:
    return False

@app.post("/slack/events")
async def slack_event(item: SlackEvent):
  if item.type == 'url_verification':
    return {"challenge": item.challenge}

@app.post("/slack/setpersona")
async def slack_setpersona(channel_id: str = Form(...), user_id: str = Form(...), text: str = Form(...)):
  set_user_persona(user_id, text)
  client.chat_postMessage(channel=channel_id, text=f"キャラを{text}に設定しました。")
  return Response(status_code=200)

@app.post("/slack/updatepersona")
async def slack_updatepersona(channel_id: str = Form(...), user_id: str = Form(...), text: str = Form(...)):
  success = update_user_persona(user_id, text)
  if success:
    client.chat_postMessage(channel=channel_id, text=f"キャラを{text}に更新しました。")
    return Response(status_code=200)
  else:
    return {"text": "キャラを設定していません。/setpersona コマンドを使用してキャラを設定してください。"}

async def process_usepersona(command: SlackCommandForm):
  persona_description = get_user_persona(command.user_id)
  if persona_description is None:
    requests.post(command.response_url, json={"text": "キャラが指定されていません。/setpersona コマンドを使用してキャラを設定してください。"})
  else:
    response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": f"あなたは入力された情報を{persona_description}風に言い換えてください。 "},
        {"role": "user", "content": command.text},
      ]
    )
    bot_response = response['choices'][0]['message']['content']
    client.chat_postMessage(channel=command.channel_id, text=bot_response)

@app.post("/slack/usepersona")
async def slack_usepersona(background_tasks: BackgroundTasks, channel_id: str = Form(...), user_id: str = Form(...), text: str = Form(...), response_url: str = Form(...)):
  command = SlackCommandForm(channel_id=channel_id, user_id=user_id, text=text, response_url=response_url)
  background_tasks.add_task(process_usepersona, command)
  return Response(status_code=200)

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=3000)
