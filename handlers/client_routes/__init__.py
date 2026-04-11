from aiogram import Router

from .submission import router as submission_router
from .payment import router as payment_router
from .views import router as views_router

router = Router()

router.include_router(submission_router)
router.include_router(payment_router)
router.include_router(views_router)
