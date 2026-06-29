"""
Common enumerations used across the backtesting framework.

Keeping these enums in one place ensures
consistent values throughout the project.
"""

from enum import Enum


class OptionType(str, Enum):
    """Type of option contract."""

    CALL = "CE"
    PUT = "PE"


class OrderAction(str, Enum):
    """Supported trading actions."""

    BUY = "BUY"
    SELL = "SELL"


class PositionStatus(str, Enum):
    """Lifecycle state of a position."""

    OPEN = "OPEN"
    CLOSED = "CLOSED"


class InstrumentType(str, Enum):
    """Tradable instrument categories."""

    OPTION = "OPTION"
    FUTURE = "FUTURE"


class Underlying(str, Enum):
    """Supported underlying indices."""

    NIFTY = "NIFTY"
    BANKNIFTY = "BANKNIFTY"
    FINNIFTY = "FINNIFTY"


class LogLevel(str, Enum):
    """Application log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ValidationSeverity(str, Enum):
    """Severity assigned to validation messages."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"