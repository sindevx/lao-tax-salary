FROM nginx:stable-alpine

# คัดลอกไฟล์ทั้งหมดในโปรเจกต์ไปไว้ที่ root ของเว็บ
# ถ้าคุณมีโฟลเดอร์ build/dist อื่น ให้เปลี่ยน path นี้ภายหลัง
COPY . /usr/share/nginx/html

EXPOSE 80
