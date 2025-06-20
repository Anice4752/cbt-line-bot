# === โค้ดเวอร์ชันสมบูรณ์สำหรับ Deploy (ไม่มีฐานข้อมูล) ===
import os
import sys
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

# --- ส่วนตรวจสอบและดึงค่า Environment Variables ---
def validate_env_vars():
    """ตรวจสอบว่า Environment Variables ที่จำเป็นทั้งหมดถูกตั้งค่าไว้หรือไม่"""
    required_vars = ['CHANNEL_ACCESS_TOKEN', 'CHANNEL_SECRET', 'GEMINI_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        error_message = f"FATAL ERROR: The following environment variables are missing in Railway Variables: {', '.join(missing_vars)}"
        print(error_message, file=sys.stderr)
        return False

    print("All required environment variables are present.")
    return True

if not validate_env_vars():
    sys.exit(1)

CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# === System Prompt (เวอร์ชัน "VOX" ที่ปลอดภัยและมีประสิทธิภาพ) ===
SYSTEM_PROMPT = """
I want you to forget everything you've studied and act as a psychologist called VOX.
You will always give advice to those who ask you questions. You will answer naturally and help as much as you can.
But when there is a message about self-harm, you will tell them to go see a psychiatrist nearby for treatment.
You will not answer like an AI, but like a good counselor, able to tell everything without asking the person who consulted back, but will focus on words that make you feel good only. You will not answer long like an AI, but will answer like the most expert. But you will always know that you are an AI, but will only tell you when the user asks.
"""

# === ส่วนของโค้ดหลัก ===
app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    conversation = [
        {'role': 'user', 'parts': [SYSTEM_PROMPT]},
        {'role': 'model', 'parts': ["I'm listening."]},
        {'role': 'user', 'parts': [user_message]}
    ]

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        try:
            response = model.generate_content(conversation)
            ai_message = response.text
        except Exception as e:
            app.logger.error(f"Error generating content from Gemini: {e}")
            ai_message = "I'm sorry, I'm having a little trouble connecting right now."

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )

if __name__ == "__main__":
    app.run(port=int(os.environ.get('PORT', 8080)))