"""
企业员工 RBAC 角色与权限计算服务
消除业务各层散落的姓名、工号与硬编码角色判定
"""
from typing import Any, Dict, Optional, Set, Union
from models import EmployeeProfile, SystemRole


class PermissionService:
    """集中式员工权限与角色判定服务"""

    @staticmethod
    def _extract_field(emp: Any, field: str, default: Any = "") -> Any:
        """从 EmployeeProfile 或 dict 中安全提取属性"""
        if emp is None:
            return default
        if isinstance(emp, dict):
            return emp.get(field, default)
        return getattr(emp, field, default)

    @classmethod
    def get_employee_roles(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> Set[str]:
        """
        获取员工拥有的所有系统角色集合（标准化全小写）
        优先从员工实体的 roles 属性读取，无显式 roles 时基于岗位与职级规则智能判定
        """
        roles: Set[str] = {SystemRole.EMPLOYEE.value}
        if not emp:
            return roles

        explicit_roles = cls._extract_field(emp, "roles", None)
        if explicit_roles and isinstance(explicit_roles, (list, tuple, set)):
            for r in explicit_roles:
                if r:
                    roles.add(str(r).lower())

        # 无论是否有显式 roles，结合岗位特征做安全兜底推导（保证向前与向后兼容）
        level = str(cls._extract_field(emp, "level", "")).strip().upper()
        department = str(cls._extract_field(emp, "department", "")).strip()
        position = str(cls._extract_field(emp, "position", "")).strip()
        emp_id = str(cls._extract_field(emp, "id", "")).strip()

        # 1. 管理层 / 直属主管 (Manager)
        if (
            level.startswith("M")
            or "总监" in position
            or "主管" in position
            or "VP" in position
            or "管理层" in department
        ):
            roles.add(SystemRole.MANAGER.value)

        # 2. 财务复核 / 专员 (Finance)
        if (
            "财务" in department
            or "财务" in position
            or "报销审核" in position
            or "核销" in position
        ):
            roles.add(SystemRole.FINANCE.value)

        # 3. 业务人力资源伙伴 (HRBP) 与 HR
        if "HRBP" in position or "HRBP" in department:
            roles.add(SystemRole.HRBP.value)
            roles.add(SystemRole.HR.value)
        elif (
            "HR" in department
            or "HR" in position
            or "人力资源" in department
            or "招聘" in position
            or "员工关系" in position
        ):
            roles.add(SystemRole.HR.value)

        # 4. 高管与管理员 (Admin)
        if level in ("M2", "M3", "M4") or "VP" in position or department == "管理层":
            roles.add(SystemRole.ADMIN.value)

        return roles

    @classmethod
    def is_manager(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> bool:
        """是否为主管/管理人员"""
        return SystemRole.MANAGER.value in cls.get_employee_roles(emp)

    @classmethod
    def is_hr(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> bool:
        """是否为 HR 人员 (包含 HRBP)"""
        roles = cls.get_employee_roles(emp)
        return (SystemRole.HR.value in roles) or (SystemRole.HRBP.value in roles)

    @classmethod
    def is_hrbp(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> bool:
        """是否为对口业务 HRBP"""
        return SystemRole.HRBP.value in cls.get_employee_roles(emp)

    @classmethod
    def is_finance(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> bool:
        """是否为财务审核人员"""
        return SystemRole.FINANCE.value in cls.get_employee_roles(emp)

    @classmethod
    def is_admin(cls, emp: Union[EmployeeProfile, Dict[str, Any], None]) -> bool:
        """是否为系统管理员/VP高管"""
        return SystemRole.ADMIN.value in cls.get_employee_roles(emp)

    @classmethod
    def determine_approval_scope(
        cls,
        emp: Union[EmployeeProfile, Dict[str, Any], None],
        requested_scope: Optional[str] = None,
        status: Optional[str] = None,
        applicant_name: Optional[str] = None,
    ) -> str:
        """
        根据当前用户角色动态推导审批查询的数据视野范围 (Scope)
        - finance: 财务报销及复核单据视野
        - hr: 人事、证明及调动单据视野
        - my_approvals: 主管下属待办及审批经办流水视野
        - all: 管理层全局单据视野
        - my_requests: 普通员工本人单据视野
        """
        if requested_scope:
            return requested_scope

        is_fin = cls.is_finance(emp)
        is_hr_role = cls.is_hr(emp)
        is_mgr_role = cls.is_manager(emp)

        if is_hr_role:
            return "hr"
        if is_fin:
            return "finance"
        if is_mgr_role:
            if status or applicant_name:
                return "my_approvals"
            return "all"
        return "my_requests"

    @classmethod
    def can_access_target_employee(
        cls,
        current_emp: Union[EmployeeProfile, Dict[str, Any], None],
        target_emp_id: Optional[str],
        tool_name: str = "",
    ) -> bool:
        """
        RBAC 细粒度数据鉴权：
        普通员工仅限查询与操作本人数据；
        业务主管、HRBP 及专门审批类工具允许放行跨工号访问。
        """
        if not target_emp_id:
            return True

        current_id = str(cls._extract_field(current_emp, "id", "")).strip()
        target_id = str(target_emp_id).strip()

        if current_id == target_id:
            return True

        # 白名单放行免校验操作（如审批人查看单据、处理待办）
        if tool_name in ("review_approval_request", "query_pending_approvals"):
            return True

        # 管理者或 HRBP 放行
        return cls.is_manager(current_emp) or cls.is_hrbp(current_emp)
