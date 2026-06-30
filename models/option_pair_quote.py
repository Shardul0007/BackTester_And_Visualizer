"""
Represents both option quotes available at a strike.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.option_quote import OptionQuote


@dataclass(slots=True)
class OptionPairQuote:
    """
    Holds the call and put quote for a strike.
    """

    call: OptionQuote

    put: OptionQuote