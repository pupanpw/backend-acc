1. User Flow

LINE App
│
▼
Rich Menu → LIFF Web App
│
▼
เปิดหน้าเว็บฟอร์มกรอกข้อมูล
│
├─ เลือกประเภท: Income / Expense
├─ ใส่จำนวนเงิน
├─ ใส่หัวข้อ/รายละเอียด
├─ วันที่: auto = วันนี้ (ไม่สามารถแก้ไขได้)
│
▼
กด "บันทึก"
│
▼
ข้อมูลส่งไป Backend API
│
▼
Backend → transactions table (บันทึกรายการ)
│
▼
Backend ส่ง Response → LIFF แสดง "บันทึกสำเร็จ "

2. Daily Summary Job Flow (ตัดยอด 23:00)

Cron Job / Scheduled Job: 23:00 ทุกวัน
│
▼
Backend Query transactions table
├─ WHERE created_at::date = วันนี้
│
▼
คำนวณยอดรวม
├─ total_income = SUM(amount WHERE type='income' AND status='active')
└─ total_expense = SUM(amount WHERE type='expense' AND status='active')
│
▼
Insert/Update daily_summary table
├─ summary_date = วันนี้
├─ total_income = ผลรวมที่คำนวณได้
└─ total_expense = ผลรวมที่คำนวณได้
│
▼
JobComplete → Log success
