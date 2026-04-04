"""측정 모델 처리 모듈.

사용자가 입력한 측정 모델식 Y = f(X₁, X₂, ..., Xₙ)을 파싱하고,
sympy를 이용하여 각 입력량에 대한 편미분(민감계수)을 자동 계산.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import sympy
from sympy import Symbol, sympify, diff, latex


@dataclass
class MeasurementModel:
    """측정 모델을 나타내는 클래스.

    Attributes:
        expression_str: 사용자가 입력한 수학식 문자열 (예: "L0 * (1 + alpha * dT)")
        symbols: 입력량 심볼 딕셔너리 {이름: sympy.Symbol}
        expression: 파싱된 sympy 표현식
        sensitivities: 각 입력량에 대한 편미분 {이름: sympy 표현식}
    """

    expression_str: str
    symbol_names: list[str] = field(default_factory=list)
    expression: Optional[sympy.Expr] = field(default=None, init=False)
    symbols: dict[str, Symbol] = field(default_factory=dict, init=False)
    sensitivities: dict[str, sympy.Expr] = field(default_factory=dict, init=False)
    _parsed: bool = field(default=False, init=False)

    def parse(self) -> None:
        """수학식을 파싱하고 심볼을 생성.

        Raises:
            ValueError: 수학식 파싱 실패 시
        """
        try:
            # 심볼 생성
            for name in self.symbol_names:
                self.symbols[name] = Symbol(name, real=True)

            # 수학식 파싱 (심볼을 로컬 변수로 전달)
            local_dict = {name: sym for name, sym in self.symbols.items()}
            self.expression = sympify(self.expression_str, locals=local_dict)
            self._parsed = True
        except Exception as e:
            raise ValueError(f"수학식 파싱 실패: {self.expression_str}\n오류: {e}")

    def compute_sensitivities(self) -> dict[str, sympy.Expr]:
        """모든 입력량에 대한 편미분(민감계수) 계산.

        c_i = ∂f/∂X_i

        Returns:
            {심볼 이름: 편미분 표현식} 딕셔너리
        """
        if not self._parsed:
            self.parse()

        self.sensitivities = {}
        for name, sym in self.symbols.items():
            self.sensitivities[name] = diff(self.expression, sym)

        return self.sensitivities

    def evaluate(self, values: dict[str, float]) -> float:
        """주어진 입력값으로 측정 모델을 평가.

        Args:
            values: {심볼 이름: 값} 딕셔너리

        Returns:
            Y = f(x₁, x₂, ..., xₙ) 계산 결과
        """
        if not self._parsed:
            self.parse()

        subs = {self.symbols[name]: val for name, val in values.items()}
        result = self.expression.subs(subs)
        return float(result)

    def evaluate_sensitivity(self, name: str, values: dict[str, float]) -> float:
        """특정 입력량의 민감계수를 주어진 값에서 평가.

        Args:
            name: 입력량 심볼 이름
            values: {심볼 이름: 값} 딕셔너리

        Returns:
            c_i = ∂f/∂X_i |_{X=x} 수치값
        """
        if not self.sensitivities:
            self.compute_sensitivities()

        if name not in self.sensitivities:
            raise KeyError(f"심볼 '{name}'이(가) 모델에 없습니다.")

        subs = {self.symbols[n]: val for n, val in values.items()}
        result = self.sensitivities[name].subs(subs)
        return float(result)

    def get_latex(self) -> str:
        """측정 모델의 LaTeX 표현을 반환."""
        if not self._parsed:
            self.parse()
        return latex(self.expression)

    def get_sensitivity_latex(self, name: str) -> str:
        """특정 입력량의 민감계수 LaTeX 표현을 반환."""
        if not self.sensitivities:
            self.compute_sensitivities()
        if name not in self.sensitivities:
            raise KeyError(f"심볼 '{name}'이(가) 모델에 없습니다.")
        return latex(self.sensitivities[name])

    def get_callable(self) -> callable:
        """측정 모델을 Python callable로 변환 (MCM 벡터 연산용).

        Returns:
            numpy 배열을 입력받아 결과를 반환하는 함수
        """
        if not self._parsed:
            self.parse()

        sym_list = [self.symbols[name] for name in self.symbol_names]
        return sympy.lambdify(sym_list, self.expression, modules=["numpy"])
