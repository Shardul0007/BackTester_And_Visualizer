"""
Validation utilities for normalized market data.
"""

from __future__ import annotations

import pandas as pd

from models.enums import ValidationSeverity
from models.validation import ValidationResult


class DataValidator:
    """Validates normalized market data."""

    REQUIRED_COLUMNS = {
        "Date",
        "Time",
        "Timestamp",
        "Price",
        "Volume",
        "OpenInterest",
    }

    @classmethod
    def validate(
        cls,
        dataframe: pd.DataFrame,
    ) -> ValidationResult:

        result = ValidationResult()

        cls._validate_schema(dataframe, result)
        cls._validate_missing_values(dataframe, result)
        cls._validate_prices(dataframe, result)
        cls._validate_timestamp_order(dataframe, result)
        cls._validate_duplicates(dataframe, result)

        return result

    @classmethod
    def _validate_schema(
        cls,
        dataframe: pd.DataFrame,
        result: ValidationResult,
    ) -> None:

        missing = cls.REQUIRED_COLUMNS.difference(dataframe.columns)

        if missing:
            result.add_issue(
                ValidationSeverity.ERROR,
                f"Missing columns: {sorted(missing)}",
            )

    @staticmethod
    def _validate_missing_values(
        dataframe: pd.DataFrame,
        result: ValidationResult,
    ) -> None:

        if dataframe.isnull().any().any():
            result.add_issue(
                ValidationSeverity.ERROR,
                "Dataset contains missing values.",
            )

    @staticmethod
    def _validate_prices(
        dataframe: pd.DataFrame,
        result: ValidationResult,
    ) -> None:

        if (dataframe["Price"] <= 0).any():
            result.add_issue(
                ValidationSeverity.ERROR,
                "Non-positive prices detected.",
            )

    @staticmethod
    def _validate_timestamp_order(
        dataframe: pd.DataFrame,
        result: ValidationResult,
    ) -> None:

        if not dataframe["Timestamp"].is_monotonic_increasing:
            result.add_issue(
                ValidationSeverity.ERROR,
                "Timestamps are not ordered chronologically.",
            )

    @staticmethod
    def _validate_duplicates(
        dataframe: pd.DataFrame,
        result: ValidationResult,
    ) -> None:

        duplicate_count = dataframe["Timestamp"].duplicated().sum()

        if duplicate_count:
            result.add_issue(
                ValidationSeverity.WARNING,
                f"{duplicate_count} duplicate timestamps detected.",
            )