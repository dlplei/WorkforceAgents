"""
HR 系统适配层 (HR Adapter Pattern)
支持本地 PostgreSQL 与企业级 ServiceNow (Table API)
"""
from abc import ABC, abstractmethod
import os
import random
import datetime
from typing import Optional, List, Dict, Any
import httpx

from db import database


class IHRServiceAdapter(ABC):
    """HR 服务统一适配器抽象基类"""

    @abstractmethod
    def get_employee_profile(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """获取员工个人档案"""
        pass

    @abstractmethod
    def get_leave_balance(self, employee_id: str) -> Dict[str, int]:
        """获取员工假期余额"""
        pass

    @abstractmethod
    def check_calendar_conflicts(self, employee_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """检查日程与假期排期冲突"""
        pass

    @abstractmethod
    def submit_leave_request(
        self,
        employee_id: str,
        applicant: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
        approver: str
    ) -> Dict[str, Any]:
        """提交休假审批申请"""
        pass

    @abstractmethod
    def get_approvals(self, employee_id: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询审批流状态"""
        pass

    @abstractmethod
    def create_ticket(
        self,
        employee_id: str,
        applicant: str,
        category: str,
        title: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """提交 HR 服务工单"""
        pass

    @abstractmethod
    def get_tickets(self, employee_id: str, ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """查询 HR 工单进度"""
        pass


class LocalPostgresAdapter(IHRServiceAdapter):
    """基于本地 PostgreSQL 的 HR 适配实现"""

    def get_employee_profile(self, employee_id: str) -> Optional[Dict[str, Any]]:
        emp = database.get_employee(employee_id)
        return emp.model_dump() if emp else None

    def get_leave_balance(self, employee_id: str) -> Dict[str, int]:
        return database.get_leave_balance(employee_id)

    def check_calendar_conflicts(self, employee_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        return database.check_calendar_conflicts(employee_id, start_date, end_date)

    def submit_leave_request(
        self,
        employee_id: str,
        applicant: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
        approver: str
    ) -> Dict[str, Any]:
        req_id = f"APR-{random.randint(100, 999)}"
        today_str = datetime.date.today().isoformat()
        return database.create_approval(
            approval_id=req_id,
            employee_id=employee_id,
            applicant=applicant,
            approval_type=leave_type,
            status="pending",
            request_date=today_str,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            approver=approver
        )

    def get_approvals(self, employee_id: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return database.query_approvals(employee_id, request_id)

    def create_ticket(
        self,
        employee_id: str,
        applicant: str,
        category: str,
        title: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        ticket_id = f"TICK-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        return database.create_hr_ticket(
            ticket_id=ticket_id,
            employee_id=employee_id,
            applicant=applicant,
            category=category,
            title=title,
            description=description,
            priority=priority
        )

    def get_tickets(self, employee_id: str, ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return database.query_hr_tickets(employee_id, ticket_id)



class ServiceNowAdapter(IHRServiceAdapter):
    """
    企业级 ServiceNow HR Service Delivery / Table API 适配器
    支持向 ServiceNow 实例发起 Incident / HR Case 请求，并降级同步至本地数据库
    """

    def __init__(self):
        self.instance = os.getenv("SERVICENOW_INSTANCE", "")  # 例如 dev12345.service-now.com
        self.user = os.getenv("SERVICENOW_USER", "admin")
        self.password = os.getenv("SERVICENOW_PASSWORD", "")
        self.local_backup = LocalPostgresAdapter()

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_employee_profile(self, employee_id: str) -> Optional[Dict[str, Any]]:
        # 员工基本资料从本地系统读取
        return self.local_backup.get_employee_profile(employee_id)

    def get_leave_balance(self, employee_id: str) -> Dict[str, int]:
        return self.local_backup.get_leave_balance(employee_id)

    def check_calendar_conflicts(self, employee_id: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        return self.local_backup.check_calendar_conflicts(employee_id, start_date, end_date)

    def submit_leave_request(
        self,
        employee_id: str,
        applicant: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        reason: str,
        approver: str
    ) -> Dict[str, Any]:
        # 始终同步记录到本地数据库
        local_approval = self.local_backup.submit_leave_request(
            employee_id, applicant, leave_type, start_date, end_date, reason, approver
        )
        return local_approval

    def get_approvals(self, employee_id: str, request_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.local_backup.get_approvals(employee_id, request_id)

    def create_ticket(
        self,
        employee_id: str,
        applicant: str,
        category: str,
        title: str,
        description: str,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        external_id = None
        # 如果配置了 ServiceNow 实例且有密码，尝试调用 ServiceNow Table API
        if self.instance and self.password:
            try:
                base_url = f"https://{self.instance}/api/now/table/incident"
                priority_map = {"low": "3", "medium": "2", "high": "1", "urgent": "1"}
                payload = {
                    "short_description": f"[{category}] {title}",
                    "description": f"申请人: {applicant} (ID: {employee_id})\n内容: {description}",
                    "urgency": priority_map.get(priority, "2"),
                    "caller_id": applicant
                }
                with httpx.Client(timeout=5.0, trust_env=False) as client:
                    resp = client.post(
                        base_url,
                        json=payload,
                        auth=(self.user, self.password),
                        headers=self._get_headers()
                    )
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        external_id = data.get("result", {}).get("number")
            except Exception as e:
                print(f"[ServiceNowAdapter] API push failed, fallback to local DB: {e}")

        # 同时持久化至本地 PostgreSQL，并记录外部 ServiceNow 编号
        ticket_id = f"TICK-{datetime.date.today().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        return database.create_hr_ticket(
            ticket_id=ticket_id,
            employee_id=employee_id,
            applicant=applicant,
            category=category,
            title=title,
            description=description,
            priority=priority,
            external_system_id=external_id
        )

    def get_tickets(self, employee_id: str, ticket_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.local_backup.get_tickets(employee_id, ticket_id)


def get_hr_adapter() -> IHRServiceAdapter:
    """HR 适配器工厂函数"""
    adapter_type = os.getenv("HR_ADAPTER_TYPE", "local").lower()
    if adapter_type == "servicenow":
        return ServiceNowAdapter()
    return LocalPostgresAdapter()

