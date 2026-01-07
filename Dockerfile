FROM python:3.13-slim

# ตั้ง working directory
WORKDIR /app

# คัดลอกไฟล์ requirements
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# รัน uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
