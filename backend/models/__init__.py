"""All SQLAlchemy models for the engineering management system."""
import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Numeric, Text, Date, DateTime, Boolean, Enum, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from core.database import Base


# ─── Enums ───────────────────────────────────────────────

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"         # 超级管理员
    COMPANY_ADMIN = "company_admin"     # 公司管理员
    FINANCE = "finance"                 # 财务人员
    PROJECT_MANAGER = "project_manager" # 项目负责人
    ATTENDANCE = "attendance"           # 工地考勤员
    WORKER = "worker"                   # 施工人员


class PartnerType(str, enum.Enum):
    OWNER = "业主"              # 甲-纯甲方
    SUPPLIER = "供应商"          # 丙-纯分包
    BOTH = "业主+供应商"         # 乙-双重身份


class ProjectStatus(str, enum.Enum):
    ONGOING = "在建"
    COMPLETED = "已完工"
    PENDING_ACCEPT = "待验收"
    WARRANTY = "质保中"


class InvoiceType(str, enum.Enum):
    B_TO_A = "乙→甲"    # 乙开票给甲
    C_TO_B = "丙→乙"    # 丙开票给乙
    C_TO_A = "丙→甲"    # 丙直接开票给甲


# ─── Mixins ──────────────────────────────────────────────

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantMixin:
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_tenant.id"), nullable=False)


# ─── Tenant & User ──────────────────────────────────────

class Tenant(Base, TimestampMixin):
    __tablename__ = "sys_tenant"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="公司名称")
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="租户编码(乙/丙)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    users: Mapped[List["User"]] = relationship(back_populates="tenant")


class User(Base, TimestampMixin):
    __tablename__ = "sys_user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_tenant.id"), nullable=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="真实姓名")
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.WORKER.value, comment="角色")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    wxpush_uid: Mapped[Optional[str]] = mapped_column(String(100), comment="WxPusher用户UID")
    tenant: Mapped[Optional["Tenant"]] = relationship(back_populates="users")


# ─── Partner (往来单位) ──────────────────────────────────

class Partner(Base, TimestampMixin):
    __tablename__ = "biz_partner"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="单位名称")
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), comment="税号")
    address: Mapped[Optional[str]] = mapped_column(String(300))
    bank_name: Mapped[Optional[str]] = mapped_column(String(200), comment="开户行")
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment="银行账号")
    bank_code: Mapped[Optional[str]] = mapped_column(String(50), comment="联行号")
    contact_person: Mapped[Optional[str]] = mapped_column(String(50), comment="联系人")
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20))
    partner_type: Mapped[str] = mapped_column(String(20), default=PartnerType.OWNER.value, comment="身份标签: 业主/供应商/业主+供应商")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ─── Project (项目) ─────────────────────────────────────

class Project(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_project"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="项目名称")
    project_code: Mapped[Optional[str]] = mapped_column(String(50), comment="项目编号")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="业主(甲/乙)")
    winning_bid_unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="中标单位")
    contract_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="合同金额")
    budget_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="预算金额")
    labor_subcontract_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="劳务分包")
    machinery_rental_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="机械租赁")
    live_working_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="带电作业")
    subcontract_ratio: Mapped[Optional[float]] = mapped_column(Float, comment="分包比例(自动)")
    settlement_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="送审定案金额")
    start_date: Mapped[Optional[date]] = mapped_column(Date, comment="计划开工日期")
    end_date: Mapped[Optional[date]] = mapped_column(Date, comment="计划竣工日期")
    actual_start_date: Mapped[Optional[date]] = mapped_column(Date, comment="实际开工日期")
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date, comment="实际竣工日期")
    contract_sign_date: Mapped[Optional[date]] = mapped_column(Date, comment="合同签订日期")
    status: Mapped[str] = mapped_column(String(20), default=ProjectStatus.ONGOING.value)
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_user.id"), comment="项目负责人")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    # 合同文件关系
    contracts: Mapped[List["ContractFile"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    # 分包单位关系
    subcontractors: Mapped[List["ProjectSubcontractor"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    # 工程计价
    pricing_items: Mapped[List["EngineeringPricing"]] = relationship(back_populates="project", cascade="all, delete-orphan")


# ─── Project-Subcontractor (项目分包关联) ───────────────

class ProjectSubcontractor(Base):
    __tablename__ = "biz_project_subcontractor"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id", ondelete="CASCADE"))
    partner_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="分包单位")
    contract_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="分包合同金额")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    project: Mapped["Project"] = relationship(back_populates="subcontractors")


# ─── Contract File (合同电子档) ─────────────────────────

class ContractFile(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_contract_file"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id", ondelete="CASCADE"))
    partner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_partner.id"), nullable=True, comment="关联分包单位(空=总包合同)")
    filename: Mapped[str] = mapped_column(String(255), comment="原始文件名")
    filepath: Mapped[str] = mapped_column(String(500), comment="存储路径")
    filesize: Mapped[int] = mapped_column(Integer, default=0, comment="文件大小(字节)")
    filetype: Mapped[str] = mapped_column(String(50), default="other", comment="文件类型: contract/invoice/receipt/other")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    project: Mapped["Project"] = relationship(back_populates="contracts")


# ─── Company Seal (公司财务章) ──────────────────────────

class CompanySeal(Base, TimestampMixin):
    __tablename__ = "biz_company_seal"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    seal_name: Mapped[str] = mapped_column(String(100), comment="印章名称")
    file_path: Mapped[str] = mapped_column(String(500), comment="印章图片路径")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")


# ─── Electronic Receipt (电子收据) ──────────────────────

class ElectronicReceipt(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_electronic_receipt"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    receipt_no: Mapped[str] = mapped_column(String(50), unique=True, comment="收据编号")
    payer_name: Mapped[str] = mapped_column(String(200), comment="付款方名称")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), comment="金额")
    amount_words: Mapped[Optional[str]] = mapped_column(String(100), comment="大写金额")
    reason: Mapped[str] = mapped_column(String(500), comment="收款事由")
    receipt_date: Mapped[date] = mapped_column(Date, comment="开票日期")
    seal_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_company_seal.id"), nullable=True, comment="财务章ID")
    status: Mapped[str] = mapped_column(String(20), default="已开具", comment="状态: 已开具/已作废")
    payment_method: Mapped[Optional[str]] = mapped_column(String(20), comment="收款方式: 现金/转账")
    handler: Mapped[Optional[str]] = mapped_column(String(50), comment="经办人")
    approver: Mapped[Optional[str]] = mapped_column(String(50), comment="核准人")
    remark: Mapped[Optional[str]] = mapped_column(Text)


# ─── Staff (施工人员) ───────────────────────────────────

class Staff(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_staff"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    id_card: Mapped[Optional[str]] = mapped_column(String(18), comment="身份证号")
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    bank_card: Mapped[Optional[str]] = mapped_column(String(50), comment="银行卡号")
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), comment="开户行")
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment="银行账号")
    id_photo: Mapped[Optional[str]] = mapped_column(String(500), comment="证件照片")
    work_type: Mapped[Optional[str]] = mapped_column(String(50), comment="工种")
    daily_wage: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), comment="日薪")
    commission_rate: Mapped[Optional[float]] = mapped_column(Float, comment="提成比例")
    advance_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="预支借款余额")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True, comment="关联用户ID")


# ─── Work Hours (工时) ───────────────────────────────────

class WorkHour(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_work_hours"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_staff.id"))
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_project.id"), nullable=True, comment="项目")
    work_date: Mapped[date] = mapped_column(Date)
    hours: Mapped[float] = mapped_column(Float, default=8.0, comment="工时")
    position_title: Mapped[Optional[str]] = mapped_column(String(100), comment="临时职务")
    attendance_subsidy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0, comment="出工补助")
    meal_allowance: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0, comment="饭补")
    heat_subsidy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0, comment="高温补贴")
    weather_subsidy: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0, comment="天气补贴")
    daily_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=0, comment="日合计")
    content: Mapped[Optional[str]] = mapped_column(Text, comment="工作内容")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_user.id"), nullable=True, comment="创建人")


# ─── Engineering Pricing (工程计价) ──────────────────────────

class EngineeringPricing(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_engineering_pricing"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"), comment="关联项目")
    item_name: Mapped[str] = mapped_column(String(200), comment="单项工程名称")
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="金额")
    pricing_date: Mapped[Optional[date]] = mapped_column(Date, comment="计价日期")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    # 项目关系
    project: Mapped["Project"] = relationship(back_populates="pricing_items")


# ─── Salary (薪酬) ───────────────────────────────────────

class Salary(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_salary"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_staff.id"))
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_project.id"), nullable=True, comment="项目")
    salary_month: Mapped[str] = mapped_column(String(7), comment="薪酬月份 YYYY-MM")
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="基础工资")
    hourly_wage: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="工时工资")
    insurance_fund: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="五险一金")
    project_bonus: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="项目提成")
    net_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, comment="实发金额")
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ─── Invoice Out (销项发票) ─────────────────────────────

class InvoiceOut(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_invoice_out"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"))
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="收票单位")
    invoice_type: Mapped[str] = mapped_column(String(10), comment="开票类型: 乙→甲/丙→乙/丙→甲")
    invoice_no: Mapped[Optional[str]] = mapped_column(String(50), comment="发票号码")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), comment="开票金额(含税)")
    amount_excluding_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="不含税金额")
    tax_rate: Mapped[Optional[float]] = mapped_column(Float, comment="税率(%)")
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="税额")
    amount_including_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="含税金额")
    invoice_date: Mapped[Optional[date]] = mapped_column(Date, comment="开票日期")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="发票扫描件路径")


# ─── Invoice In (进项发票) ──────────────────────────────

class InvoiceIn(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_invoice_in"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"))
    issuer_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="开票单位(丙)")
    invoice_no: Mapped[Optional[str]] = mapped_column(String(50))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), comment="金额(含税)")
    amount_excluding_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="不含税金额")
    tax_rate: Mapped[Optional[float]] = mapped_column(Float)
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="税额")
    amount_including_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="含税金额")
    actual_tax_received: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), comment="实收税金")
    invoice_date: Mapped[Optional[date]]
    is_deductible: Mapped[bool] = mapped_column(Boolean, default=True, comment="可抵扣")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))


# ─── Payment (回款/付款) ─────────────────────────────────

class Receipt(Base, TimestampMixin, TenantMixin):
    """回款登记（甲方打款）"""
    __tablename__ = "biz_receipt"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"))
    invoice_out_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_invoice_out.id"))
    payer_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="付款方")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    receipt_date: Mapped[date]
    receipt_type: Mapped[str] = mapped_column(String(20), default="银行转账", comment="回款方式")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="回单附件")


class Payment(Base, TimestampMixin, TenantMixin):
    """付款登记（对外付款）"""
    __tablename__ = "biz_payment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"))
    payee_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_partner.id"), comment="收款方")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_date: Mapped[date]
    payment_type: Mapped[str] = mapped_column(String(20), default="对公付款", comment="付款方式")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="付款凭证")


# ─── Cost Record (成本记录) ─────────────────────────────

class CostRecord(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_cost"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_project.id"))
    cost_type: Mapped[str] = mapped_column(String(50), comment="成本类型: 分包/人工/材料/杂费")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    cost_date: Mapped[date]
    remark: Mapped[Optional[str]] = mapped_column(Text)


# ─── Audit Log (审计日志) ───────────────────────────────

class AuditLog(Base):
    __tablename__ = "sys_audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(100), comment="操作动作")
    biz_type: Mapped[Optional[str]] = mapped_column(String(50), comment="业务类型")
    biz_id: Mapped[Optional[int]] = mapped_column(Integer)
    detail: Mapped[Optional[dict]] = mapped_column(JSON, comment="变更详情")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Notification (消息通知) ────────────────────────────

class Notification(Base):
    __tablename__ = "biz_notification"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    notify_type: Mapped[str] = mapped_column(String(50), comment="payment_due/invoice_missing/salary_ready")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    biz_type: Mapped[Optional[str]] = mapped_column(String(50))
    biz_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Approval (审批流) ──────────────────────────────────

class Approval(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_approval"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    biz_type: Mapped[str] = mapped_column(String(50), comment="payment/salary/project")
    biz_id: Mapped[int] = mapped_column(Integer, comment="关联业务ID")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="pending/approved/rejected")
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    total_level: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"))


class ApprovalLog(Base):
    __tablename__ = "biz_approval_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_id: Mapped[int] = mapped_column(Integer, ForeignKey("biz_approval.id"))
    approver_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"))
    level: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20), comment="approve/reject")
    comment: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ─── Tax Record (税金缴纳记录) ─────────────────────────

class TaxRecord(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_tax_record"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("biz_project.id"), nullable=True, comment="关联项目")
    unit_name: Mapped[Optional[str]] = mapped_column(String(200), comment="单位名称")
    tax_type: Mapped[str] = mapped_column(String(50), comment="税种: 增值税/企业所得税/附加税/印花税/个税/其他")
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), comment="金额")
    tax_period: Mapped[str] = mapped_column(String(7), comment="所属期 YYYY-MM")
    period_type: Mapped[str] = mapped_column(String(10), default="月度", comment="缴纳周期: 月度/季度/年度")
    due_date: Mapped[Optional[date]] = mapped_column(Date, comment="缴纳期限")
    paid_date: Mapped[Optional[date]] = mapped_column(Date, comment="实际缴纳日期")
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否已缴纳")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="缴税凭证")
    remark: Mapped[Optional[str]] = mapped_column(Text)


# ─── Electronic Archive (电子档案) ─────────────────────

class ElectronicArchive(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_archive"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True, comment="文件/目录名")
    directory: Mapped[str] = mapped_column(String(500), default="/", comment="所在目录路径")
    is_directory: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否为目录")
    file_type: Mapped[Optional[str]] = mapped_column(String(100), comment="文件类型(MIME)")
    file_size: Mapped[Optional[int]] = mapped_column(Integer, comment="文件大小(字节)")
    file_path: Mapped[Optional[str]] = mapped_column(String(500), comment="存储路径")
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), comment="原始文件名")


# ─── Reimbursement (报销) ─────────────────────────────

class Reimbursement(Base, TimestampMixin, TenantMixin):
    __tablename__ = "biz_reimbursement"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_user.id"), comment="提交人")
    applicant: Mapped[str] = mapped_column(String(50), comment="报销人")
    expense_type: Mapped[str] = mapped_column(String(20), default="其他", comment="报销类型: 交通费/餐饮费/办公用品/差旅费/其他")
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), comment="报销金额")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="费用说明")
    receipt_urls: Mapped[Optional[str]] = mapped_column(Text, comment="凭证附件(JSON数组)")
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), comment="开户行")
    bank_account: Mapped[Optional[str]] = mapped_column(String(50), comment="银行账号")
    status: Mapped[str] = mapped_column(String(10), default="待审核", comment="审核状态: 待审核/已通过/已驳回/已付款")
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_user.id"), comment="审核人")
    review_remark: Mapped[Optional[str]] = mapped_column(String(500), comment="审核备注")
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="审核时间")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="付款时间")
