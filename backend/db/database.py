"""
PostgreSQL 数据库交互层
封装员工、假期、日程、审批及工单的持久化存储
"""
import os
import json
from typing import Optional, List, Dict, Any
import psycopg
from models import EmployeeProfile, LeaveBalance

from psycopg.rows import dict_row

# 确保本地请求不经过代理
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
PG_DB = os.getenv("POSTGRES_DB", "")

DB_CONN_STR = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
DEFAULT_EMPLOYEE_ID = "E10293"


def get_db_connection():
    """获取数据库连接"""
    return psycopg.connect(DB_CONN_STR, row_factory=dict_row)


def init_db() -> bool:
    """检查并确认数据库连接"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return True
    except Exception as e:
        print(f"[Database] Connection check failed: {e}")
        return False


def get_employee(employee_id: str = DEFAULT_EMPLOYEE_ID) -> Optional[EmployeeProfile]:
    """获取员工档案数据"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.*, b.annual, b.sick, b.personal
                    FROM employees e
                    LEFT JOIN leave_balances b ON e.id = b.employee_id
                    WHERE e.id = %s;
                    """,
                    (employee_id,)
                )
                row = cur.fetchone()
                if not row:
                    return None

                benefits = row["benefits"]
                if isinstance(benefits, str):
                    benefits = json.loads(benefits)

                return EmployeeProfile(
                    id=row["id"],
                    name=row["name"],
                    department=row["department"],
                    position=row["position"],
                    level=row["level"] or "",
                    location=row["location"] or "",
                    manager=row["manager"] or "",
                    hire_date=row["hire_date"] or "",
                    contract_type=row["contract_type"] or "全职",
                    leave_balance=LeaveBalance(
                        annual=int(row["annual"]) if row["annual"] is not None else 0,
                        sick=int(row["sick"]) if row["sick"] is not None else 0,
                        personal=int(row["personal"]) if row["personal"] is not None else 0,
                    ),
                    benefits=benefits or []
                )
    except Exception as e:
        if employee_id == DEFAULT_EMPLOYEE_ID:
            return EmployeeProfile(
                id=DEFAULT_EMPLOYEE_ID,
                name="张明",
                department="技术研发部",
                position="高级前端工程师",
                level="P6",
                location="北京",
                manager="李伟",
                hire_date="2022-03-15",
                contract_type="全职",
                leave_balance=LeaveBalance(annual=7, sick=5, personal=2),
                benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作"]
            )
        return None


def get_current_employee() -> EmployeeProfile:
    """获取当前默认登录员工"""
    emp = get_employee(DEFAULT_EMPLOYEE_ID)
    if not emp:
        return EmployeeProfile(
            id=DEFAULT_EMPLOYEE_ID,
            name="张明",
            department="技术研发部",
            position="高级前端工程师",
            level="P6",
            location="北京",
            manager="李伟",
            hire_date="2022-03-15",
            contract_type="全职",
            leave_balance=LeaveBalance(annual=7, sick=5, personal=2),
            benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作"]
        )
    return emp



def get_leave_balance(employee_id: str = DEFAULT_EMPLOYEE_ID) -> Dict[str, int]:
    """获取假期余额"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT annual, sick, personal FROM leave_balances WHERE employee_id = %s;",
                    (employee_id,)
                )
                row = cur.fetchone()
                if row:
                    return {
                        "annual": int(row["annual"]),
                        "sick": int(row["sick"]),
                        "personal": int(row["personal"])
                    }
    except Exception as e:
        pass
    return {"annual": 7, "sick": 5, "personal": 2}


def check_calendar_conflicts(employee_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """检查指定日期区间的日历事件冲突"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT event_date, title, event_type
                FROM calendar_events
                WHERE (employee_id = %s OR employee_id IS NULL)
                  AND event_date >= %s AND event_date <= %s
                ORDER BY event_date ASC;
                """,
                (employee_id, start_date, end_date)
            )
            rows = cur.fetchall()
            return [
                {"date": r["event_date"], "title": r["title"], "type": r["event_type"]}
                for r in rows
            ]


_in_memory_approvals: List[Dict[str, Any]] = [
    {
        "id": "APR-101",
        "employee_id": DEFAULT_EMPLOYEE_ID,
        "applicant": "张明",
        "type": "年假",
        "status": "已通过",
        "date": "2026-04-10",
        "start_date": "2026-05-02",
        "end_date": "2026-05-04",
        "reason": "节假日错峰探亲",
        "approver": "王经理",
    }
]

_in_memory_tickets: List[Dict[str, Any]] = [
    {
        "id": "TCK-8801",
        "employee_id": DEFAULT_EMPLOYEE_ID,
        "applicant": "张明",
        "category": "社保公积金",
        "title": "异地公积金缴存证明开具咨询",
        "description": "请协助开具近期连续6个月公积金缴存证明",
        "priority": "medium",
        "status": "resolved",
        "assigned_to": "HR服务专员 (李莉)",
        "created_at": "2026-04-01 10:20:00",
        "external_system_id": "SN-INC-10921"
    }
]


def create_approval(
    approval_id: str,
    employee_id: str,
    applicant: str,
    approval_type: str,
    status: str,
    request_date: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reason: Optional[str] = None,
    approver: Optional[str] = None
) -> Dict[str, Any]:
    """创建审批单记录"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO approvals (id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, approval_type, status, applicant, request_date, start_date, end_date;
                    """,
                    (approval_id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver)
                )
                res = cur.fetchone()
                conn.commit()
                return dict(res)
    except Exception:
        item = {
            "id": approval_id,
            "employee_id": employee_id,
            "applicant": applicant,
            "type": approval_type,
            "approval_type": approval_type,
            "status": status,
            "date": request_date,
            "request_date": request_date,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "approver": approver,
        }
        _in_memory_approvals.append(item)
        return item


def query_approvals(employee_id: str = DEFAULT_EMPLOYEE_ID, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """查询审批单"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if request_id:
                    cur.execute(
                        """
                        SELECT id, approval_type AS type, status, applicant, request_date AS date, start_date, end_date, reason, approver
                        FROM approvals
                        WHERE id = %s AND employee_id = %s;
                        """,
                        (request_id, employee_id)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, approval_type AS type, status, applicant, request_date AS date, start_date, end_date, reason, approver
                        FROM approvals
                        WHERE employee_id = %s
                        ORDER BY request_date DESC;
                        """,
                        (employee_id,)
                    )
                rows = cur.fetchall()
                return [dict(r) for r in rows]
    except Exception:
        results = [a for a in _in_memory_approvals if a.get("employee_id") == employee_id]
        if request_id:
            results = [a for a in results if a.get("id") == request_id]
        return results


def create_hr_ticket(
    ticket_id: str,
    employee_id: str,
    applicant: str,
    category: str,
    title: str,
    description: str,
    priority: str = "medium",
    external_system_id: Optional[str] = None,
    assigned_to: Optional[str] = None
) -> Dict[str, Any]:
    """创建 HR 工单"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hr_tickets (id, employee_id, applicant, category, title, description, priority, status, assigned_to, external_system_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', %s, %s)
                    RETURNING id, category, title, priority, status, applicant, external_system_id;
                    """,
                    (ticket_id, employee_id, applicant, category, title, description, priority, assigned_to, external_system_id)
                )
                res = cur.fetchone()
                conn.commit()
                return dict(res)
    except Exception:
        item = {
            "id": ticket_id,
            "employee_id": employee_id,
            "applicant": applicant,
            "category": category,
            "title": title,
            "description": description,
            "priority": priority,
            "status": "open",
            "assigned_to": assigned_to or "HR 服务专员",
            "external_system_id": external_system_id,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _in_memory_tickets.append(item)
        return item


def query_hr_tickets(employee_id: str = DEFAULT_EMPLOYEE_ID, ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """查询 HR 工单"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if ticket_id:
                    cur.execute(
                        """
                        SELECT id, employee_id, applicant, category, title, description, priority, status, assigned_to, created_at, external_system_id
                        FROM hr_tickets
                        WHERE id = %s AND employee_id = %s;
                        """,
                        (ticket_id, employee_id)
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, employee_id, applicant, category, title, description, priority, status, assigned_to, created_at, external_system_id
                        FROM hr_tickets
                        WHERE employee_id = %s
                        ORDER BY created_at DESC;
                        """,
                        (employee_id,)
                    )
                rows = cur.fetchall()
                return [dict(r) for r in rows]
    except Exception:
        results = [t for t in _in_memory_tickets if t.get("employee_id") == employee_id]
        if ticket_id:
            results = [t for t in results if t.get("id") == ticket_id]
        return results

