-- Initialize expenses table
CREATE TABLE IF NOT EXISTS expense (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_expense_user_id ON expense(telegram_user_id);
CREATE INDEX idx_expense_created_at ON expense(created_at);
