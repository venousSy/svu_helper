"""
Application Services – Payment Lifecycle
==========================================
Services covering the full payment flow: submission by the student,
confirmation by the admin, and rejection (reset so the student can retry).

Result dataclasses carry all the data handlers need to send Telegram
notifications, without the services knowing anything about aiogram.
"""
from dataclasses import dataclass
from typing import Optional

from domain.enums import PaymentStatus, ProjectStatus
from infrastructure.repositories import PaymentRepository, ProjectRepository


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class SubmitPaymentResult:
    """Returned after a student submits a receipt."""
    payment_id: int
    proj_id: int
    file_id: str
    file_type: Optional[str]


@dataclass
class PaymentActionResult:
    """Returned after an admin confirms or rejects a payment."""
    payment_id: int
    proj_id: int
    user_id: int
    subject: str  # raw, not escaped


# ---------------------------------------------------------------------------
# SubmitPaymentService
# ---------------------------------------------------------------------------

class SubmitPaymentService:
    """
    Persists a payment receipt and advances the project status to
    AWAITING_VERIFICATION.

    Raises:
        ValueError: if proj_id is missing from FSM data.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._project_repo = project_repo
        self._payment_repo = payment_repo

    async def execute(
        self,
        proj_id: int,
        user_id: int,
        file_id: str,
        file_type: Optional[str],
    ) -> SubmitPaymentResult:
        if not proj_id:
            raise ValueError("No active project for payment – missing FSM state.")

        payment_id = await self._payment_repo.add_payment(
            proj_id, user_id, file_id, file_type=file_type
        )
        await self._project_repo.update_status(proj_id, ProjectStatus.AWAITING_VERIFICATION)

        return SubmitPaymentResult(
            payment_id=payment_id,
            proj_id=proj_id,
            file_id=file_id,
            file_type=file_type,
        )


# ---------------------------------------------------------------------------
# ConfirmPaymentService
# ---------------------------------------------------------------------------

class ConfirmPaymentService:
    """
    Marks a payment Accepted and advances the project to Accepted (ongoing).

    Raises:
        ValueError: if payment_id not found.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._project_repo = project_repo
        self._payment_repo = payment_repo

    async def execute(self, payment_id: int) -> PaymentActionResult:
        payment = await self._payment_repo.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment #{payment_id} not found.")

        proj_id = payment["project_id"]
        await self._payment_repo.update_status(payment_id, PaymentStatus.ACCEPTED)
        await self._project_repo.update_status(proj_id, ProjectStatus.ACCEPTED)

        project = await self._project_repo.get_project_by_id(proj_id)
        return PaymentActionResult(
            payment_id=payment_id,
            proj_id=proj_id,
            user_id=project["user_id"],
            subject=project.get("subject_name", ""),
        )


# ---------------------------------------------------------------------------
# RejectPaymentService
# ---------------------------------------------------------------------------

class RejectPaymentService:
    """
    Marks a payment Rejected and resets the project back to OFFERED so the
    student can upload a correct receipt.

    Raises:
        ValueError: if payment_id not found.
    """

    def __init__(
        self,
        project_repo: ProjectRepository,
        payment_repo: PaymentRepository,
    ) -> None:
        self._project_repo = project_repo
        self._payment_repo = payment_repo

    async def execute(self, payment_id: int) -> PaymentActionResult:
        payment = await self._payment_repo.get_payment(payment_id)
        if not payment:
            raise ValueError(f"Payment #{payment_id} not found.")

        proj_id = payment["project_id"]
        await self._payment_repo.update_status(payment_id, PaymentStatus.REJECTED)
        # Reset to OFFERED so student can re-upload
        await self._project_repo.update_status(proj_id, ProjectStatus.OFFERED)

        project = await self._project_repo.get_project_by_id(proj_id)
        return PaymentActionResult(
            payment_id=payment_id,
            proj_id=proj_id,
            user_id=project["user_id"] if project else 0,
            subject=project.get("subject_name", "") if project else "",
        )
