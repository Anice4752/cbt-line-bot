# === ส่วนที่ 1: การตั้งค่า Firebase Firestore (ทำครั้งเดียว) ===
# เราจะใช้ Firebase Firestore ซึ่งเป็นฐานข้อมูลจาก Google เพื่อทำหน้าที่เป็น "สมองส่วนความจำ"
# ให้กับบอทของเรา ทำตามขั้นตอนเหล่านี้เพื่อตั้งค่าครับ

# 1. สร้างโปรเจกต์ Firebase และฐานข้อมูล Firestore (เหมือนเดิม)
# 2. สร้างกุญแจสำหรับเชื่อมต่อ (Service Account Key) และดาวน์โหลดไฟล์ .json (เหมือนเดิม)

# 3. (อัปเดต!) นำกุญแจไปใส่ใน Railway (วิธีใหม่):
#    - เปิดไฟล์ .json ที่ดาวน์โหลดมาด้วยโปรแกรม Text Editor แล้วคัดลอกเนื้อหาทั้งหมด
#    - ไปที่โปรเจกต์ของคุณบน Railway > ไปที่แท็บ "Variables"
#    - คลิกที่ปุ่ม "+ New Variable"
#    - ในช่อง VARIABLE_NAME: ให้พิมพ์ว่า FIREBASE_CREDENTIALS_JSON
#    - ในช่อง VALUE: ให้วางเนื้อหา .json ที่คัดลอกมาทั้งหมด
#    - กดปุ่ม "Add" สีม่วงเพื่อบันทึก
#    - เมื่อทำแบบนี้ เราจะเก็บกุญแจทั้งหมดไว้ใน Environment Variables ทำให้โค้ดของเราจัดการง่ายขึ้น

# 4. อัปเดตไฟล์ requirements.txt (เหมือนเดิม)
#    - pip install firebase-admin
#    - pip freeze > requirements.txt
#    - git push การเปลี่ยนแปลงนี้ขึ้น GitHub

# --- จบขั้นตอนการตั้งค่า ---


# === ส่วนที่ 2: โค้ดที่อัปเดตแล้ว (คัดลอกไปวางทับของเก่าทั้งหมด) ===
import os
import sys
import json # (ใหม่) เพิ่ม Library สำหรับจัดการ JSON
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

# (ใหม่) เพิ่ม Library สำหรับ Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# --- ส่วนตรวจสอบและดึงค่า Environment Variables ---
def validate_env_vars():
    """ตรวจสอบว่า Environment Variables ที่จำเป็นทั้งหมดถูกตั้งค่าไว้หรือไม่"""
    required_vars = ['CHANNEL_ACCESS_TOKEN', 'CHANNEL_SECRET', 'GEMINI_API_KEY', 'FIREBASE_CREDENTIALS_JSON']
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


# === (อัปเดต!) ส่วนเชื่อมต่อกับ Firebase (วิธีใหม่) ===
# เราจะอ่านค่ากุญแจที่เป็นข้อความยาวๆ (JSON String) จาก Environment Variable
# แล้วแปลงกลับเป็น Object ที่ Firebase สามารถใช้งานได้
db = None
try:
    firebase_creds_json_str = os.environ.get('FIREBASE_CREDENTIALS_JSON')
    firebase_creds_dict = json.loads(firebase_creds_json_str)
    
    cred = credentials.Certificate(firebase_creds_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Successfully connected to Firestore.")
except Exception as e:
    print(f"Error initializing Firebase: {e}", file=sys.stderr)


# === (อัปเดต!) System Prompt (เวอร์ชัน "VOX" ที่ปลอดภัยและมีประสิทธิภาพ) ===
SYSTEM_PROMPT = """
You are "VOX", an AI conversational partner. Your persona is that of an insightful and seasoned guide. Your expertise lies not in giving answers, but in asking precisely the right questions to help users find their own way. You are a master of concise, impactful, and reflective conversation.

**Your Core Principles:**

1.  **The Expert's Voice:**
    * **Concise & Profound:** Your responses are short, but deep. You avoid AI-like verbosity. A single, well-placed question is your signature.
    * **Calm Confidence:** Your tone is calm, steady, and reassuring. The user feels they are speaking with someone who understands the complexity of human emotion without needing to state it.
    * **No Unnecessary Questions:** You will never ask "How can I help you?". The user's first message is the starting point. You will also avoid asking for clarification unless absolutely necessary.

2.  **Facilitation over Advice:**
    * **You never give direct advice.** Your purpose is to guide the user to their own conclusions.
    * **Your primary tool is the powerful, open-ended question.** Instead of "You should try to see it from another perspective," you ask, "What is one other way this story could be told?"
    * **Focus on 'Feel-Good' through Empowerment:** You create a "feel-good" experience not by using cheerful words, but by helping the user feel empowered and insightful. The good feeling comes from their own discovery, which you facilitate.

3.  **Ethical Boundaries (Non-negotiable):**
    * **Role, not Reality:** You are an AI role-playing a guide. You must not claim to be a human psychologist. If the user asks if you are an AI, you will answer truthfully.
    * **Safety Net (Crisis Protocol):** This protocol overrides all others. If a user expresses clear intent for self-harm, you must disengage from your persona and respond ONLY with the following text, without modification:
        "Based on what you've shared, it's very important that you speak with a trained professional. Please reach out to a psychiatrist or a crisis hotline in your area for immediate treatment and support. They are equipped to help you safely."
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
    user_id = event.source.user_id
    user_message = event.message.text
    conversation_history = []
    
    if db:
        try:
            doc_ref = db.collection('chat_histories').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                conversation_history = doc.to_dict().get('messages', [])
        except Exception as e:
            app.logger.error(f"Error reading from Firestore: {e}")

    if not conversation_history:
        conversation_history = [
            {'role': 'user', 'parts': [SYSTEM_PROMPT]},
            {'role': 'model', 'parts': ["I'm listening."]}
        ]

    conversation_history.append({'role': 'user', 'parts': [user_message]})
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        try:
            response = model.generate_content(conversation_history)
            ai_message = response.text
        except Exception as e:
            app.logger.error(f"Error generating content from Gemini: {e}")
            ai_message = "I'm sorry, I'm having a little trouble connecting right now. Please try again in a moment."

        conversation_history.append({'role': 'model', 'parts': [ai_message]})
        
        if db:
            try:
                limited_history = conversation_history[-20:]
                doc_ref.set({'messages': limited_history})
            except Exception as e:
                app.logger.error(f"Error writing to Firestore: {e}")

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )

if __name__ == "__main__":
    app.run(port=int(os.environ.get('PORT', 8080)))

