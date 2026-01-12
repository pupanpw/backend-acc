-- สร้าง function ใหม่
CREATE OR REPLACE FUNCTION public.update_period_summary()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    income_sum numeric;
    expense_sum numeric;
BEGIN
    -- คำนวณผลรวมของ user และวันที่เดียวกับ transaction ใหม่
    SELECT
        COALESCE(SUM(CASE WHEN type='income' THEN amount END),0),
        COALESCE(SUM(CASE WHEN type='expense' THEN amount END),0)
    INTO income_sum, expense_sum
    FROM transactions
    WHERE user_id_line = NEW.user_id_line
      AND DATE(created_at) = DATE(NEW.created_at);

    -- Insert หรือ Update record ใน period_summary
    INSERT INTO period_summary (
        summary_date,
        user_id_line,
        total_income,
        total_expense,
        total_balance,
        created_at,
        updated_at
    )
    VALUES (
        DATE(NEW.created_at),
        NEW.user_id_line,
        income_sum,
        expense_sum,
        income_sum - expense_sum,
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
$function$;

-- สร้าง trigger
DROP TRIGGER IF EXISTS trg_update_period_summary ON transactions;

CREATE TRIGGER trg_update_period_summary
AFTER INSERT OR UPDATE ON transactions
FOR EACH ROW
EXECUTE FUNCTION public.update_period_summary();