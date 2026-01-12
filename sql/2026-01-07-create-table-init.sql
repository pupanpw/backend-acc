CREATE TABLE users
(
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100),
    picture_url TEXT,
    role VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE transactions
(
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255),
    amount DECIMAL(10, 2),
    type VARCHAR(10) CHECK (type IN ('income', 'expense')),
    status VARCHAR(10) DEFAULT 'active',
    user_id UUID REFERENCES users(user_id),
    source VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE daily_summary
(
    id BIGSERIAL PRIMARY KEY,
    summary_date DATE UNIQUE,
    total_income INTEGER DEFAULT 0,
    total_expense INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(created_at);


ALTER TABLE users ADD COLUMN user_id_line varchar;


-- ลบคอลัมน์ user_id เดิม
ALTER TABLE transactions DROP COLUMN IF EXISTS user_id;

-- เพิ่มคอลัมน์ user_id_line (ถ้ายังไม่มี)
ALTER TABLE transactions ADD COLUMN
IF NOT EXISTS user_id_line VARCHAR
(255) NOT NULL;

-- ตรวจสอบว่า index ใช้ user_id_line แทน
CREATE INDEX
IF NOT EXISTS idx_transactions_user_line ON transactions
(user_id_line);


ALTER TABLE daily_summary
ADD COLUMN user_id_line VARCHAR NOT NULL;

-- กำหนด unique constraint
ALTER TABLE daily_summary
ADD CONSTRAINT uq_daily_summary UNIQUE(summary_date, user_id_line);


ALTER TABLE daily_summary
ADD COLUMN total_balance NUMERIC DEFAULT 0;



ALTER TABLE daily_summary
ALTER COLUMN total_income TYPE NUMERIC(12,2),
ALTER COLUMN total_expense TYPE NUMERIC(12,2),
ALTER COLUMN total_balance TYPE NUMERIC(12,2);


ALTER TABLE users
ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();

ALTER TABLE daily_summary
ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();


ALTER TABLE public.daily_summary RENAME TO period_summary;


CREATE INDEX idx_daily_summary_user_date
ON period_summary (user_id_line, summary_date);


ALTER TABLE period_summary DROP CONSTRAINT IF EXISTS daily_summary_summary_date_key;
ALTER TABLE period_summary
ADD CONSTRAINT unique_summary_user UNIQUE (summary_date, user_id_line);

ALTER TABLE transactions ADD COLUMN  transaction_at TIMESTAMP;

UPDATE transactions
SET transaction_at = created_at
WHERE transaction_at IS NULL;

CREATE INDEX idx_transactions_user_transaction_at
ON transactions (user_id_line, transaction_at);
