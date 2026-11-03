"""
PostgreSQL 数据库交互层
封装员工、假期、日程、审批及工单的持久化存储
"""
import os
import json
import decimal
from datetime import date, datetime
import contextvars
from typing import Optional, List, Dict, Any
import psycopg
from models import EmployeeProfile, LeaveBalance

from psycopg.rows import dict_row

from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
load_dotenv()

# 确保本地请求不经过代理
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

PG_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
PG_DB = os.getenv("POSTGRES_DB", "")

DB_CONN_STR = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
DEFAULT_EMPLOYEE_ID = "E10293"

# 协程/线程安全的当前请求操作员工上下文
_current_employee_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_employee_id", default=DEFAULT_EMPLOYEE_ID
)


def set_current_employee_id(emp_id: str) -> None:
    """设置当前请求/会话上下文中的操作员工工号"""
    if emp_id:
        _current_employee_id_ctx.set(emp_id)


def get_current_employee_id() -> str:
    """获取当前请求/会话上下文中的操作员工工号"""
    return _current_employee_id_ctx.get()
def sanitize_db_output(val: Any) -> Any:
    """递归清理从数据库查询出的数据，将 Decimal 转换为 float，日期转为 ISO 字符串，确保 JSON 序列化无障碍"""
    if isinstance(val, dict):
        return {k: sanitize_db_output(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_db_output(v) for v in val]
    elif isinstance(val, decimal.Decimal):
        return float(val)
    elif isinstance(val, (datetime, date)):
        return val.isoformat()
    return val




MOCK_EMPLOYEES: Dict[str, EmployeeProfile] = {
    "E10293": EmployeeProfile(
        id="E10293",
        name="张明",
        department="技术研发部",
        position="高级前端工程师",
        level="P6",
        location="北京",
        manager="李伟",
        hire_date="2022-03-15",
        contract_type="全职",
        leave_balance=LeaveBalance(annual=7, sick=5, personal=2),
        benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作"],
    ),
    "E10001": EmployeeProfile(
        id="E10001",
        name="李伟",
        department="技术研发部",
        position="技术研发部总监",
        level="M1",
        location="北京",
        manager="赵静",
        hire_date="2019-06-10",
        contract_type="全职",
        leave_balance=LeaveBalance(annual=15, sick=10, personal=5),
        benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"],
    ),
    "E10456": EmployeeProfile(
        id="E10456",
        name="王芳",
        department="人力资源部",
        position="HRBP",
        level="P7",
        location="上海",
        manager="赵静",
        hire_date="2020-08-01",
        contract_type="全职",
        leave_balance=LeaveBalance(annual=12, sick=8, personal=3),
        benefits=["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"],
    ),
}


def get_db_connection():
    """获取数据库连接"""
    if not PG_USER or not PG_DB:
        raise ConnectionError("PostgreSQL connection parameters not fully configured")
    return psycopg.connect(DB_CONN_STR, row_factory=dict_row, connect_timeout=2)


def init_db() -> bool:
    """检查并确认数据库连接，并确保初始角色就绪"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                try:
                    cur.execute(
                        """
                        INSERT INTO employees (id, name, department, position, level, location, manager, hire_date, contract_type, benefits)
                        VALUES ('E10001', '李伟', '技术研发部', '技术总监 / 研发主管', 'M1', '北京', '赵静', '2019-06-10', '全职', '["五险一金", "补充商业保险", "年度体检", "弹性工作", "股票期权"]'::jsonb)
                        ON CONFLICT (id) DO NOTHING;
                        INSERT INTO leave_balances (employee_id, annual, sick, personal)
                        VALUES ('E10001', 15.0, 10.0, 5.0)
                        ON CONFLICT (employee_id) DO NOTHING;
                        INSERT INTO approvals (id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver)
                        VALUES ('APR-001', 'E10293', '张明', '年假申请', 'pending', '2026-05-15', '2026-06-01', '2026-06-02', '节后调休探亲，已交接前端开发进度', '李伟')
                        ON CONFLICT (id) DO UPDATE SET
                            start_date = COALESCE(approvals.start_date, EXCLUDED.start_date),
                            end_date = COALESCE(approvals.end_date, EXCLUDED.end_date),
                            reason = COALESCE(approvals.reason, EXCLUDED.reason),
                            approver = EXCLUDED.approver;
                        UPDATE approvals 
                        SET start_date = '2026-06-01', 
                            end_date = '2026-06-02', 
                            reason = '节后调休探亲，已交接前端开发进度', 
                            request_date = '2026-05-15'
                        WHERE id = 'APR-001' AND (start_date IS NULL OR end_date IS NULL);
                        """
                    )
                    conn.commit()
                except Exception:
                    pass
                return True
    except Exception as e:
        print(f"[Database] Connection check failed: {e}")
        return False


def get_employee(employee_id: Optional[str] = None) -> Optional[EmployeeProfile]:
    """获取员工档案数据"""
    target_id = employee_id or get_current_employee_id()
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
                    (target_id,)
                )
                row = cur.fetchone()
                if not row:
                    return MOCK_EMPLOYEES.get(target_id)

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
    except Exception:
        return MOCK_EMPLOYEES.get(target_id) or MOCK_EMPLOYEES.get(DEFAULT_EMPLOYEE_ID)


def get_current_employee(employee_id: Optional[str] = None) -> EmployeeProfile:
    """获取当前登录或上下文指定的员工"""
    target_id = employee_id or get_current_employee_id()
    emp = get_employee(target_id)
    if not emp:
        return MOCK_EMPLOYEES.get(DEFAULT_EMPLOYEE_ID)
    return emp


def get_all_employees() -> List[EmployeeProfile]:
    """获取系统中所有员工列表（供身份快速切换 Persona Switcher）"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.*, b.annual, b.sick, b.personal
                    FROM employees e
                    LEFT JOIN leave_balances b ON e.id = b.employee_id
                    ORDER BY e.id ASC;
                    """
                )
                rows = cur.fetchall()
                if rows:
                    res = []
                    for row in rows:
                        b = row["benefits"]
                        if isinstance(b, str):
                            b = json.loads(b)
                        res.append(EmployeeProfile(
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
                            benefits=b or []
                        ))
                    # 确保张明、李伟、王芳三大 Persona 完备
                    existing_ids = {r.id for r in res}
                    for mock_id, mock_emp in MOCK_EMPLOYEES.items():
                        if mock_id not in existing_ids:
                            res.append(mock_emp)
                    return res
    except Exception:
        pass
    return list(MOCK_EMPLOYEES.values())



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
            return sanitize_db_output([
                {"date": r["event_date"], "title": r["title"], "type": r["event_type"]}
                for r in rows
            ])


_in_memory_approvals: List[Dict[str, Any]] = [
    {
        "id": "APR-001",
        "approval_id": "APR-001",
        "employee_id": "E10293",
        "applicant": "张明",
        "employee_name": "张明",
        "type": "年假申请",
        "approval_type": "年假申请",
        "status": "pending",
        "date": "2026-05-15",
        "request_date": "2026-05-15",
        "start_date": "2026-06-01",
        "end_date": "2026-06-02",
        "reason": "节后调休探亲，已协调交接前端代码合并",
        "approver": "李伟",
        "comment": None,
    },
    {
        "id": "APR-101",
        "employee_id": "E10293",
        "applicant": "张明",
        "type": "年假",
        "approval_type": "年假",
        "status": "approved",
        "date": "2026-04-10",
        "request_date": "2026-04-10",
        "start_date": "2026-05-02",
        "end_date": "2026-05-04",
        "reason": "节假日错峰探亲",
        "approver": "李伟",
        "comment": "同意，保持手机通畅",
    },
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
                return sanitize_db_output(dict(res))
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
                return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        results = [a for a in _in_memory_approvals if a.get("employee_id") == employee_id]
        if request_id:
            results = [a for a in results if a.get("id") == request_id]
        return sanitize_db_output(results)


def deduct_leave_balance(employee_id: str, leave_type: str = "annual", days: float = 1.0) -> Dict[str, Any]:
    """从指定员工扣减假期余额（支持真实数据库与内存 MOCK 同步）"""
    field = "annual"
    if "病" in leave_type or "sick" in leave_type.lower():
        field = "sick"
    elif "事" in leave_type or "personal" in leave_type.lower():
        field = "personal"

    # 同步内存 MOCK 数据
    target_mock = MOCK_EMPLOYEES.get(employee_id)
    if target_mock:
        cur_val = getattr(target_mock.leave_balance, field, 0)
        new_val = max(0, int(cur_val - days))
        setattr(target_mock.leave_balance, field, new_val)

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE leave_balances SET {field} = GREATEST(0, {field} - %s) WHERE employee_id = %s RETURNING annual, sick, personal;",
                    (days, employee_id)
                )
                res = cur.fetchone()
                conn.commit()
                if res:
                    return sanitize_db_output(dict(res))
    except Exception:
        pass

    if target_mock:
        return {
            "annual": target_mock.leave_balance.annual,
            "sick": target_mock.leave_balance.sick,
            "personal": target_mock.leave_balance.personal,
        }
    return {"annual": 5, "sick": 5, "personal": 2}


def query_pending_approvals_for_manager(manager_name_or_id: str) -> List[Dict[str, Any]]:
    """查询等待该主管（或管理员/HRBP）审批的单据列表"""
    manager_name = manager_name_or_id
    if manager_name_or_id.startswith("E") or manager_name_or_id.startswith("M"):
        emp = get_employee(manager_name_or_id)
        if emp:
            manager_name = emp.name

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if manager_name == "王芳" or manager_name_or_id == "E10456":
                    cur.execute(
                        """
                        SELECT id, id AS approval_id, employee_id, approval_type AS type, approval_type, status, applicant, applicant AS employee_name, request_date AS date, request_date, start_date, end_date, reason, approver
                        FROM approvals
                        WHERE status IN ('pending', '待审批')
                        ORDER BY request_date DESC;
                        """
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, id AS approval_id, employee_id, approval_type AS type, approval_type, status, applicant, applicant AS employee_name, request_date AS date, request_date, start_date, end_date, reason, approver
                        FROM approvals
                        WHERE status IN ('pending', '待审批')
                          AND (approver = %s OR approver = %s)
                        ORDER BY request_date DESC;
                        """,
                        (manager_name, manager_name_or_id)
                    )
                rows = cur.fetchall()
                if rows is not None:
                    return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        pass

    results = [
        a for a in _in_memory_approvals
        if a.get("status") in ("pending", "待审批")
    ]
    if manager_name != "王芳" and manager_name_or_id != "E10456":
        results = [
            a for a in results
            if a.get("approver") in (manager_name, manager_name_or_id)
        ]
    return sanitize_db_output(results)

def update_approval_status(
    approval_id: str,
    approver_name_or_id: str,
    decision: str,
    comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理审批单（通过或驳回），并在通过时触发业务副作用（原子扣减假期、日历登记）
    decision: "approved" | "rejected"
    """
    manager_name = approver_name_or_id
    if approver_name_or_id.startswith("E") or approver_name_or_id.startswith("M"):
        emp = get_employee(approver_name_or_id)
        if emp:
            manager_name = emp.name

    norm_decision = "approved" if str(decision).lower() in ("approved", "agree", "pass", "通过", "同意", "批准") else "rejected"
    
    target = None
    target_idx = -1
    for idx, a in enumerate(_in_memory_approvals):
        if a.get("id") == approval_id:
            target = a
            target_idx = idx
            break

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE approvals
                    SET status = %s, approver = %s
                    WHERE id = %s
                    RETURNING id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver;
                    """,
                    (norm_decision, manager_name, approval_id)
                )
                row = cur.fetchone()
                if row:
                    target = sanitize_db_output(dict(row))
                    conn.commit()
    except Exception:
        pass

    if not target:
        target = {
            "id": approval_id,
            "employee_id": DEFAULT_EMPLOYEE_ID,
            "applicant": "张明",
            "type": "年假申请",
            "approval_type": "年假申请",
            "status": norm_decision,
            "date": "2026-05-15",
            "request_date": "2026-05-15",
            "start_date": "2026-06-01",
            "end_date": "2026-06-02",
            "reason": "年假调休",
            "approver": manager_name,
            "comment": comment or ("审批通过" if norm_decision == "approved" else "审批驳回"),
        }
        _in_memory_approvals.append(target)
    else:
        target["status"] = norm_decision
        target["approver"] = manager_name
        target["comment"] = comment or ("审批通过" if norm_decision == "approved" else "审批驳回")
        # 同步写入内存 fallback 列表，防止后续因数据为空 fallback 时状态回滚
        if target_idx >= 0:
            _in_memory_approvals[target_idx] = dict(target)
        else:
            _in_memory_approvals.append(dict(target))

    deducted_balance = None
    if norm_decision == "approved":
        applicant_id = target.get("employee_id") or DEFAULT_EMPLOYEE_ID
        app_type = target.get("approval_type") or target.get("type", "年假")
        
        calc_days = 2.0
        s_date = target.get("start_date")
        e_date = target.get("end_date")
        if s_date and e_date:
            try:
                from datetime import datetime as dt
                d1 = dt.strptime(s_date, "%Y-%m-%d")
                d2 = dt.strptime(e_date, "%Y-%m-%d")
                calc_days = max(1.0, float((d2 - d1).days + 1))
            except Exception:
                calc_days = 2.0

        deducted_balance = deduct_leave_balance(applicant_id, app_type, calc_days)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO calendar_events (employee_id, event_date, title, event_type)
                        VALUES (%s, %s, %s, 'holiday')
                        ON CONFLICT DO NOTHING;
                        """,
                        (applicant_id, s_date or "2026-06-01", f"请假({app_type}) - {target.get('applicant')}")
                    )
                    conn.commit()
        except Exception:
            pass

    return sanitize_db_output({
        "success": True,
        "approval": target,
        "leave_balance_deducted": deducted_balance,
        "message": f"审批单 {approval_id} 已成功判定为【{'已通过' if norm_decision == 'approved' else '已驳回'}】"
    })



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
                return sanitize_db_output(dict(res))
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
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        results = [t for t in _in_memory_tickets if t.get("employee_id") == employee_id]
        if ticket_id:
            results = [t for t in results if t.get("id") == ticket_id]
        return sanitize_db_output(results)

