"""Router aggregation."""
from fastapi import APIRouter
from .auth import router as auth_router
from .partners import router as partners_router
from .projects import router as projects_router
from .invoices import router as invoices_router
from .finance import router as finance_router
from .dashboard import router as dashboard_router
from .files import router as files_router
from .subcontractors import router as subcontractors_router
from .taxes import router as taxes_router
from .receipts import router as receipts_router
from .labour import router as labour_router
from .archive import router as archive_router
from .reimbursement import router as reimbursement_router
from .backup import router as backup_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(partners_router)
api_router.include_router(projects_router)
api_router.include_router(invoices_router)
api_router.include_router(finance_router)
api_router.include_router(dashboard_router)
api_router.include_router(files_router)
api_router.include_router(subcontractors_router)
api_router.include_router(taxes_router)
api_router.include_router(receipts_router)
api_router.include_router(labour_router)
api_router.include_router(archive_router)
api_router.include_router(reimbursement_router)
api_router.include_router(backup_router)
