"""
GUM <-> Posterior Bridge  (metroai/inverse/gum_posterior_bridge.py)
===================================================================
6/2 아이디어카드 **I2 — 회귀형 ML-inverse 의 posterior 불확도를 GUM 표준/확장 불확도로 사상**.

배경(6/2 딥리서치): CD-SAXS 문헌이 "GUM 1차 Taylor/준선형 가정은 sub-3nm 비선형 inverse 에서
부정확·오도 가능"이라고 공식 인정 -> 비선형 inverse 엔 posterior(ensemble/SBI/conformal) 기반
UQ 가 더 옳다. 그러나 KOLAS/DCC 보고체계는 GUM(u_c, U=k*u_c) 언어를 쓴다.
=> 둘을 잇는 '번역기'가 I2. 이 모듈이 uncertainty.py(GUM) 와 ml_inverse.py(posterior) 의 다리.

사상(mapping):
    ensemble posterior std  s_post     -> 표준불확도 u (type A, k=1)            [통계적]
    conformal halfwidth h @ level      -> 보장 구간; level->k 로 등가 표준화      [분포무관]
    측정계통 u_sys (GUM budget)        -> uncertainty.py 의 combined u_sys        [type B]
    결합:  u_c = sqrt(s_post^2 + u_sys^2),   U = k * u_c

VERIFIED (__main__): ml_inverse posterior + 가상 u_sys -> u_c, U(k=2) 산출 데모.
Deps: numpy, scipy  (+ ml_inverse, uncertainty 와 결합)
"""
import numpy as np
from scipy.stats import norm


def level_to_k(level):
    """coverage level(예: 0.90) -> 정규근사 양측 포함계수 k. conformal level 을 GUM k 로 환산."""
    return float(norm.ppf(0.5 + level / 2.0))


def conformal_to_standard(halfwidth, level):
    """conformal 반폭(분포무관 보장 구간) -> 등가 표준불확도 근사 = h / k(level)."""
    return float(halfwidth) / level_to_k(level)


def posterior_to_gum(s_post, u_sys=0.0, k=2):
    """ML posterior std (type A) + 측정계통 u_sys (type B) -> GUM 결합/확장 불확도.
    uncertainty.py 의 combine 과 동일 규약(제곱합)으로, ML 쪽을 GUM budget 의 한 성분처럼 편입."""
    s_post = np.asarray(s_post, float)
    u_c = np.sqrt(s_post ** 2 + np.asarray(u_sys, float) ** 2)
    return {"u_c": u_c, "U": k * u_c, "k": k}


if __name__ == "__main__":
    from ml_inverse import MLInverse
    rng = np.random.default_rng(0)

    def fwd(p):
        t = p / 100.0
        return np.array([t, t**2, np.sqrt(t), np.log1p(t), 1.0 / t, t**1.5,
                         np.sin(t), np.cos(t), np.tanh(t), t**0.5, np.exp(-t), t / 2])

    P = rng.uniform(80, 160, 600)
    X = np.array([fwd(p) + 0.01 * rng.standard_normal(12) for p in P])
    mdl = MLInverse().fit(X, P)

    Xq = np.array([fwd(120.0) + 0.01 * rng.standard_normal(12)])
    o = mdl.predict(Xq)
    s_post = float(o["u_epistemic"][0])
    h, lvl = o["conformal_halfwidth"], o["conformal_level"]
    u_sys = 0.5  # 예: 측정계통 표준불확도 (uncertainty.py GUM budget 에서 옴)

    g = posterior_to_gum(s_post, u_sys, k=2)
    print(f"posterior std = {s_post:.3f}   conformal h@{lvl:.0%} = {h:.3f}")
    print(f"conformal -> standard u = {conformal_to_standard(h, lvl):.3f}   (level {lvl:.0%} -> k = {level_to_k(lvl):.2f})")
    print(f"GUM 결합: u_c = {float(g['u_c']):.3f},  U(k=2) = {float(g['U']):.3f}   [posterior {s_post:.3f} (+) u_sys {u_sys}]")
