import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_db_connection

def sync_seed():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO employees (id, name, department, position, level, location, manager, hire_date, contract_type, benefits)
                    VALUES ('E10001', '李伟', '技术研发部', '技术总监 / 研发主管', 'M1', '北京', '赵静', '2019-06-10', '全职', '["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"]'::jsonb)
                    ON CONFLICT (id) DO UPDATE SET position = EXCLUDED.position, level = EXCLUDED.level;
                    """
                )
                cur.execute(
                    """
                    INSERT INTO leave_balances (employee_id, annual, sick, personal)
                    VALUES ('E10001', 15.0, 10.0, 5.0)
                    ON CONFLICT (employee_id) DO NOTHING;
                    """
                )
                # 确保有一条给李伟审批的待办单据
                cur.execute(
                    """
                    INSERT INTO approvals (id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver)
                    VALUES ('APR-001', 'E10293', '张明', '年假申请', 'pending', '2026-05-15', '2026-06-01', '2026-06-02', '节后调休探亲，已交接前端开发进度', '李伟')
                    ON CONFLICT (id) DO UPDATE SET status = 'pending', approver = '李伟';
                    """
                )
                conn.commit()
                print("Seed sync completed successfully.")
    except Exception as e:
        print(f"Seed sync skipped: {e}")

if __name__ == "__main__":
    sync_seed()
