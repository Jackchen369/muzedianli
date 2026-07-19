"""Pydantic schemas for API request/response validation."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Auth ────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    display_name: str
    role: str
    tenant_id: Optional[int] = None

class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    phone: Optional[str] = None
    role: str = "worker"
    tenant_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    tenant_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None


class PasswordReset(BaseModel):
    new_password: str


# ─── Partner ─────────────────────────────────────────────

class PartnerCreate(BaseModel):
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_code: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    partner_type: str = "业主"

class PartnerResponse(PartnerCreate):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Project ─────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    project_code: Optional[str] = None
    owner_id: int
    winning_bid_unit_id: Optional[int] = None
    contract_amount: Optional[Decimal] = None
    budget_amount: Optional[Decimal] = None
    labor_subcontract_amount: Optional[Decimal] = None
    machinery_rental_amount: Optional[Decimal] = None
    live_working_amount: Optional[Decimal] = None
    subcontract_ratio: Optional[float] = None
    settlement_amount: Optional[Decimal] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    contract_sign_date: Optional[date] = None
    manager_id: Optional[int] = None
    status: str = "在建"
    remark: Optional[str] = None

class ProjectResponse(ProjectCreate):
    id: int
    tenant_id: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    revenue_amount: Optional[float] = None
    unpaid_amount: Optional[float] = None
    owner_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Invoice Out ─────────────────────────────────────────

class InvoiceOutCreate(BaseModel):
    project_id: int
    receiver_id: int
    invoice_type: str
    invoice_no: Optional[str] = None
    amount: Decimal
    amount_excluding_tax: Optional[Decimal] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[Decimal] = None
    amount_including_tax: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    file_path: Optional[str] = None
    remark: Optional[str] = None

class InvoiceOutResponse(InvoiceOutCreate):
    id: int
    tenant_id: int
    tax_amount: Optional[Decimal] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Invoice In ──────────────────────────────────────────

class InvoiceInCreate(BaseModel):
    project_id: int
    issuer_id: int
    invoice_no: Optional[str] = None
    amount: Decimal
    amount_excluding_tax: Optional[Decimal] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[Decimal] = None
    amount_including_tax: Optional[Decimal] = None
    actual_tax_received: Optional[Decimal] = None
    invoice_date: Optional[date] = None
    is_deductible: bool = True
    file_path: Optional[str] = None
class InvoiceInResponse(InvoiceInCreate):
    id: int
    tenant_id: int
    is_deductible: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Receipt/Payment ─────────────────────────────────────

class ReceiptCreate(BaseModel):
    project_id: int
    invoice_out_id: Optional[int] = None
    payer_id: int
    amount: Decimal
    receipt_date: date
    receipt_type: str = "银行转账"

class ReceiptResponse(ReceiptCreate):
    id: int
    tenant_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class PaymentCreate(BaseModel):
    project_id: int
    payee_id: int
    amount: Decimal
    payment_date: date
    payment_type: str = "对公付款"

class PaymentResponse(PaymentCreate):
    id: int
    tenant_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Engineering Pricing ─────────────────────────────

class EngineeringPricingCreate(BaseModel):
    project_id: int
    item_name: str
    amount: Optional[Decimal] = None
    pricing_date: Optional[date] = None
    category: str = "主体业务"
    remark: Optional[str] = None

class EngineeringPricingResponse(EngineeringPricingCreate):
    id: int
    tenant_id: int
    is_approved: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─── Dashboard ───────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_revenue: Decimal = Decimal("0.00")
    total_receivable: Decimal = Decimal("0.00")
    total_payable: Decimal = Decimal("0.00")
    total_invoice_out: Decimal = Decimal("0.00")
    project_count: int = 0
    staff_count: int = 0


# ─── Audit Log ───────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    username: Optional[str] = None
    action: str
    biz_type: Optional[str] = None
    detail: Optional[dict] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
