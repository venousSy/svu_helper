from aiogram import Router

from .submission import router as submission_router
from .payment import router as payment_router
from .views import router as views_router
from .tickets import router as tickets_router
from .peer_routes import router as peer_router

router = Router()

router.include_router(submission_router)
router.include_router(payment_router)
router.include_router(views_router)
router.include_router(tickets_router)
router.include_router(peer_router)
