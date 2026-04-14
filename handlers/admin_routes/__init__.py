from aiogram import Router

from .broadcast import router as broadcast_router
from .dashboard import router as dashboard_router
from .offers import router as offers_router
from .payments import router as payments_router
from .tickets import router as tickets_router
from .views import router as views_router

router = Router()

# Ticket handler FIRST — catches forum topic messages before other handlers
router.include_router(tickets_router)
router.include_router(dashboard_router)
router.include_router(views_router)
router.include_router(offers_router)
router.include_router(payments_router)
router.include_router(broadcast_router)
