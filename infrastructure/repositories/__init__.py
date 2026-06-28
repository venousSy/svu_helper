# Re-exporting all repositories to maintain backwards compatibility
from .project import ProjectRepository
from .payment import PaymentRepository
from .stats import StatsRepository
from .settings import SettingsRepository
from .ticket import TicketRepository
from .audit import AuditRepository
from .matchmaking import TeamRequestRepository
from .student_repo import StudentRepository
from .user_referral import UserReferralRepository

__all__ = [
    "ProjectRepository",
    "PaymentRepository",
    "StatsRepository",
    "SettingsRepository",
    "TicketRepository",
    "AuditRepository",
    "TeamRequestRepository",
    "StudentRepository",
    "UserReferralRepository",
]
