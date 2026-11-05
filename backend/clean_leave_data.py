import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from db.database import get_db_connection, _in_memory_approvals, MOCK_EMPLOYEES, get_leave_balance

def run_clean():
    # 2026-11-02 至 2026-11-03 期间张明的重复单据
    # 保留最早的一笔 APR-464（有效通过），其余作废
    keep_id = 'APR-464'
    invalid_ids = ['APR-906', 'APR-893', 'APR-695', 'APR-625']

    print(f"1. 准备作废重复单据: {invalid_ids}，保留生效单据: {keep_id}")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 作废重复单据
                for i_id in invalid_ids:
                    cur.execute("""
                        UPDATE approvals 
                        SET status = 'invalidated', 
                            comment = '【系统风控冲销】与单据 APR-464 (2026-11-02至11-03) 重复，已作废并冲正额度'
                        WHERE id = %s;
                    """, (i_id,))
                
                # 冲正张明（E10293）的年假余额
                # 初始 7 天 - APR-001 (2天) - APR-464 (2天) = 3.0 天
                cur.execute("""
                    UPDATE leave_balances 
                    SET annual = 3.0 
                    WHERE employee_id = 'E10293';
                """)
                conn.commit()
                print("   PostgreSQL 数据库更新成功！")
    except Exception as e:
        print(f"   PostgreSQL 更新出现异常 (可能使用纯内存模式): {e}")

    # 同步更新内存缓存
    for a in _in_memory_approvals:
        if a.get('id') in invalid_ids:
            a['status'] = 'invalidated'
            a['comment'] = '【系统风控冲销】与单据 APR-464 (2026-11-02至11-03) 重复，已作废并冲正额度'

    if 'E10293' in MOCK_EMPLOYEES:
        MOCK_EMPLOYEES['E10293'].leave_balance.annual = 3.0

    print("2. 内存与 Mock 数据对齐完成！")
    print(f"3. 张明 (E10293) 最新假期余额: {get_leave_balance('E10293')}")

if __name__ == "__main__":
    run_clean()
