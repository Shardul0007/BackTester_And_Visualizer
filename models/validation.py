"""
Models used by the data validation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.enums import ValidationSeverity


@dataclass(slots=True)
class ValidationIssue:
    """Represents a single validation finding."""

    severity: ValidationSeverity
    message: str


@dataclass(slots=True)
class ValidationResult:
    """Aggregates all validation findings."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(
            issue.severity == ValidationSeverity.ERROR
            for issue in self.issues
        )

    def add_issue(
        self,
        severity: ValidationSeverity,
        message: str,
    ) -> None:
        self.issues.append(
            ValidationIssue(
                severity=severity,
                message=message,
            )
        )