"""MetroAI SQLite Database — System of Record (v0.5.0).

모든 데이터를 영속 저장하여 MetroAI가 "기관의 품질 시스템"이 되게 한다.
Regulatory lock-in의 기반: 이 DB에 데이터가 쌓이면 이탈이 규제 리스크가 됨.

Tables:
  - equipment: 장비 목록 + 교정 상태
  - calibration_history: 장비별 교정 이력
  - uncertainty_records: 불확도 계산 이력
  - pt_records: PT 참가 이력
  - measure_requests: MeasureLink 의뢰 이력
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

# DB 파일 위치 (프로젝트 루트)
import tempfile as _tf
_default_dir = Path(_tf.gettempdir()) if not (Path(__file__).resolve().parent.parent.parent / "metroai_data.db").parent.exists() else Path(__file__).resolve().parent.parent.parent
DB_PATH = _default_dir / "metroai_data.db"


def get_db() -> "MetroAIDB":
    """싱글톤 DB 인스턴스."""
    return MetroAIDB(DB_PATH)


class MetroAIDB:
    """MetroAI 영속 데이터베이스."""

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        """테이블 생성 (없으면)."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    manufacturer TEXT,
                    model TEXT,
                    serial_number TEXT,
                    category TEXT,
                    location TEXT,
                    cal_cycle_months INTEGER DEFAULT 12,
                    last_cal_date TEXT,
                    next_cal_date TEXT,
                    cal_org TEXT,
                    cal_cert_number TEXT,
                    status TEXT DEFAULT 'active',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS calibration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER REFERENCES equipment(id),
                    cal_date TEXT NOT NULL,
                    cal_org TEXT,
                    cal_cert_number TEXT,
                    expanded_uncertainty TEXT,
                    coverage_factor REAL,
                    result TEXT,
                    cost REAL,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS uncertainty_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template TEXT,
                    measurand_name TEXT,
                    measurand_unit TEXT,
                    combined_uncertainty REAL,
                    expanded_uncertainty REAL,
                    coverage_factor REAL,
                    effective_dof REAL,
                    input_data TEXT,
                    components_json TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    created_by TEXT
                );

                CREATE TABLE IF NOT EXISTS pt_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pt_program TEXT,
                    cal_point TEXT,
                    lab_value REAL,
                    assigned_value REAL,
                    z_score REAL,
                    z_judgment TEXT,
                    en_number REAL,
                    en_judgment TEXT,
                    year INTEGER,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS measure_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requester_name TEXT,
                    requester_email TEXT,
                    requester_type TEXT,
                    category TEXT,
                    detail TEXT,
                    kolas_required TEXT,
                    urgency TEXT,
                    budget TEXT,
                    status TEXT DEFAULT 'pending',
                    matched_org TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
            """)

    # ══════════════════════════════════════
    # 장비 관리
    # ══════════════════════════════════════

    def add_equipment(self, **kwargs) -> int:
        """장비 등록."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO equipment (name, manufacturer, model, serial_number,
                   category, location, cal_cycle_months, last_cal_date, next_cal_date,
                   cal_org, cal_cert_number, notes)
                   VALUES (:name, :manufacturer, :model, :serial_number,
                   :category, :location, :cal_cycle_months, :last_cal_date, :next_cal_date,
                   :cal_org, :cal_cert_number, :notes)""",
                kwargs,
            )
            return cur.lastrowid

    def get_all_equipment(self) -> list[dict]:
        """전체 장비 목록."""
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM equipment WHERE status='active' ORDER BY next_cal_date").fetchall()
            return [dict(r) for r in rows]

    def get_equipment(self, equipment_id: int) -> Optional[dict]:
        """장비 1건 조회."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM equipment WHERE id=?", (equipment_id,)).fetchone()
            return dict(row) if row else None

    def update_equipment(self, equipment_id: int, **kwargs) -> None:
        """장비 정보 수정."""
        sets = ", ".join(f"{k}=:{k}" for k in kwargs)
        kwargs["id"] = equipment_id
        kwargs["updated_at"] = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(f"UPDATE equipment SET {sets}, updated_at=:updated_at WHERE id=:id", kwargs)

    def get_overdue_equipment(self) -> list[dict]:
        """교정 기한 초과 장비."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM equipment WHERE status='active' AND next_cal_date < ? ORDER BY next_cal_date",
                (today,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ══════════════════════════════════════
    # 교정 이력
    # ══════════════════════════════════════

    def add_calibration(self, equipment_id: int, **kwargs) -> int:
        """교정 이력 추가."""
        kwargs["equipment_id"] = equipment_id
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO calibration_history (equipment_id, cal_date, cal_org,
                   cal_cert_number, expanded_uncertainty, coverage_factor, result, cost, notes)
                   VALUES (:equipment_id, :cal_date, :cal_org, :cal_cert_number,
                   :expanded_uncertainty, :coverage_factor, :result, :cost, :notes)""",
                kwargs,
            )
            return cur.lastrowid

    def get_calibration_history(self, equipment_id: int) -> list[dict]:
        """장비별 교정 이력."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM calibration_history WHERE equipment_id=? ORDER BY cal_date DESC",
                (equipment_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ══════════════════════════════════════
    # 불확도 계산 이력
    # ══════════════════════════════════════

    def save_uncertainty(self, **kwargs) -> int:
        """불확도 계산 결과 저장."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO uncertainty_records (template, measurand_name, measurand_unit,
                   combined_uncertainty, expanded_uncertainty, coverage_factor, effective_dof,
                   input_data, components_json, created_by)
                   VALUES (:template, :measurand_name, :measurand_unit,
                   :combined_uncertainty, :expanded_uncertainty, :coverage_factor, :effective_dof,
                   :input_data, :components_json, :created_by)""",
                kwargs,
            )
            return cur.lastrowid

    def get_uncertainty_history(self, limit: int = 50) -> list[dict]:
        """불확도 계산 이력."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM uncertainty_records ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ══════════════════════════════════════
    # PT 이력
    # ══════════════════════════════════════

    def save_pt(self, **kwargs) -> int:
        """PT 결과 저장."""
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO pt_records (pt_program, cal_point, lab_value, assigned_value,
                   z_score, z_judgment, en_number, en_judgment, year, notes)
                   VALUES (:pt_program, :cal_point, :lab_value, :assigned_value,
                   :z_score, :z_judgment, :en_number, :en_judgment, :year, :notes)""",
                kwargs,
            )
            return cur.lastrowid

    def get_pt_history(self, limit: int = 50) -> list[dict]:
        """PT 이력."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pt_records ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ══════════════════════════════════════
    # 통계
    # ══════════════════════════════════════

    def get_dashboard_stats(self) -> dict:
        """대시보드용 통계."""
        with self._conn() as conn:
            equip_count = conn.execute("SELECT COUNT(*) FROM equipment WHERE status='active'").fetchone()[0]
            overdue = conn.execute(
                "SELECT COUNT(*) FROM equipment WHERE status='active' AND next_cal_date < date('now')"
            ).fetchone()[0]
            unc_count = conn.execute("SELECT COUNT(*) FROM uncertainty_records").fetchone()[0]
            pt_count = conn.execute("SELECT COUNT(*) FROM pt_records").fetchone()[0]
            req_count = conn.execute("SELECT COUNT(*) FROM measure_requests").fetchone()[0]

            return {
                "total_equipment": equip_count,
                "overdue_equipment": overdue,
                "total_uncertainties": unc_count,
                "total_pt": pt_count,
                "total_requests": req_count,
            }
