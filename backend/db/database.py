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
    """检查并确认数据库连接，并确保初始角色与数据库表字段就绪"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                try:
                    # 动态平滑迁移：补齐审批流历史与审计留言字段，以及人事证明与会话持久化表
                    cur.execute(
                        """
                        ALTER TABLE approvals ADD COLUMN IF NOT EXISTS comment TEXT;
                        ALTER TABLE approvals ADD COLUMN IF NOT EXISTS action_date VARCHAR(50);

                        CREATE TABLE IF NOT EXISTS documents (
                            id VARCHAR(50) PRIMARY KEY,
                            employee_id VARCHAR(50) REFERENCES employees(id) ON DELETE CASCADE,
                            applicant VARCHAR(100) NOT NULL,
                            doc_type VARCHAR(50) NOT NULL,
                            purpose VARCHAR(200) NOT NULL,
                            language VARCHAR(50) DEFAULT '中文',
                            status VARCHAR(50) NOT NULL DEFAULT 'processing',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            completed_at TIMESTAMP WITH TIME ZONE,
                            metadata JSONB DEFAULT '{}'::jsonb
                        );

                        CREATE TABLE IF NOT EXISTS chat_messages (
                            id VARCHAR(100) PRIMARY KEY,
                            session_id VARCHAR(100) NOT NULL,
                            employee_id VARCHAR(50) REFERENCES employees(id) ON DELETE CASCADE,
                            role VARCHAR(20) NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            metadata JSONB DEFAULT '{}'::jsonb
                        );
                        """
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()

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
                        UPDATE approvals 
                        SET comment = '票据合规，准予报销', action_date = '2026-01-11'
                        WHERE id = 'APR-002' AND (comment IS NULL OR action_date IS NULL);
                        UPDATE approvals
                        SET comment = '审批流程已办结'
                        WHERE status IN ('approved', 'rejected') AND (comment IS NULL OR comment = '');
                        UPDATE approvals
                        SET action_date = COALESCE(NULLIF(action_date, ''), request_date, '2026-05-15')
                        WHERE status IN ('approved', 'rejected') AND (action_date IS NULL OR action_date = '');
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
        "action_date": None,
    },
    {
        "id": "APR-002",
        "approval_id": "APR-002",
        "employee_id": "E10293",
        "applicant": "张明",
        "employee_name": "张明",
        "type": "差旅报销",
        "approval_type": "差旅报销",
        "status": "approved",
        "date": "2026-01-10",
        "request_date": "2026-01-10",
        "start_date": "2026-01-12",
        "end_date": "2026-01-13",
        "reason": "上海客户技术支持差旅",
        "approver": "李伟",
        "comment": "票据合规，准予报销",
        "action_date": "2026-01-11",
    },
    {
        "id": "APR-101",
        "approval_id": "APR-101",
        "employee_id": "E10293",
        "applicant": "张明",
        "employee_name": "张明",
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
        "action_date": "2026-04-11",
    },
    {
        "id": "APR-102",
        "approval_id": "APR-102",
        "employee_id": "E10293",
        "applicant": "张明",
        "employee_name": "张明",
        "type": "在职证明开具",
        "approval_type": "在职证明开具",
        "status": "approved",
        "date": "2026-05-01",
        "request_date": "2026-05-01",
        "start_date": "2026-05-01",
        "end_date": "2026-05-01",
        "reason": "出国签证办理使用",
        "approver": "王芳",
        "comment": "公章审核完毕，已签发电子件",
        "action_date": "2026-05-02",
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

_in_memory_documents: List[Dict[str, Any]] = [
    {
        "id": "DOC-20260501-01",
        "employee_id": DEFAULT_EMPLOYEE_ID,
        "applicant": "张明",
        "doc_type": "在职证明",
        "purpose": "出国签证办理使用",
        "language": "中文",
        "status": "completed",
        "created_at": "2026-05-01 10:00:00",
        "completed_at": "2026-05-02 14:30:00",
        "metadata": {"archived": True},
    }
]

_in_memory_chat_messages: List[Dict[str, Any]] = []


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


def query_approvals(
    employee_id: str = DEFAULT_EMPLOYEE_ID,
    request_id: Optional[str] = None,
    status: Optional[str] = None,
    scope: Optional[str] = None,
    applicant_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    approval_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """全维度审批单查询（支持单号、申请人、起止日期、审批状态、经办视角复合过滤）"""
    cur_emp = get_employee(employee_id)
    cur_name = cur_emp.name if cur_emp else ""
    is_mgr = bool(cur_emp and (cur_emp.level.startswith("M") or "主管" in cur_emp.position or "总监" in cur_emp.position))
    is_hr = bool(cur_emp and ("HR" in cur_emp.department or "HR" in cur_emp.position or cur_emp.name == "王芳"))

    norm_status = None
    if status and str(status).lower() not in ("all", "全部"):
        sl = str(status).lower()
        if sl in ("pending", "待审批", "待办"): norm_status = "pending"
        elif sl in ("approved", "已批准", "通过", "已通过"): norm_status = "approved"
        elif sl in ("rejected", "已驳回", "驳回", "拒绝"): norm_status = "rejected"
        else: norm_status = status

    eff_scope = scope or ("all" if is_hr else ("my_approvals" if (is_mgr and (norm_status or applicant_name)) else ("all" if is_mgr else "my_requests")))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                where, params = [], []
                if request_id:
                    where.append("id = %s")
                    params.append(request_id)
                    if not (is_mgr or is_hr):
                        where.append("(employee_id = %s OR approver = %s OR approver = %s)")
                        params.extend([employee_id, cur_name, employee_id])
                else:
                    if eff_scope == "my_requests":
                        where.append("employee_id = %s"); params.append(employee_id)
                    elif eff_scope == "my_approvals" and not is_hr:
                        where.append("(approver = %s OR approver = %s)"); params.extend([cur_name, employee_id])
                    elif eff_scope == "all" and not is_hr:
                        if is_mgr:
                            where.append("(employee_id = %s OR approver = %s OR approver = %s)")
                            params.extend([employee_id, cur_name, employee_id])
                        else:
                            where.append("employee_id = %s"); params.append(employee_id)
                    if norm_status:
                        where.append("status = %s"); params.append(norm_status)
                    if applicant_name:
                        where.append("(applicant LIKE %s OR employee_id = %s)"); params.extend([f"%{applicant_name}%", applicant_name])
                    if start_date:
                        where.append("(request_date >= %s OR COALESCE(start_date, request_date) >= %s)"); params.extend([start_date, start_date])
                    if end_date:
                        where.append("(request_date <= %s OR COALESCE(end_date, request_date) <= %s)"); params.extend([end_date, end_date])
                    if approval_type:
                        where.append("approval_type LIKE %s"); params.append(f"%{approval_type}%")

                where_sql = ("WHERE " + " AND ".join(where)) if where else ""
                sql = f"""
                    SELECT id, id AS approval_id, employee_id, approval_type AS type, approval_type, 
                           status, applicant, applicant AS employee_name, request_date AS date, 
                           request_date, start_date, end_date, reason, approver, comment, action_date
                    FROM approvals
                    {where_sql}
                    ORDER BY request_date DESC, id DESC;
                """
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
                if rows is not None:
                    return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        pass

    results = list(_in_memory_approvals)
    if request_id:
        results = [a for a in results if a.get("id") == request_id or a.get("approval_id") == request_id]
        if not (is_mgr or is_hr):
            results = [a for a in results if a.get("employee_id") == employee_id or a.get("approver") in (cur_name, employee_id)]
        return sanitize_db_output(results)

    if eff_scope == "my_requests":
        results = [a for a in results if a.get("employee_id") == employee_id]
    elif eff_scope == "my_approvals" and not is_hr:
        results = [a for a in results if a.get("approver") in (cur_name, employee_id)]
    elif eff_scope == "all" and not is_hr:
        if is_mgr:
            results = [a for a in results if a.get("employee_id") == employee_id or a.get("approver") in (cur_name, employee_id)]
        else:
            results = [a for a in results if a.get("employee_id") == employee_id]

    if norm_status:
        results = [a for a in results if a.get("status") == norm_status]
    if applicant_name:
        results = [a for a in results if applicant_name in str(a.get("applicant", "")) or applicant_name == a.get("employee_id")]
    if start_date:
        results = [a for a in results if str(a.get("request_date") or a.get("start_date") or "") >= start_date]
    if end_date:
        results = [a for a in results if str(a.get("request_date") or a.get("end_date") or "") <= end_date]
    if approval_type:
        results = [a for a in results if approval_type in str(a.get("approval_type") or a.get("type") or "")]

    results.sort(key=lambda x: str(x.get("request_date") or ""), reverse=True)
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

    action_today = datetime.now().strftime("%Y-%m-%d")
    final_comment = comment or ("审批通过" if norm_decision == "approved" else "审批驳回")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        UPDATE approvals
                        SET status = %s, approver = %s, comment = %s, action_date = %s
                        WHERE id = %s
                        RETURNING id, employee_id, applicant, approval_type, status, request_date, start_date, end_date, reason, approver, comment, action_date;
                        """,
                        (norm_decision, manager_name, final_comment, action_today, approval_id)
                    )
                    row = cur.fetchone()
                except Exception:
                    conn.rollback()
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
            "comment": final_comment,
            "action_date": action_today,
        }
        _in_memory_approvals.append(target)
    else:
        target["status"] = norm_decision
        target["approver"] = manager_name
        target["comment"] = final_comment
        target["action_date"] = action_today
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



# ============ 人事证明与申请 (Certificates & Documents) ============

def normalize_doc_type(doc_type: str) -> str:
    """归一化证明文件类型名称"""
    raw = (doc_type or "").strip().lower()
    if any(k in raw for k in ["在职", "employment"]):
        return "在职证明"
    if any(k in raw for k in ["收入", "薪酬", "income", "salary"]):
        return "收入证明"
    if any(k in raw for k in ["实习", "intern"]):
        return "实习证明"
    if any(k in raw for k in ["离职", "leaving", "termination"]):
        return "离职证明"
    return doc_type.strip() if doc_type else "在职证明"


def match_document_purpose(p1: str, p2: str) -> bool:
    """比较两个开具用途是否实质相同"""
    s1 = (p1 or "").strip().lower()
    s2 = (p2 or "").strip().lower()
    if not s1 or not s2:
        return True
    if s1 in s2 or s2 in s1:
        return True
    keywords = ["签证", "贷款", "买房", "购房", "落户", "入学", "入职", "离职", "车贷", "房贷", "公证", "信用卡"]
    for kw in keywords:
        if kw in s1 and kw in s2:
            return True
    return False


def create_document(
    doc_id: str,
    employee_id: str,
    applicant: str,
    doc_type: str,
    purpose: str,
    language: str = "中文",
    status: str = "processing",
    metadata: Optional[Dict[str, Any]] = None,
    created_at: Optional[str] = None,
) -> Dict[str, Any]:
    """创建人事证明申请记录"""
    norm_type = normalize_doc_type(doc_type)
    now_str = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents (id, employee_id, applicant, doc_type, purpose, language, status, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id, employee_id, applicant, doc_type, purpose, language, status, created_at, completed_at, metadata;
                    """,
                    (doc_id, employee_id, applicant, norm_type, purpose, language, status, meta_json)
                )
                res = cur.fetchone()
                conn.commit()
                if res:
                    return sanitize_db_output(dict(res))
    except Exception:
        pass

    item = {
        "id": doc_id,
        "employee_id": employee_id,
        "applicant": applicant,
        "doc_type": norm_type,
        "purpose": purpose,
        "language": language,
        "status": status,
        "created_at": now_str,
        "completed_at": None,
        "metadata": metadata or {},
    }
    _in_memory_documents.append(item)
    return item



def query_documents(
    employee_id: Optional[str] = None,
    doc_type: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """查询人事证明申请记录"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                where, params = [], []
                if employee_id:
                    where.append("employee_id = %s")
                    params.append(employee_id)
                if doc_type:
                    where.append("doc_type = %s")
                    params.append(normalize_doc_type(doc_type))
                if status:
                    where.append("status = %s")
                    params.append(status)
                where_clause = ("WHERE " + " AND ".join(where)) if where else ""
                cur.execute(
                    f"""
                    SELECT id, employee_id, applicant, doc_type, purpose, language, status, created_at, completed_at, metadata
                    FROM documents
                    {where_clause}
                    ORDER BY created_at DESC;
                    """,
                    tuple(params)
                )
                rows = cur.fetchall()
                if rows is not None:
                    return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        pass

    results = list(_in_memory_documents)
    if employee_id:
        results = [d for d in results if d.get("employee_id") == employee_id]
    if doc_type:
        norm_t = normalize_doc_type(doc_type)
        results = [d for d in results if d.get("doc_type") == norm_t]
    if status:
        results = [d for d in results if d.get("status") == status]
    results.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)
    return sanitize_db_output(results)


def check_duplicate_document(
    employee_id: str,
    doc_type: str,
    purpose: str,
) -> Optional[Dict[str, Any]]:
    """
    检查员工针对该类型与用途的证明申请是否存在重复：
    1. 在途申请校验 (In-flight check): 员工名下存在相同类型且用途相似的未办结单据（pending / processing）
    2. 政策防重冷静期校验 (Cooldown check - POL-005): 30天内是否已开具相同用途的证明 (completed)
    返回 None 表示合规可发起；否则返回包含拦截原因的字典
    """
    norm_t = normalize_doc_type(doc_type)
    all_docs = query_documents(employee_id=employee_id, doc_type=norm_t)

    # 1. 检查是否存在未办结的在途申请 (In-flight requests)
    for doc in all_docs:
        doc_status = str(doc.get("status") or "").lower()
        if doc_status in ("pending", "processing"):
            if match_document_purpose(purpose, doc.get("purpose", "")):
                created_time = str(doc.get("created_at") or "")[:19]
                return {
                    "is_duplicate": True,
                    "type": "in_flight",
                    "existing_doc": doc,
                    "message": f"您于 {created_time[:10]} 提交的【{norm_t}】（用途：{doc.get('purpose')}，单号：{doc.get('id')}）当前仍在处理中，预计1-2个工作日内办结，无需重复提交申请。"
                }

    # 2. 检查 30 天内是否已开具相同用途（依据 POL-005 规定）
    from datetime import datetime as dt, timedelta
    now_dt = dt.now()
    thirty_days_ago = now_dt - timedelta(days=30)
    for doc in all_docs:
        doc_status = str(doc.get("status") or "").lower()
        if doc_status in ("completed", "approved"):
            if match_document_purpose(purpose, doc.get("purpose", "")):
                ts_str = str(doc.get("completed_at") or doc.get("created_at") or "")
                if ts_str:
                    try:
                        clean_ts = ts_str[:19].replace("T", " ")
                        doc_dt = dt.strptime(clean_ts, "%Y-%m-%d %H:%M:%S") if len(clean_ts) == 19 else dt.strptime(clean_ts[:10], "%Y-%m-%d")
                        if doc_dt >= thirty_days_ago:
                            return {
                                "is_duplicate": True,
                                "type": "cooldown_violation",
                                "existing_doc": doc,
                                "message": f"根据公司《POL-005 证明开具管理规定》第三条，同一用途（{doc.get('purpose')}）30天内不可重复开具【{norm_t}】。您最近已于 {clean_ts[:10]} 开具过单号为 {doc.get('id')} 的证明。如因使馆拒签重递或材料遗失等特殊紧急情况，请提报 HR 服务工单由专员人工复核办理。"
                            }
                    except Exception:
                        pass

    return None



# ============ 会话消息持久化 (Chat Messages Persistence) ============

def save_chat_message(
    message_id: str,
    session_id: str,
    employee_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """持久化保存会话消息"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_messages (id, session_id, employee_id, role, content, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    RETURNING id, session_id, employee_id, role, content, created_at, metadata;
                    """,
                    (message_id, session_id, employee_id, role, content, meta_json)
                )
                res = cur.fetchone()
                conn.commit()
                if res:
                    return sanitize_db_output(dict(res))
    except Exception:
        pass

    item = {
        "id": message_id,
        "session_id": session_id,
        "employee_id": employee_id,
        "role": role,
        "content": content,
        "created_at": now_str,
        "metadata": metadata or {},
    }
    _in_memory_chat_messages.append(item)
    return item


def get_recent_chat_messages(
    employee_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """获取员工或会话最近的对话历史消息"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                where, params = [], []
                if employee_id:
                    where.append("employee_id = %s")
                    params.append(employee_id)
                if session_id:
                    where.append("session_id = %s")
                    params.append(session_id)
                where_clause = ("WHERE " + " AND ".join(where)) if where else ""
                cur.execute(
                    f"""
                    SELECT id, session_id, employee_id, role, content, created_at, metadata
                    FROM chat_messages
                    {where_clause}
                    ORDER BY created_at ASC
                    LIMIT %s;
                    """,
                    (*params, limit)
                )
                rows = cur.fetchall()
                if rows is not None:
                    return sanitize_db_output([dict(r) for r in rows])
    except Exception:
        pass

    results = list(_in_memory_chat_messages)
    if employee_id:
        results = [m for m in results if m.get("employee_id") == employee_id]
    if session_id:
        results = [m for m in results if m.get("session_id") == session_id]
    results.sort(key=lambda x: str(x.get("created_at") or ""))
    return sanitize_db_output(results[-limit:])

