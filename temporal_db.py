from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd


@dataclass
class TemporalRecord:
    first_name: str
    last_name: str
    loinc_num: str
    value: str
    unit: str
    valid_time: datetime          # valid time (measurement time)
    system_from: datetime         # transaction time (when this version was inserted)
    system_to: Optional[datetime] # None = still valid


class TemporalDB:
    def __init__(self, excel_path: str, loinc_csv_path: str):
        self.current_time: datetime = datetime.now()
        self.records: List[TemporalRecord] = []
        self.loinc_name: Dict[str, str] = {}

        self._load_excel(excel_path)
        self._load_loinc(loinc_csv_path)

    # ---------- loading data ----------

    def _load_excel(self, excel_path: str) -> None:
        df = pd.read_excel(excel_path)

        for _, row in df.iterrows():
            self.records.append(
                TemporalRecord(
                    first_name=row["First name"],
                    last_name=row["Last name"],
                    loinc_num=str(row["LOINC-NUM"]),
                    value=str(row["Value"]),
                    unit=row["Unit"],
                    valid_time=pd.to_datetime(row["Valid start time"]).to_pydatetime(),
                    system_from=pd.to_datetime(row["Transaction time"]).to_pydatetime(),
                    system_to=None,
                )
            )

    def _load_loinc(self, loinc_csv_path: str) -> None:
        loinc_df = pd.read_csv(loinc_csv_path)

        # חשוב: אם בעמודות בקובץ שלך השמות קצת שונים,
        # למשל "LOINC_NUM" או "LONG_COMMON_NAME ",
        # תעדכן כאן בהתאם.
        self.loinc_name = {
            str(row["LOINC_NUM"]): row["LONG_COMMON_NAME"]
            for _, row in loinc_df.iterrows()
        }

    # ---------- helpers ----------

    def set_current_time(self, t: datetime) -> None:
        self.current_time = t

    def _is_alive_at(self, rec: TemporalRecord, t: datetime) -> bool:
        if rec.system_from > t:
            return False
        if rec.system_to is not None and rec.system_to <= t:
            return False
        return True

    # ---------- queries ----------

    def query_value(
            self,
            first_name: str,
            last_name: str,
            loinc_num: str,
            date: datetime,
            time: Optional[datetime.time] = None,
            perspective_time: Optional[datetime] = None,
    ):
        """
        Retrieve a single value according to bi-temporal logic.

        Behavior:
        - If both date AND time are provided:
            A measurement must exist exactly at that valid time.
        - If only date is provided (no time):
            The system returns the latest measurement of that day
            that is still alive at the given perspective time.
        - Logical deletions (system_to) are fully respected.
        """

        if perspective_time is None:
            perspective_time = self.current_time

        # Filter records by patient, LOINC code, and valid-date (same day)
        candidates = [
            r
            for r in self.records
            if r.first_name == first_name
               and r.last_name == last_name
               and r.loinc_num == loinc_num
               and r.valid_time.date() == date.date()
        ]

        if not candidates:
            return None

        # Case 1: Exact time is provided → must match exactly
        if time is not None:
            same_time = [r for r in candidates if r.valid_time.time() == time]
            if not same_time:
                return None

            # Keep only records that are alive at the given perspective time
            alive = [r for r in same_time if self._is_alive_at(r, perspective_time)]
            if not alive:
                return None

            # If multiple versions exist for the same valid time,
            # choose the one with the latest transaction time (system_from)
            best = max(alive, key=lambda r: r.system_from)

        # Case 2: Only date is provided → choose the latest alive measurement of that day
        else:
            # First, keep only records that are alive at the perspective time
            alive = [r for r in candidates if self._is_alive_at(r, perspective_time)]
            if not alive:
                return None

            # Find the latest valid_time among alive records
            max_valid = max(r.valid_time for r in alive)
            latest_same_time = [r for r in alive if r.valid_time == max_valid]

            # If multiple versions exist for the same latest valid_time,
            # choose the one with the latest transaction time
            best = max(latest_same_time, key=lambda r: r.system_from)

        # Map LOINC number to its official long common name
        long_name = self.loinc_name.get(loinc_num, loinc_num)

        return {
            "first_name": best.first_name,
            "last_name": best.last_name,
            "loinc": best.loinc_num,
            "long_common_name": long_name,
            "value": best.value,
            "unit": best.unit,
            "valid_time": best.valid_time,
            "system_from": best.system_from,
            "system_to": best.system_to,
        }

    def query_history(
        self,
        first_name: str,
        last_name: str,
        loinc_num: str,
        valid_from: datetime,
        valid_to: datetime,
        tx_from: Optional[datetime] = None,
        tx_to: Optional[datetime] = None,
    ):
        """History query – versions in valid-time range, grouped by valid_time."""
        if tx_from is None:
            tx_from = datetime(1900, 1, 1)
        if tx_to is None:
            tx_to = self.current_time

        # filter by patient + loinc + valid range
        candidates = [
            r
            for r in self.records
            if r.first_name == first_name
            and r.last_name == last_name
            and r.loinc_num == loinc_num
            and valid_from <= r.valid_time <= valid_to
        ]

        # transaction-time range (basic version)
        tx_filtered = [r for r in candidates if tx_from <= r.system_from <= tx_to]

        # group by valid_time and keep only latest system_from
        groups: Dict[datetime, TemporalRecord] = {}
        for r in tx_filtered:
            key = r.valid_time
            if key not in groups or groups[key].system_from < r.system_from:
                groups[key] = r

        long_name = self.loinc_name.get(loinc_num, loinc_num)

        result = []
        for vt in sorted(groups.keys()):
            rec = groups[vt]
            result.append(
                {
                    "valid_time": rec.valid_time,
                    "value": rec.value,
                    "unit": rec.unit,
                    "system_from": rec.system_from,
                    "system_to": rec.system_to,
                    "long_common_name": long_name,
                }
            )
        return result

    # ---------- updates ----------

    def update_value(
        self,
        first_name: str,
        last_name: str,
        loinc_num: str,
        valid_time: datetime,
        new_value: str,
        t_update: Optional[datetime] = None,
    ) -> None:
        """Logical update: close current version and insert new one."""
        if t_update is None:
            t_update = self.current_time

        candidates = [
            r
            for r in self.records
            if r.first_name == first_name
            and r.last_name == last_name
            and r.loinc_num == loinc_num
            and r.valid_time == valid_time
            and self._is_alive_at(r, t_update)
        ]

        if not candidates:
            print("No record found to update.")
            return

        current = max(candidates, key=lambda r: r.system_from)

        # close old version
        current.system_to = t_update

        # add new version
        new_rec = TemporalRecord(
            first_name=current.first_name,
            last_name=current.last_name,
            loinc_num=current.loinc_num,
            value=new_value,
            unit=current.unit,
            valid_time=current.valid_time,
            system_from=t_update,
            system_to=None,
        )
        self.records.append(new_rec)

        print("Update done.")
        print("Old version:", current)
        print("New version:", new_rec)

    def delete_value(
        self,
        first_name: str,
        last_name: str,
        loinc_num: str,
        date: datetime,
        time: Optional[datetime.time] = None,
        t_delete: Optional[datetime] = None,
    ) -> None:
        """Logical delete: close last version for that measurement."""
        if t_delete is None:
            t_delete = self.current_time

        candidates = [
            r
            for r in self.records
            if r.first_name == first_name
            and r.last_name == last_name
            and r.loinc_num == loinc_num
            and r.valid_time.date() == date.date()
            and self._is_alive_at(r, t_delete)
        ]

        if not candidates:
            print("No record found to delete.")
            return

        if time is not None:
            candidates = [r for r in candidates if r.valid_time.time() == time]
            if not candidates:
                print("No record with this exact time.")
                return
        else:
            max_valid = max(r.valid_time for r in candidates)
            candidates = [r for r in candidates if r.valid_time == max_valid]

        target = max(candidates, key=lambda r: r.system_from)
        target.system_to = t_delete

        print("Logical delete done. Record closed at:", t_delete)
        print(target)
