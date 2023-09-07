# キャラ付けChatBot(Slack)
SecHackのナイトチャレンジで作成しました。
![image](https://github.com/mofunyanko/chat-character-bot/assets/95011869/ea432ab0-2765-4fd2-9ab4-012b6c0c22ad)

## 設定の仕方
1. Slackでbotを作成し、権限を付与する
2. OpenAPIを登録する
3. ```.env```ファイルを直下に作成する
4. ```.env```ファイルにキーを入力する
    - ```OPENAI_API_KEY```
    - ```SLACK_BOT_TOKEN```
5. Slackのワークスペースにカスタムコマンドを登録する
    - ```/slack/setpersona``` → ペルソナを設定する
    - ```/slack/updatepersona``` → ペルソナを更新する
    - ```/slack/usepersona``` → ペルソナを使う
