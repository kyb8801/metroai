"""단위 문자열 → D-SI 단위 표기 변환.

DCC(Digital Calibration Certificate)의 수치는 D-SI(Digital System of Units,
https://ptb.de/si, SI_Format.xsd v2.2.1) 표기를 사용한다.
예: "mm" → "\\milli\\metre", "°C" → "\\degreecelsius".

주의:
- D-SI 2.2.1의 unitType 자체는 패턴 제약이 없는 문자열이므로, 미등록 단위를
  원문 그대로 넣어도 XSD 검증은 통과한다. 다만 D-SI 관례(SI brochure 9판)에는
  어긋나므로 builder가 경고를 남긴다.
- 대소문자를 구분한다 ("s"=초, "S"=지멘스). "C"는 쿨롬으로 해석하며,
  섭씨는 반드시 "°C"/"℃"/"degC"로 표기한다.
- ppm·dB·bar 등 SI brochure 9판 비수록 단위는 의도적으로 매핑하지 않는다
  (필요 시 사용자가 D-SI 원문 표기를 직접 입력).
"""

from __future__ import annotations

# 접두어 없는/있는 상용 단위 → D-SI 표기 (KOLAS 교정 분야에서 흔한 것 위주)
DSI_UNIT_MAP: dict[str, str] = {
    # 무차원
    "1": r"\one",
    "one": r"\one",
    "%": r"\percent",
    # 길이
    "m": r"\metre",
    "km": r"\kilo\metre",
    "cm": r"\centi\metre",
    "mm": r"\milli\metre",
    "um": r"\micro\metre",
    "µm": r"\micro\metre",
    "μm": r"\micro\metre",
    "nm": r"\nano\metre",
    "pm": r"\pico\metre",
    # 질량
    "kg": r"\kilogram",
    "g": r"\gram",
    "mg": r"\milli\gram",
    "ug": r"\micro\gram",
    "µg": r"\micro\gram",
    # 시간
    "s": r"\second",
    "ms": r"\milli\second",
    "us": r"\micro\second",
    "µs": r"\micro\second",
    "ns": r"\nano\second",
    "min": r"\minute",
    "h": r"\hour",
    # 전류
    "A": r"\ampere",
    "mA": r"\milli\ampere",
    "uA": r"\micro\ampere",
    "µA": r"\micro\ampere",
    "kA": r"\kilo\ampere",
    # 온도
    "K": r"\kelvin",
    "mK": r"\milli\kelvin",
    "°C": r"\degreecelsius",
    "℃": r"\degreecelsius",
    "degC": r"\degreecelsius",
    # 물질량·광도
    "mol": r"\mole",
    "mmol": r"\milli\mole",
    "cd": r"\candela",
    # 주파수
    "Hz": r"\hertz",
    "kHz": r"\kilo\hertz",
    "MHz": r"\mega\hertz",
    "GHz": r"\giga\hertz",
    # 힘·압력
    "N": r"\newton",
    "kN": r"\kilo\newton",
    "mN": r"\milli\newton",
    "Pa": r"\pascal",
    "hPa": r"\hecto\pascal",
    "kPa": r"\kilo\pascal",
    "MPa": r"\mega\pascal",
    "GPa": r"\giga\pascal",
    # 에너지·일률
    "J": r"\joule",
    "kJ": r"\kilo\joule",
    "eV": r"\electronvolt",
    "W": r"\watt",
    "mW": r"\milli\watt",
    "kW": r"\kilo\watt",
    # 전기
    "C": r"\coulomb",
    "V": r"\volt",
    "mV": r"\milli\volt",
    "uV": r"\micro\volt",
    "µV": r"\micro\volt",
    "kV": r"\kilo\volt",
    "F": r"\farad",
    "pF": r"\pico\farad",
    "nF": r"\nano\farad",
    "uF": r"\micro\farad",
    "µF": r"\micro\farad",
    "ohm": r"\ohm",
    "Ohm": r"\ohm",
    "Ω": r"\ohm",
    "kΩ": r"\kilo\ohm",
    "kohm": r"\kilo\ohm",
    "MΩ": r"\mega\ohm",
    "Mohm": r"\mega\ohm",
    "mΩ": r"\milli\ohm",
    "mohm": r"\milli\ohm",
    "S": r"\siemens",
    # 자기
    "Wb": r"\weber",
    "T": r"\tesla",
    "mT": r"\milli\tesla",
    "uT": r"\micro\tesla",
    "µT": r"\micro\tesla",
    "H": r"\henry",
    # 광·방사
    "lm": r"\lumen",
    "lx": r"\lux",
    "Bq": r"\becquerel",
    "Gy": r"\gray",
    "Sv": r"\sievert",
    # 각도
    "rad": r"\radian",
    "mrad": r"\milli\radian",
    "urad": r"\micro\radian",
    "µrad": r"\micro\radian",
    "sr": r"\steradian",
    "°": r"\degree",
    "deg": r"\degree",
    "'": r"\arcminute",
    "''": r"\arcsecond",
    '"': r"\arcsecond",
    # 부피
    "L": r"\litre",
    "l": r"\litre",
    "mL": r"\milli\litre",
    "ml": r"\milli\litre",
}


def to_dsi_unit(unit: str) -> str | None:
    """상용 단위 문자열을 D-SI 표기로 변환.

    Args:
        unit: 단위 문자열 (예: "mm", "°C", "m/s", 또는 이미 D-SI 표기인 "\\metre")

    Returns:
        D-SI 표기 문자열. 변환 불가 시 None (호출자가 경고 처리).
        빈 문자열은 무차원(\\one)으로 취급.
    """
    unit = (unit or "").strip()
    if unit == "":
        return r"\one"
    if unit.startswith("\\"):
        # 이미 D-SI 표기로 판단 → 그대로 통과 (내용 검증은 XSD/소비자 몫)
        return unit
    if unit in DSI_UNIT_MAP:
        return DSI_UNIT_MAP[unit]
    # 단순 몫 형태 "A/B" (예: "m/s", "µm/m")
    if unit.count("/") == 1:
        num, den = (p.strip() for p in unit.split("/"))
        num_dsi = DSI_UNIT_MAP.get(num)
        den_dsi = DSI_UNIT_MAP.get(den)
        if num_dsi and den_dsi:
            return num_dsi + den_dsi + r"\tothe{-1}"
    return None
