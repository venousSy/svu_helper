"""Domain-level exceptions for the referral/withdrawal system."""

class InsufficientBalanceError(Exception):
    """Raised when a withdrawal amount exceeds the user's available balance."""

class WithdrawalTooSmallError(Exception):
    """Raised when the requested withdrawal is below the 500 SYP minimum."""

class WithdrawalLimitError(Exception):
    """Raised when the user has already submitted a withdrawal today."""
