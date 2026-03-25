from handlers.registration import router as reg_router
from handlers.test import router as test_router
from handlers.settings import router as settings_router
from handlers.paid_channels import router as paid_router

__all__ = ["reg_router", "test_router", "settings_router","paid_router"]
