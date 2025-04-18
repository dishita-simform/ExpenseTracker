CREATE OR REPLACE FUNCTION calculate_monthly_budget(
    user_id INTEGER,
    month INTEGER,
    year INTEGER
)
RETURNS TABLE (
    category_name VARCHAR,
    category_icon VARCHAR,
    category_color VARCHAR,
    total_spent NUMERIC,
    budget_limit NUMERIC,
    percentage_used NUMERIC,
    transaction_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.name::VARCHAR,
        c.icon::VARCHAR,
        c.color::VARCHAR,
        COALESCE(SUM(e.amount), 0)::NUMERIC AS total_spent,
        COALESCE(cb.amount, 0)::NUMERIC AS budget_limit,
        CASE 
            WHEN COALESCE(cb.amount, 0) > 0 THEN (COALESCE(SUM(e.amount), 0) / cb.amount * 100)::NUMERIC 
            ELSE 0::NUMERIC 
        END AS percentage_used,
        COUNT(e.id)::BIGINT AS transaction_count
    FROM budget_category c
    LEFT JOIN budget_categorybudget cb ON cb.category_id = c.id AND cb.user_id = $1
    LEFT JOIN budget_expense e ON e.category_id = c.id
        AND EXTRACT(MONTH FROM e.date) = $2
        AND EXTRACT(YEAR FROM e.date) = $3
        AND e.user_id = $1
    WHERE cb.user_id = $1
    GROUP BY c.id, c.name, c.icon, c.color, cb.amount;
END;
$$ LANGUAGE plpgsql;



CREATE OR REPLACE FUNCTION calculate_monthly_summary(
    in_user_id INTEGER,
    in_month INTEGER,
    in_year INTEGER
)
RETURNS TABLE (
    total_income NUMERIC,
    total_expenses NUMERIC,
    net_savings NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE((
            SELECT SUM(amount)
            FROM budget_income
            WHERE user_id = in_user_id
              AND EXTRACT(MONTH FROM date) = in_month
              AND EXTRACT(YEAR FROM date) = in_year
        ), 0)::NUMERIC AS total_income,

        COALESCE((
            SELECT SUM(amount)
            FROM budget_expense
            WHERE user_id = in_user_id
              AND EXTRACT(MONTH FROM date) = in_month
              AND EXTRACT(YEAR FROM date) = in_year
        ), 0)::NUMERIC AS total_expenses,

        (
            COALESCE((
                SELECT SUM(amount)
                FROM budget_income
                WHERE user_id = in_user_id
                  AND EXTRACT(MONTH FROM date) = in_month
                  AND EXTRACT(YEAR FROM date) = in_year
            ), 0) 
            - 
            COALESCE((
                SELECT SUM(amount)
                FROM budget_expense
                WHERE user_id = in_user_id
                  AND EXTRACT(MONTH FROM date) = in_month
                  AND EXTRACT(YEAR FROM date) = in_year
            ), 0)
        )::NUMERIC AS net_savings;
END;
$$ LANGUAGE plpgsql;




CREATE OR REPLACE FUNCTION get_expense_trends(
    in_user_id INTEGER,
    in_months INTEGER
)
RETURNS TABLE (
    category_name VARCHAR,
    month VARCHAR,
    total_amount NUMERIC,
    transaction_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.name::VARCHAR,
        TO_CHAR(e.date, 'YYYY-MM')::VARCHAR AS month,
        COALESCE(SUM(e.amount), 0)::NUMERIC AS total_amount,
        COUNT(e.id)::BIGINT AS transaction_count
    FROM budget_expense e
    JOIN budget_category c ON e.category_id = c.id
    WHERE e.user_id = in_user_id
      AND e.date >= CURRENT_DATE - (in_months || ' months')::INTERVAL
    GROUP BY c.name, TO_CHAR(e.date, 'YYYY-MM')
    ORDER BY c.name, TO_CHAR(e.date, 'YYYY-MM');
END;
$$ LANGUAGE plpgsql;

