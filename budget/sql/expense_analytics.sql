DELIMITER //

CREATE PROCEDURE GetExpenseAnalytics(
    IN user_id INT,
    IN start_date DATE,
    IN end_date DATE
)
BEGIN
    -- Get total expenses for the period
    SELECT 
        SUM(e.amount) as total_expenses,
        COUNT(*) as transaction_count,
        AVG(e.amount) as average_transaction,
        MAX(e.amount) as highest_transaction,
        MIN(e.amount) as lowest_transaction
    FROM budget_expense e
    WHERE e.user_id = user_id
    AND e.date BETWEEN start_date AND end_date;

    -- Get expenses by category
    SELECT 
        c.name as category_name,
        SUM(e.amount) as category_total,
        COUNT(*) as transaction_count,
        (SUM(e.amount) / (
            SELECT SUM(amount) 
            FROM budget_expense 
            WHERE user_id = user_id 
            AND date BETWEEN start_date AND end_date
        ) * 100) as percentage_of_total
    FROM budget_expense e
    JOIN budget_category c ON e.category_id = c.id
    WHERE e.user_id = user_id
    AND e.date BETWEEN start_date AND end_date
    GROUP BY c.id, c.name
    ORDER BY category_total DESC;

    -- Get daily expense trend
    SELECT 
        DATE(e.date) as expense_date,
        SUM(e.amount) as daily_total,
        COUNT(*) as transaction_count
    FROM budget_expense e
    WHERE e.user_id = user_id
    AND e.date BETWEEN start_date AND end_date
    GROUP BY DATE(e.date)
    ORDER BY expense_date;

    -- Get budget vs actual
    SELECT 
        c.name as category_name,
        c.budget as monthly_budget,
        SUM(e.amount) as actual_spent,
        (c.budget - SUM(e.amount)) as remaining_budget,
        (SUM(e.amount) / c.budget * 100) as budget_utilization
    FROM budget_category c
    LEFT JOIN budget_expense e ON c.id = e.category_id
    AND e.date BETWEEN start_date AND end_date
    WHERE c.user_id = user_id
    GROUP BY c.id, c.name, c.budget
    HAVING actual_spent > 0
    ORDER BY budget_utilization DESC;
END //

DELIMITER ; 