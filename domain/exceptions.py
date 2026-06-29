"""Domain-level exceptions for the referral/withdrawal system."""

class InsufficientBalanceError(Exception):
    """Raised when a withdrawal amount exceeds the user's available balance."""

class WithdrawalTooSmallError(Exception):
    """Raised when the requested withdrawal is below the 500 SYP minimum."""

class WithdrawalTooLargeError(Exception):
    """Raised when the requested withdrawal exceeds the maximum allowed amount."""

class WithdrawalAmountInvalidError(Exception):
    """Raised when the withdrawal amount is zero or negative."""

class WithdrawalLimitError(Exception):
    """Raised when the user has already submitted a withdrawal today."""
