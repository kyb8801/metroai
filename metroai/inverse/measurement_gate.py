"""
Conformal Measurement Gate  (metroai/inverse/measurement_gate.py)
=================================================================
6/2 아이디어카드 I5 — "±tol 합부판정에 유한표본 보장".
ml_inverse 의 conformal 예측구간을 받아 측정값을 PASS / FAIL / RETEST 로 게이팅한다.
conformal 은 분포무관(distribution-free) coverage 라, 합부판정에 통계적 보장이 붙는다.

판정 (예측구간 [pred-h, pred+h] vs 스펙 [lo, hi], h = conformal 반폭):
    PASS   : 구간이 스펙 안에 완전히 들어감
    FAIL   : 구간이 스펙 밖으로 완전히 벗어남
    RETEST : 구간이 스펙 경계를 걸침 -> 재측정/실측 트리거(I8)
Deps: numpy (+ ml_inverse)
"""
import numpy as np

PASS, FAIL, RETEST = "PASS", "FAIL", "RETEST"


def gate(pred, halfwidth, spec_low, spec_high):
    pred = np.asarray(pred, float)
    lo, hi = pred - halfwidth, pred + halfwidth
    out = np.full(pred.shape, RETEST, dtype=object)
    out[(lo >= spec_low) & (hi <= spec_high)] = PASS
    out[(hi < spec_low) | (lo > spec_high)] = FAIL
    return out


def gate_report(pred, halfwidth, spec_low, spec_high, level=None):
    g = np.atleast_1d(gate(pred, halfwidth, spec_low, spec_high))
    n = len(g)
    counts = {k: int((g == k).sum()) for k in (PASS, FAIL, RETEST)}
    return {"decisions": g, "counts": counts,
            "retest_frac": counts[RETEST] / n if n else 0.0,
            "conformal_level": level, "spec": (spec_low, spec_high),
            "halfwidth": float(halfwidth)}


if __name__ == "__main__":
    from ml_inverse import MLInverse
    rng = np.random.default_rng(0)

    def fwd(p):
        t = p / 100.0
        return np.array([t, t**2, np.sqrt(t), np.log1p(t), 1.0 / t, t**1.5,
                         np.sin(t), np.cos(t), np.tanh(t), t**0.5, np.exp(-t), t / 2])

    SPEC_LO, SPEC_HI = 100.0, 140.0
    P = rng.uniform(80, 160, 600)
    X = np.array([fwd(p) + 0.01 * rng.standard_normal(12) for p in P])
    mdl = MLInverse().fit(X, P)
    Pt = rng.uniform(80, 160, 300)
    Xt = np.array([fwd(p) + 0.01 * rng.standard_normal(12) for p in Pt])
    o = mdl.predict(Xt)
    rep = gate_report(o["pred"], o["conformal_halfwidth"], SPEC_LO, SPEC_HI, o["conformal_level"])
    print(f"spec=[{SPEC_LO:.0f},{SPEC_HI:.0f}]  conformal_level={rep['conformal_level']:.0%}  halfwidth={rep['halfwidth']:.2f}")
    c = rep["counts"]
    print(f"PASS / FAIL / RETEST = {c['PASS']} / {c['FAIL']} / {c['RETEST']}  (retest {rep['retest_frac']:.0%})")
    g = rep["decisions"]
    true_in = (Pt >= SPEC_LO) & (Pt <= SPEC_HI)
    pm = g == PASS
    if pm.sum():
        print(f"PASS precision (true in-spec) = {(true_in & pm).sum() / pm.sum():.1%}")
    fm = g == FAIL
    if fm.sum():
        print(f"FAIL precision (true out-spec) = {(~true_in & fm).sum() / fm.sum():.1%}")
