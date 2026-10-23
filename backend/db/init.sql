-- 员工表
CREATE TABLE IF NOT EXISTS employees (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    level VARCHAR(50),
    location VARCHAR(100),
    manager VARCHAR(100),
    hire_date VARCHAR(50),
    contract_type VARCHAR(50),
    benefits JSONB DEFAULT '[]'::jsonb
);

-- 假期余额表
CREATE TABLE IF NOT EXISTS leave_balances (
    employee_id VARCHAR(50) PRIMARY KEY REFERENCES employees(id) ON DELETE CASCADE,
    annual NUMERIC(5, 1) DEFAULT 0,
    sick NUMERIC(5, 1) DEFAULT 0,
    personal NUMERIC(5, 1) DEFAULT 0
);

-- 日历事件表
CREATE TABLE IF NOT EXISTS calendar_events (
    id SERIAL PRIMARY KEY,
    employee_id VARCHAR(50) REFERENCES employees(id) ON DELETE CASCADE,
    event_date VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    event_type VARCHAR(50) NOT NULL
);

-- 审批单表
CREATE TABLE IF NOT EXISTS approvals (
    id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) REFERENCES employees(id) ON DELETE CASCADE,
    applicant VARCHAR(100) NOT NULL,
    approval_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    request_date VARCHAR(50) NOT NULL,
    start_date VARCHAR(50),
    end_date VARCHAR(50),
    reason TEXT,
    approver VARCHAR(100)
);

-- HR 服务工单表 (Service Request / Tickets)
CREATE TABLE IF NOT EXISTS hr_tickets (
    id VARCHAR(50) PRIMARY KEY,
    employee_id VARCHAR(50) REFERENCES employees(id) ON DELETE CASCADE,
    applicant VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    external_system_id VARCHAR(100)
);

-- 插入初始员工数据
INSERT INTO employees (id, name, department, position, level, location, manager, hire_date, contract_type, benefits)
VALUES
('E10293', '张明', '技术研发部', '高级前端工程师', 'P6', '北京', '李伟', '2022-03-15', '全职', '["五险一金", "补充商业保险", "年度体检", "弹性工作"]'::jsonb),
('E10456', '王芳', '人力资源部', 'HRBP', 'P7', '上海', '赵静', '2020-08-01', '全职', '["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"]'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- 插入假期余额
INSERT INTO leave_balances (employee_id, annual, sick, personal)
VALUES
('E10293', 7.0, 5.0, 2.0),
('E10456', 12.0, 8.0, 3.0)
ON CONFLICT (employee_id) DO NOTHING;

-- 插入日历事件
INSERT INTO calendar_events (employee_id, event_date, title, event_type)
VALUES
('E10293', '2026-01-20', '项目评审会', 'meeting'),
('E10293', '2026-01-22', 'Sprint Planning', 'meeting'),
('E10293', '2026-02-01', '春节假期开始', 'holiday');

-- 插入初始审批单
INSERT INTO approvals (id, employee_id, applicant, approval_type, status, request_date, approver)
VALUES
('APR-001', 'E10293', '张明', '年假申请', 'pending', '2026-01-15', '李伟'),
('APR-002', 'E10293', '张明', '差旅报销', 'approved', '2026-01-10', '李伟')
ON CONFLICT (id) DO NOTHING;
