# ใช้พิมพ์เขียวของ Python เวอร์ชัน 3.10 เป็นฐาน
FROM python:3.10-slim

# ตั้งค่าโฟลเดอร์ทำงานภายในบ้านของบอท
WORKDIR /app

# คัดลอกรายการชิ้นส่วน (requirements.txt) เข้าไปก่อน
COPY requirements.txt requirements.txt

# ติดตั้งชิ้นส่วนทั้งหมดที่จำเป็น
RUN pip install -r requirements.txt

# คัดลอกโค้ดทั้งหมดของเราเข้าไปในบ้าน
COPY . .

# คำสั่งที่จะใช้รันบอทเมื่อบ้านสร้างเสร็จ (ให้ gunicorn รัน app จากไฟล์ app.py)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]