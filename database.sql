CREATE DATABASE IF NOT EXISTS SaaS_AI_DB;
USE SaaS_AI_DB;

CREATE TABLE Plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(50) NOT NULL,
    monthly_price DECIMAL(10, 2) NOT NULL,
    ai_token_limit INT NOT NULL
);

CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    company_size VARCHAR(20) CHECK (company_size IN ('Startup', 'SMB', 'Enterprise')),
    signup_date DATE NOT NULL,
    plan_id INT,
    FOREIGN KEY (plan_id) REFERENCES Plans(plan_id)
);

CREATE TABLE UsageLogs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    usage_month DATE NOT NULL,
    tokens_consumed INT NOT NULL,
    ai_api_cost DECIMAL(10, 2) NOT NULL,
    support_tickets_opened INT DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE Subscriptions (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    status VARCHAR(20) CHECK (status IN ('Active', 'Churned', 'Upgraded')),
    churn_reason VARCHAR(150),
    updated_at DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

INSERT INTO Plans (plan_name, monthly_price, ai_token_limit) VALUES
('Starter', 49.00, 100000),
('Pro', 149.00, 500000),
('Enterprise', 499.00, 2000000);

INSERT INTO Customers (customer_name, company_size, signup_date, plan_id) VALUES
('Alpha Tech', 'Startup', '2025-11-10', 1),
('Beta Solutions', 'Startup', '2025-12-01', 1),
('Gamma Corp', 'SMB', '2025-10-15', 2),
('Delta Retail', 'SMB', '2025-11-20', 2),
('Epsilon Group', 'Enterprise', '2025-09-05', 3),
('Zeta Studio', 'Startup', '2026-01-08', 1),
('Eta Logistics', 'SMB', '2025-12-12', 2),
('Theta Finance', 'Enterprise', '2025-10-01', 3),
('Iota Media', 'Startup', '2026-01-15', 2),
('Kappa Health', 'SMB', '2025-11-25', 2),
('Lambda AI', 'Startup', '2026-02-01', 1),
('Mu Global', 'Enterprise', '2025-08-20', 3);

INSERT INTO Subscriptions (customer_id, status, churn_reason, updated_at) VALUES
(1, 'Churned', 'Chi phí vượt ngân sách', '2026-03-15'),
(2, 'Active', NULL, '2026-03-01'),
(3, 'Upgraded', NULL, '2026-03-10'),
(4, 'Churned', 'Giới hạn AI Token thấp', '2026-02-28'),
(5, 'Active', NULL, '2026-03-01'),
(6, 'Churned', 'Lỗi kỹ thuật / API chậm', '2026-03-20'),
(7, 'Active', NULL, '2026-03-05'),
(8, 'Upgraded', NULL, '2026-03-12'),
(9, 'Churned', 'Chi phí vượt ngân sách', '2026-03-25'),
(10, 'Active', NULL, '2026-03-01'),
(11, 'Churned', 'Chuyển sang đối thủ', '2026-03-18'),
(12, 'Active', NULL, '2026-03-01');

INSERT INTO UsageLogs (customer_id, usage_month, tokens_consumed, ai_api_cost, support_tickets_opened) VALUES
(1, '2026-01-01', 95000, 28.50, 2),
(1, '2026-02-01', 135000, 42.00, 5),
(1, '2026-03-01', 160000, 55.00, 6),
(2, '2026-01-01', 60000, 15.00, 1),
(2, '2026-02-01', 75000, 19.50, 0),
(2, '2026-03-01', 82000, 21.00, 1),
(3, '2026-01-01', 420000, 95.00, 1),
(3, '2026-02-01', 480000, 110.00, 2),
(3, '2026-03-01', 510000, 118.00, 1),
(4, '2026-01-01', 520000, 130.00, 4),
(4, '2026-02-01', 610000, 155.00, 5),
(5, '2026-01-01', 1500000, 290.00, 1),
(5, '2026-02-01', 1650000, 310.00, 0),
(5, '2026-03-01', 1800000, 340.00, 2),
(6, '2026-01-01', 110000, 35.00, 4),
(6, '2026-02-01', 140000, 48.00, 6),
(6, '2026-03-01', 125000, 40.00, 7),
(7, '2026-01-01', 300000, 70.00, 1),
(7, '2026-02-01', 320000, 75.00, 2),
(7, '2026-03-01', 350000, 82.00, 1),
(8, '2026-01-01', 1700000, 320.00, 0),
(8, '2026-02-01', 1900000, 360.00, 1),
(8, '2026-03-01', 2100000, 395.00, 2),
(9, '2026-01-01', 490000, 125.00, 3),
(9, '2026-02-01', 580000, 148.00, 4),
(9, '2026-03-01', 630000, 165.00, 5),
(10, '2026-01-01', 280000, 65.00, 0),
(10, '2026-02-01', 310000, 72.00, 1),
(10, '2026-03-01', 295000, 68.00, 1),
(11, '2026-02-01', 120000, 38.00, 3),
(11, '2026-03-01', 145000, 46.00, 5),
(12, '2026-01-01', 1400000, 260.00, 1),
(12, '2026-02-01', 1550000, 285.00, 1),
(12, '2026-03-01', 1600000, 295.00, 0);