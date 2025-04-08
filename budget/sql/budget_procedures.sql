-- Procedure to calculate monthly budget statistics
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
        COALESCE(SUM(e.amount), 0)::NUMERIC,
        c.budget::NUMERIC,
        CASE 
            WHEN c.budget > 0 THEN (COALESCE(SUM(e.amount), 0) / c.budget * 100)::NUMERIC 
            ELSE 0::NUMERIC 
        END,
        COUNT(e.id)::BIGINT
    FROM budget_category c
    LEFT JOIN budget_expense e ON e.category_id = c.id
        AND EXTRACT(MONTH FROM e.date) = month
        AND EXTRACT(YEAR FROM e.date) = year
        AND e.user_id = user_id
    WHERE c.user_id = user_id
    GROUP BY c.id, c.name, c.icon, c.color, c.budget;
END;
$$ LANGUAGE plpgsql;

-- Procedure to calculate monthly income vs expenses
CREATE OR REPLACE FUNCTION calculate_monthly_summary(
    user_id INTEGER,
    month INTEGER,
    year INTEGER
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
            WHERE user_id = $1
            AND EXTRACT(MONTH FROM date) = $2
            AND EXTRACT(YEAR FROM date) = $3
        ), 0)::NUMERIC,
        COALESCE((
            SELECT SUM(amount)
            FROM budget_expense
            WHERE user_id = $1
            AND EXTRACT(MONTH FROM date) = $2
            AND EXTRACT(YEAR FROM date) = $3
        ), 0)::NUMERIC,
        (COALESCE((
            SELECT SUM(amount)
            FROM budget_income
            WHERE user_id = $1
            AND EXTRACT(MONTH FROM date) = $2
            AND EXTRACT(YEAR FROM date) = $3
        ), 0) - COALESCE((
            SELECT SUM(amount)
            FROM budget_expense
            WHERE user_id = $1
            AND EXTRACT(MONTH FROM date) = $2
            AND EXTRACT(YEAR FROM date) = $3
        ), 0))::NUMERIC;
END;
$$ LANGUAGE plpgsql;

-- Procedure to get category-wise expense trends
CREATE OR REPLACE FUNCTION get_expense_trends(
    user_id INTEGER,
    months INTEGER
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
        TO_CHAR(e.date, 'YYYY-MM')::VARCHAR,
        COALESCE(SUM(e.amount), 0)::NUMERIC,
        COUNT(e.id)::BIGINT
    FROM budget_expense e
    JOIN budget_category c ON e.category_id = c.id
    WHERE e.user_id = user_id
    AND e.date >= CURRENT_DATE - (months || ' months')::INTERVAL
    GROUP BY c.name, TO_CHAR(e.date, 'YYYY-MM')
    ORDER BY c.name, TO_CHAR(e.date, 'YYYY-MM');
END;
$$ LANGUAGE plpgsql; 