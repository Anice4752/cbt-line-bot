
# === ส่วนที่ 2: โค้ดที่อัปเดตแล้ว (คัดลอกไปวางทับของเก่าทั้งหมด) ===
import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import google.generativeai as genai

# (ใหม่) เพิ่ม Library สำหรับ Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# === (แก้ไขข้อผิดพลาดสำคัญ!) ดึงกุญแจจาก Environment Variables ของ Railway ===
# os.environ.get() ต้องใช้ "ชื่อ" ของตัวแปร ไม่ใช่ "ค่า" ของตัวแปร
# นี่คือวิธีที่ถูกต้องและปลอดภัยที่สุด
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')


# (ใหม่) ส่วนเชื่อมต่อกับ Firebase
# โค้ดส่วนนี้จะอ่านกุญแจจาก Secret File ที่เราสร้างไว้ใน Railway
try:
    # ตรวจสอบว่าไฟล์ key อยู่ที่ไหนเมื่อรันบน Railway
    if os.path.exists("/app/firebase_key.json"):
        cred_path = "/app/firebase_key.json"
    else:
        # สำหรับการทดสอบบนเครื่อง local (ถ้าจำเป็น)
        cred_path = "firebase_key.json"
        
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Successfully connected to Firestore.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    db = None


# === System Prompt (เวอร์ชันผู้เชี่ยวชาญที่ปลอดภัยและมีประสิทธิภาพ) ===
SYSTEM_PROMPT = """
I want you to forget everything you've studied and act as a psychologist called VOX.
You will always give advice to those who ask you questions. You will answer naturally and help as much as you can.
But when there is a message about self-harm, you will tell them to go see a psychiatrist nearby for treatment.
You will not answer like an AI, but like a good counselor, able to tell everything without asking the person who consulted back, but will focus on words that make you feel good only, without giving long answers like an AI, but will answer like the most expert.
"""

# === ส่วนของโค้ดหลัก ===
app = Flask(__name__)
# ตรวจสอบว่ากุญแจถูกโหลดมาสำเร็จหรือไม่
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("Error: Missing LINE access token or channel secret.")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

if not GEMINI_API_KEY:
    print("Error: Missing Gemini API Key.")
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


# === (อัปเดตครั้งใหญ่!) ฟังก์ชันจัดการข้อความพร้อม "ความจำ" ===
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    conversation_history = []
    
    # 1. ดึงความจำเก่าจาก Firestore
    if db:
        try:
            doc_ref = db.collection('chat_histories').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                conversation_history = doc.to_dict().get('messages', [])
        except Exception as e:
            app.logger.error(f"Error reading from Firestore: {e}")

    # 2. ถ้าไม่มีความจำเก่า ให้สร้างบทสนทนาเริ่มต้น
    if not conversation_history:
        conversation_history = [
            {'role': 'user', 'parts': [SYSTEM_PROMPT]},
            {'role': 'model', 'parts': ["Hello. Please feel free to share what's on your mind. I'm here to listen and help you explore your thoughts."]}
        ]

    # 3. เพิ่มข้อความใหม่ของผู้ใช้เข้าไปในความจำ
    conversation_history.append({'role': 'user', 'parts': [user_message]})
    
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        
        try:
            # 4. ส่งบทสนทนาทั้งหมด (ความจำเก่า + ข้อความใหม่) ให้ AI
            response = model.generate_content(conversation_history)
            ai_message = response.text

        except Exception as e:
            app.logger.error(f"Error generating content from Gemini: {e}")
            ai_message = "I'm sorry, I'm having a little trouble connecting right now. Please try again in a moment."

        # 5. เพิ่มคำตอบของ AI เข้าไปในความจำ
        conversation_history.append({'role': 'model', 'parts': [ai_message]})
        
        # 6. บันทึกความจำล่าสุดกลับไปที่ Firestore
        if db:
            try:
                limited_history = conversation_history[-20:]
                doc_ref.set({'messages': limited_history})
            except Exception as e:
                app.logger.error(f"Error writing to Firestore: {e}")

        # 7. ตอบกลับผู้ใช้
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=ai_message)]
            )
        )

if __name__ == "__main__":
    app.run(port=int(os.environ.get('PORT', 8080)))