import os
import sqlite3
import argparse
import re
from datetime import datetime

import ijson
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

DEFAULT_DATA_DIR = "data/almrrc2021-data-training"

DB_FILE = "failure_features_v2.db"
OUTPUT_DIR = "failure_dataset_parts_v2"


# ============================================================
# STREAMING JSON READER
# ============================================================

class NaNSafeReader:
    """
    Streaming JSON reader that converts NaN / Infinity / -Infinity
    to null. Holds back trailing token-like characters so a token
    is never split across read() chunks.
    """

    def __init__(self, path):
        self.file = open(path, "rb")
        self.pending = b""

    def read(self, size=-1):
        while True:
            data = self.file.read(size)

            if not data:
                data, self.pending = self.pending, b""
                return self._replace_constants(data)

            data = self.pending + data

            m = re.search(rb'[A-Za-z0-9_\-]{0,10}\Z', data)
            tail_len = len(m.group())

            process = data[:len(data) - tail_len]
            self.pending = data[len(data) - tail_len:]

            if process:
                return self._replace_constants(process)

    @staticmethod
    def _replace_constants(data):
        data = re.sub(rb'(?<![A-Za-z0-9_])NaN(?![A-Za-z0-9_])', b'null', data)
        data = re.sub(rb'(?<![A-Za-z0-9_])-Infinity(?![A-Za-z0-9_])', b'null', data)
        data = re.sub(rb'(?<![A-Za-z0-9_])Infinity(?![A-Za-z0-9_])', b'null', data)
        return data

    def close(self):
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None


def hour_of_day(dt):
    return dt.hour + dt.minute / 60.0


# ============================================================
# DATABASE
# ============================================================

def create_database(db_path):
    if os.path.exists(db_path):
        print(f"Removing old database: {db_path}")
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA temp_store=FILE;")

    conn.execute("""
        CREATE TABLE stops (
            route_id TEXT,
            stop_id TEXT,

            station_code TEXT,
            executor_capacity REAL,
            route_date TEXT,

            zone_id TEXT,
            latitude REAL,
            longitude REAL,

            route_num_stops INTEGER,
            route_num_packages INTEGER,
            stop_package_count INTEGER,

            stop_total_volume REAL,
            stop_avg_volume REAL,
            total_service_time REAL,

            has_time_window INTEGER,
            window_duration_sec REAL,
            window_start_hour REAL,
            window_end_hour REAL,

            stop_position INTEGER,
            stop_position_ratio REAL,
            remaining_stops INTEGER,

            first_attempt_failure INTEGER DEFAULT 0,

            PRIMARY KEY(route_id, stop_id)
        )
    """)

    conn.execute("""
        CREATE TABLE package_events (
            route_id TEXT,
            stop_id TEXT,
            package_id TEXT,
            scan_status TEXT
        )
    """)

    conn.execute("CREATE INDEX idx_route_stop ON package_events(route_id, stop_id)")
    conn.commit()
    return conn


# ============================================================
# STEP 1: ROUTE FEATURES
# ============================================================

def process_routes(route_file, conn):
    print("\n========================================")
    print("STEP 1: Processing route data")
    print("========================================")

    count = 0

    with NaNSafeReader(route_file) as f:
        for route_id, route_info in ijson.kvitems(f, ""):

            stops = route_info.get("stops", {})

            station_code = route_info.get("station_code")
            executor_capacity = safe_float(route_info.get("executor_capacity_cm3"))
            route_date = route_info.get("date_YYYY_MM_DD")

            delivery_stops = [
                (stop_id, stop_info)
                for stop_id, stop_info in stops.items()
                if stop_info.get("type") != "Station"
            ]

            route_num_stops = len(delivery_stops)
            rows = []

            for position, (stop_id, stop_info) in enumerate(delivery_stops, start=1):
                position_ratio = position / route_num_stops if route_num_stops else 0
                remaining_stops = route_num_stops - position

                rows.append((
                    route_id,
                    stop_id,
                    station_code,
                    executor_capacity,
                    route_date,
                    stop_info.get("zone_id"),
                    safe_float(stop_info.get("lat")),
                    safe_float(stop_info.get("lng")),
                    route_num_stops,
                    0,      # route_num_packages (filled in step 2)
                    0,      # stop_package_count
                    0,      # stop_total_volume
                    0,      # stop_avg_volume
                    0,      # total_service_time
                    0,      # has_time_window
                    0,      # window_duration_sec
                    None,   # window_start_hour
                    None,   # window_end_hour
                    position,
                    position_ratio,
                    remaining_stops,
                ))

            conn.executemany("""
                INSERT INTO stops (
                    route_id, stop_id, station_code, executor_capacity,
                    route_date, zone_id, latitude, longitude,
                    route_num_stops, route_num_packages, stop_package_count,
                    stop_total_volume, stop_avg_volume, total_service_time,
                    has_time_window, window_duration_sec,
                    window_start_hour, window_end_hour,
                    stop_position, stop_position_ratio, remaining_stops
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, rows)

            count += 1
            if count % 500 == 0:
                conn.commit()
                print(f"Routes processed: {count}")

    conn.commit()
    print(f"\nFinished routes: {count}")


# ============================================================
# STEP 2: PACKAGE FEATURES
# ============================================================

def process_packages(package_file, conn):
    print("\n========================================")
    print("STEP 2: Processing package data")
    print("========================================")

    count = 0

    with NaNSafeReader(package_file) as f:
        for route_id, route_stops in ijson.kvitems(f, ""):

            route_package_total = 0
            event_rows = []

            for stop_id, packages in route_stops.items():

                if not isinstance(packages, dict):
                    continue

                package_count = 0
                total_volume = 0.0
                total_service_time = 0.0
                window_starts = []
                window_ends = []

                for package_id, package in packages.items():

                    if not isinstance(package, dict):
                        continue

                    package_count += 1
                    route_package_total += 1

                    # VOLUME (cm^3)
                    dims = package.get("dimensions") or {}
                    depth = safe_float(dims.get("depth_cm"))
                    width = safe_float(dims.get("width_cm"))
                    height = safe_float(dims.get("height_cm"))
                    total_volume += depth * width * height

                    # SERVICE TIME
                    total_service_time += safe_float(
                        package.get("planned_service_time_seconds")
                    )

                    # TIME WINDOW
                    tw = package.get("time_window") or {}
                    start_dt = parse_datetime(tw.get("start_time_utc"))
                    end_dt = parse_datetime(tw.get("end_time_utc"))

                    if start_dt is not None:
                        window_starts.append(start_dt)
                    if end_dt is not None:
                        window_ends.append(end_dt)

                    # EVENT STATUS (used only to build the label)
                    scan_status = package.get("scan_status") or package.get("status")
                    if scan_status:
                        event_rows.append(
                            (route_id, stop_id, package_id, str(scan_status))
                        )

                avg_volume = total_volume / package_count if package_count else 0

                has_time_window = int(bool(window_starts or window_ends))

                start_hour = None
                end_hour = None
                window_duration = 0

                if window_starts:
                    earliest = min(window_starts)
                    start_hour = hour_of_day(earliest)

                if window_ends:
                    latest = max(window_ends)
                    end_hour = hour_of_day(latest)

                if window_starts and window_ends:
                    window_duration = max(
                        0, (max(window_ends) - min(window_starts)).total_seconds()
                    )

                conn.execute("""
                    UPDATE stops
                    SET
                        stop_package_count = ?,
                        stop_total_volume = ?,
                        stop_avg_volume = ?,
                        total_service_time = ?,
                        has_time_window = ?,
                        window_duration_sec = ?,
                        window_start_hour = ?,
                        window_end_hour = ?
                    WHERE route_id = ? AND stop_id = ?
                """, (
                    package_count,
                    total_volume,
                    avg_volume,
                    total_service_time,
                    has_time_window,
                    window_duration,
                    start_hour,
                    end_hour,
                    route_id,
                    stop_id,
                ))

            if event_rows:
                conn.executemany("""
                    INSERT INTO package_events
                        (route_id, stop_id, package_id, scan_status)
                    VALUES (?, ?, ?, ?)
                """, event_rows)

            conn.execute(
                "UPDATE stops SET route_num_packages = ? WHERE route_id = ?",
                (route_package_total, route_id),
            )

            count += 1
            if count % 500 == 0:
                conn.commit()
                print(f"Package routes processed: {count}")

    conn.commit()
    print(f"\nFinished package processing: {count}")


# ============================================================
# STEP 3: INSPECT EVENTS
# ============================================================

def inspect_events(conn):
    print("\n========================================")
    print("STEP 3: Inspecting delivery events")
    print("========================================")

    count = conn.execute("SELECT COUNT(*) FROM package_events").fetchone()[0]
    print(f"Package event records: {count}")

    if count == 0:
        print("WARNING: no scan_status found. Not fabricating labels.")
        return False

    rows = conn.execute("""
        SELECT scan_status, COUNT(*)
        FROM package_events
        GROUP BY scan_status
        LIMIT 20
    """).fetchall()

    for status, n in rows:
        print(f"  {status}: {n}")

    return True


# ============================================================
# STEP 4: BUILD LABEL
# ============================================================

def build_labels(conn):
    print("\n========================================")
    print("STEP 4: Building failure labels")
    print("========================================")

    # A stop is a failure if ANY package there has an ATTEMPT status
    conn.execute("""
        UPDATE stops
        SET first_attempt_failure = 1
        WHERE EXISTS (
            SELECT 1
            FROM package_events e
            WHERE e.route_id = stops.route_id
              AND e.stop_id = stops.stop_id
              AND UPPER(e.scan_status) LIKE '%ATTEMPT%'
        )
    """)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM stops").fetchone()[0]
    failures = conn.execute(
        "SELECT COUNT(*) FROM stops WHERE first_attempt_failure = 1"
    ).fetchone()[0]

    print(f"Total stops  : {total}")
    print(f"Failures     : {failures}")
    if total:
        print(f"Failure rate : {failures / total:.4%}")


# ============================================================
# STEP 5: EXPORT
# ============================================================

def export_dataset(conn, output_dir):
    print("\n========================================")
    print("STEP 5: Exporting dataset")
    print("========================================")

    query = """
        SELECT
            route_id,
            station_code,
            executor_capacity,
            route_date,
            zone_id,
            latitude,
            longitude,
            route_num_stops,
            route_num_packages,
            stop_package_count,
            stop_total_volume,
            stop_avg_volume,
            total_service_time,
            has_time_window,
            window_duration_sec,
            window_start_hour,
            window_end_hour,
            stop_position,
            stop_position_ratio,
            remaining_stops,
            first_attempt_failure
        FROM stops
    """

    os.makedirs(output_dir, exist_ok=True)

    categorical = ["station_code", "zone_id", "route_date"]

    numeric = [
        "executor_capacity", "latitude", "longitude",
        "route_num_stops", "route_num_packages", "stop_package_count",
        "stop_total_volume", "stop_avg_volume", "total_service_time",
        "has_time_window", "window_duration_sec",
        "window_start_hour", "window_end_hour",
        "stop_position", "stop_position_ratio", "remaining_stops",
        "first_attempt_failure",
    ]

    chunk_number = 0

    for chunk in pd.read_sql_query(query, conn, chunksize=100_000):
        chunk_number += 1

        for col in categorical:
            chunk[col] = chunk[col].fillna("UNKNOWN").astype(str)

        for col in numeric:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

        path = os.path.join(output_dir, f"part_{chunk_number:04d}.parquet")
        chunk.to_parquet(path, index=False)
        print(f"Written {path} ({len(chunk):,} rows)")

    print(f"\nDataset parts written to: {output_dir}/")


# ============================================================
# STEP 6: AUDIT
# ============================================================

def audit_dataset(output_dir):
    print("\n========================================")
    print("STEP 6: Auditing dataset")
    print("========================================")

    df = pd.read_parquet(output_dir)

    print(f"Shape: {df.shape}")
    print(f"Columns ({len(df.columns)}): {df.columns.tolist()}")

    print("\nTARGET:")
    print(df["first_attempt_failure"].value_counts())

    print("\nNUMERIC SUMMARY:")
    num_cols = df.select_dtypes("number").columns
    print(df[num_cols].describe().T[["mean", "min", "max"]])

    print("\nDEAD / SUSPICIOUS COLUMNS:")
    problems = 0
    for c in num_cols:
        if c == "first_attempt_failure":
            continue
        if df[c].nunique(dropna=False) <= 1:
            print(f"  !! {c} is constant")
            problems += 1
    if problems == 0:
        print("  none")

    print("\nMISSING VALUES:")
    print(df.isna().sum()[df.isna().sum() > 0])


# ============================================================
# MAIN
# ============================================================

def main(data_dir):
    route_file = os.path.join(data_dir, "model_build_inputs", "route_data.json")
    package_file = os.path.join(data_dir, "model_build_inputs", "package_data.json")

    for p in (route_file, package_file):
        if not os.path.exists(p):
            raise FileNotFoundError(f"File not found:\n{p}")

    print("\n==============================================")
    print(" FAILURE DATASET BUILDER v2")
    print("==============================================")

    conn = create_database(DB_FILE)

    try:
        process_routes(route_file, conn)
        process_packages(package_file, conn)

        if not inspect_events(conn):
            print("\nSTOPPING: no events found.")
            return

        build_labels(conn)
        export_dataset(conn, OUTPUT_DIR)

    finally:
        conn.close()

    audit_dataset(OUTPUT_DIR)

    print("\n==============================================")
    print(" DONE")
    print("==============================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default=DEFAULT_DATA_DIR)
    args = parser.parse_args()
    main(args.data_dir)