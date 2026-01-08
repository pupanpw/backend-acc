CREATE OR REPLACE FUNCTION update_period_summary()
RETURNS TRIGGER AS $$
BEGIN
    WITH sums AS (
        SELECT
            SUM(CASE WHEN type='income' THEN amount ELSE 0 END) AS income_sum,
            SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS expense_sum
        FROM transactions
        WHERE user_id_line = NEW.user_id_line
          AND DATE(created_at) = DATE(NEW.created_at)
    )
    INSERT INTO period_summary(summary_date, user_id_line, total_income, total_expense, total_balance, created_at, updated_at)
    VALUES (
        DATE(NEW.created_at),
        NEW.user_id_line,
        (SELECT income_sum FROM sums),
        (SELECT expense_sum FROM sums),
        (SELECT income_sum - expense_sum FROM sums),
        NOW(),
        NOW()
    )
    ON CONFLICT (summary_date, user_id_line)
    DO UPDATE SET
        total_income = EXCLUDED.total_income,
        total_expense = EXCLUDED.total_expense,
        total_balance = EXCLUDED.total_balance,
        updated_at = NOW();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
