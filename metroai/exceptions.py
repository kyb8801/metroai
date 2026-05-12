"""MetroAI custom exception hierarchy.

박수연(MetroAI advisor) 통합. 코드 품질 강화.
v0.5.0 → v0.6.0 신규 모듈.
"""

from __future__ import annotations


# ============================================================
# Base
# ============================================================

class MetroAIError(Exception):
    """All MetroAI exceptions inherit from this base."""


# ============================================================
# Input / Validation errors
# ============================================================

class UserInputError(MetroAIError):
    """사용자 입력 검증 실패."""


class InvalidDistributionError(UserInputError):
    """지원하지 않는 분포."""
    SUPPORTED = ("normal", "rectangular", "triangular", "u_shape")

    def __init__(self, distribution: str):
        super().__init__(
            f"Unsupported distribution: '{distribution}'. "
            f"Supported: {', '.join(self.SUPPORTED)}."
        )


class InsufficientRepeatsError(UserInputError):
    """반복 측정 부족 (Type A)."""
    def __init__(self, n: int, required: int = 2):
        super().__init__(
            f"Type A uncertainty requires ≥{required} repeated measurements; "
            f"got {n}."
        )


class NegativeUncertaintyError(UserInputError):
    """음수 불확도."""
    def __init__(self, name: str, value: float):
        super().__init__(f"Negative uncertainty in '{name}': {value}.")


# ============================================================
# Domain / Math errors
# ============================================================

class DomainError(MetroAIError):
    """측정 도메인 룰 위반."""


class IllPosedInverseError(DomainError):
    """역설계 ill-posed (target unc < theoretical floor)."""
    def __init__(self, target: float, floor: float):
        super().__init__(
            f"Target u_c={target:.4g} below theoretical floor {floor:.4g}. "
            f"No valid input tolerance vector exists."
        )


class SympyParseError(DomainError):
    """Sympy model parsing 실패."""
    def __init__(self, model: str, reason: str):
        super().__init__(f"Cannot parse model '{model}': {reason}")


class StandardComplianceError(DomainError):
    """ISO·KOLAS 표준 부적합."""
    def __init__(self, standard: str, reason: str):
        super().__init__(f"{standard} compliance violation: {reason}")


# ============================================================
# Math computation errors
# ============================================================

class MathError(MetroAIError):
    """수치 계산 실패."""


class ConvergenceError(MathError):
    """반복 알고리즘 수렴 실패 (MCM·optimization)."""
    def __init__(self, algo: str, n_iter: int, tol: float):
        super().__init__(
            f"{algo} did not converge after {n_iter} iterations (tol={tol})."
        )


class DivisionByZeroError(MathError):
    """0으로 나눔."""
    def __init__(self, context: str):
        super().__init__(f"Division by zero in: {context}")


# ============================================================
# Infrastructure errors
# ============================================================

class InfraError(MetroAIError):
    """DB·API·file system 실패."""


class AuditLogError(InfraError):
    """Audit log write/read 실패."""
    def __init__(self, audit_id: str, reason: str):
        super().__init__(f"Audit log failure (id={audit_id[:8]}...): {reason}")


class DatabaseError(InfraError):
    """DB query·migration 실패."""


# ============================================================
# Export errors
# ============================================================

class ExportError(MetroAIError):
    """PDF·Excel·DCC export 실패."""


class PDFGenerationError(ExportError):
    """PDF 생성 실패."""


class DCCSchemaError(ExportError):
    """Digital Calibration Certificate schema 위반."""
