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

DB_FILE = "failure_features.db"
OUTPUT_FILE = "failure_dataset.parquet"


# ============================================================
# STREAMING JSON READER
# ============================================================

class NaNSafeReader:
    """
    Streaming JSON reader that safely converts non-standard
    JSON constants (NaN, Infinity, -Infinity) to null.

    Handles tokens split across read() chunks by holding back
    any trailing run of token-like characters until the next read.
    """

    def __init__(self, path):
        self.file = open(path, "rb")
        self.pending = b""

    def read(self, size=-1):
        while True:
            data = self.file.read(size)

            if not data:
                # EOF: flush whatever is left
                data, self.pending = self.pending, b""
                return self._replace_constants(data)

            data = self.pending + data

            # Hold back a trailing run of token-like chars (max 10 bytes),
            # since it might be the start of NaN / Infinity / -Infinity.
            # \Z = true end of data (not before a trailing newline).
            m = re.search(rb'[A-Za-z0-9_\-]{0,10}\Z', data)
            tail_len = len(m.group())

            process = data[:len(data) - tail_len]
            self.pending = data[len(data) - tail_len:]

            # Never return empty bytes mid-file, ijson would treat it as EOF
            if process:
                return self._replace_constants(process)

    @staticmethod
    def _replace_constants(data):
        data = re.sub(
            rb'(?<![A-Za-z0-9_])NaN(?![A-Za-z0-9_])',
            b'null',
            data
        )
        data = re.sub(
            rb'(?<![A-Za-z0-9_])-Infinity(?![A-Za-z0-9_])',
            b'null',
            data
        )
        data = re.sub(
            rb'(?<![A-Za-z0-9_])Infinity(?![A-Za-z0-9_])',
            b'null',
            data
        )
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

        return datetime.strptime(
            value,
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception:

        try:
            return datetime.fromisoformat(value)

        except Exception:
            return None


def get_hour(value):

    dt = parse_datetime(value)

    if dt is None:
        return None

    return dt.hour + dt.minute / 60.0


# ============================================================
# DATABASE
# ============================================================

def create_database(db_path):

    if os.path.exists(db_path):

        print(
            f"Removing old database: {db_path}"
        )

        os.remove(db_path)

    conn = sqlite3.connect(db_path)

    conn.execute(
        "PRAGMA journal_mode=WAL;"
    )

    conn.execute(
        "PRAGMA synchronous=NORMAL;"
    )

    conn.execute(
        "PRAGMA temp_store=FILE;"
    )

    # --------------------------------------------------------
    # STOP TABLE
    # --------------------------------------------------------

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

            stop_total_weight REAL,
            stop_avg_weight REAL,

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

    # --------------------------------------------------------
    # PACKAGE EVENTS
    # --------------------------------------------------------

    conn.execute("""
        CREATE TABLE package_events (

            route_id TEXT,
            stop_id TEXT,
            package_id TEXT,
            scan_status TEXT

        )
    """)

    conn.execute("""
        CREATE INDEX idx_package_id
        ON package_events(package_id)
    """)

    conn.execute("""
        CREATE INDEX idx_route_stop
        ON package_events(route_id, stop_id)
    """)

    conn.commit()

    return conn


# ============================================================
# STEP 1
# ROUTE FEATURES
# ============================================================

def process_routes(route_file, conn):

    print()
    print("========================================")
    print("STEP 1: Processing route data")
    print("========================================")

    count = 0

    with NaNSafeReader(route_file) as f:

        routes = ijson.kvitems(f, "")

        for route_id, route_info in routes:

            stops = route_info.get(
                "stops",
                {}
            )

            station_code = route_info.get(
                "station_code"
            )

            executor_capacity = safe_float(
                route_info.get(
                    "executor_capacity"
                )
            )

            route_date = route_info.get(
                "date_YYYY_MM_DD"
            )

            # ----------------------------------------------
            # Count delivery stops
            # ----------------------------------------------

            delivery_stops = [
                (stop_id, stop_info)
                for stop_id, stop_info
                in stops.items()
                if stop_info.get("type") != "Station"
            ]

            route_num_stops = len(
                delivery_stops
            )

            # ----------------------------------------------
            # Create one row per stop
            # ----------------------------------------------

            for position, (
                stop_id,
                stop_info
            ) in enumerate(
                delivery_stops,
                start=1
            ):

                zone_id = stop_info.get(
                    "zone_id"
                )

                latitude = safe_float(
                    stop_info.get("lat")
                )

                longitude = safe_float(
                    stop_info.get("lng")
                )

                position_ratio = (
                    position / route_num_stops
                    if route_num_stops
                    else 0
                )

                remaining_stops = (
                    route_num_stops - position
                )

                conn.execute("""
    INSERT INTO stops (

        route_id,
        stop_id,
        station_code,
        executor_capacity,
        route_date,
        zone_id,
        latitude,
        longitude,
        route_num_stops,
        route_num_packages,
        stop_package_count,
        stop_total_weight,
        stop_avg_weight,
        stop_total_volume,
        stop_avg_volume,
        total_service_time,
        has_time_window,
        window_duration_sec,
        window_start_hour,
        window_end_hour,
        stop_position,
        stop_position_ratio,
        remaining_stops

    )

    VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    )

""",  (
    route_id,
    stop_id,

    station_code,
    executor_capacity,

    route_date,

    zone_id,
    latitude,
    longitude,

    route_num_stops,
    0,

    0,

    0,
    0,

    0,
    0,

    0,

    0,
    0,

    None,
    None,

    position,
    position_ratio,
    remaining_stops
))

            count += 1

            if count % 500 == 0:

                conn.commit()

                print(
                    f"Routes processed: {count}"
                )

    conn.commit()

    print()
    print(
        f"Finished routes: {count}"
    )


# ============================================================
# STEP 2
# PACKAGE FEATURES
# ============================================================

def process_packages(package_file, conn):

    print()
    print("========================================")
    print("STEP 2: Processing package data")
    print("========================================")

    count = 0

    with NaNSafeReader(package_file) as f:

        routes = ijson.kvitems(f, "")

        for route_id, route_stops in routes:

            route_package_total = 0

            for stop_id, packages in route_stops.items():

                if not isinstance(
                    packages,
                    dict
                ):
                    continue

                package_count = 0

                total_weight = 0.0
                total_volume = 0.0
                total_service_time = 0.0

                window_starts = []
                window_ends = []

                # ------------------------------------------
                # Packages at this stop
                # ------------------------------------------

                for package_id, package in packages.items():

                    if not isinstance(
                        package,
                        dict
                    ):
                        continue

                    package_count += 1

                    route_package_total += 1

                    # --------------------------------------
                    # WEIGHT
                    # --------------------------------------

                    weight_lbs = safe_float(
                        package.get(
                            "weight_lbs"
                        )
                    )

                    weight_kg = (
                        weight_lbs * 0.453592
                    )

                    total_weight += weight_kg

                    # --------------------------------------
                    # VOLUME
                    # --------------------------------------

                    dimensions = package.get(
                        "dimensions",
                        {}
                    )

                    length = safe_float(
                        dimensions.get(
                            "length_cm"
                        )
                    )

                    width = safe_float(
                        dimensions.get(
                            "width_cm"
                        )
                    )

                    height = safe_float(
                        dimensions.get(
                            "height_cm"
                        )
                    )

                    volume = (
                        length *
                        width *
                        height
                    )

                    total_volume += volume

                    # --------------------------------------
                    # SERVICE TIME
                    # --------------------------------------

                    service_time = safe_float(
                        package.get(
                            "planned_service_time_seconds"
                        )
                    )

                    total_service_time += (
                        service_time
                    )

                    # --------------------------------------
                    # TIME WINDOW
                    # --------------------------------------

                    time_window = package.get(
                        "time_window",
                        {}
                    )

                    start = time_window.get(
                        "start_time_utc"
                    )

                    end = time_window.get(
                        "end_time_utc"
                    )

                    if start:
                        window_starts.append(
                            start
                        )

                    if end:
                        window_ends.append(
                            end
                        )

                    # --------------------------------------
                    # EVENT STATUS
                    #
                    # Keep this only if it exists.
                    # --------------------------------------

                    scan_status = (
                        package.get(
                            "scan_status"
                        )
                        or
                        package.get(
                            "status"
                        )
                    )

                    if scan_status:

                        conn.execute("""
                            INSERT INTO package_events (

                                route_id,
                                stop_id,
                                package_id,
                                scan_status

                            )

                            VALUES (?, ?, ?, ?)
                        """, (

                            route_id,
                            stop_id,
                            package_id,
                            str(scan_status)

                        ))

                # ------------------------------------------
                # Aggregation
                # ------------------------------------------

                avg_weight = (
                    total_weight /
                    package_count
                    if package_count
                    else 0
                )

                avg_volume = (
                    total_volume /
                    package_count
                    if package_count
                    else 0
                )

                has_time_window = int(
                    bool(
                        window_starts
                        or
                        window_ends
                    )
                )

                window_duration = 0

                start_hour = None
                end_hour = None

                # ------------------------------------------
                # Start
                # ------------------------------------------

                start_dates = [
                    parse_datetime(x)
                    for x in window_starts
                ]

                start_dates = [
                    x for x in start_dates
                    if x is not None
                ]

                if start_dates:

                    earliest = min(
                        start_dates
                    )

                    start_hour = (
                        earliest.hour
                        +
                        earliest.minute / 60
                    )

                # ------------------------------------------
                # End
                # ------------------------------------------

                end_dates = [
                    parse_datetime(x)
                    for x in window_ends
                ]

                end_dates = [
                    x for x in end_dates
                    if x is not None
                ]

                if end_dates:

                    latest = max(
                        end_dates
                    )

                    end_hour = (
                        latest.hour
                        +
                        latest.minute / 60
                    )

                # ------------------------------------------
                # Window duration
                # ------------------------------------------

                if (
                    start_hour is not None
                    and
                    end_hour is not None
                ):

                    window_duration = max(
                        0,
                        (
                            end_hour
                            -
                            start_hour
                        ) * 3600
                    )

                # ------------------------------------------
                # UPDATE STOP
                # ------------------------------------------

                conn.execute("""
                    UPDATE stops

                    SET

                        stop_package_count = ?,

                        stop_total_weight = ?,
                        stop_avg_weight = ?,

                        stop_total_volume = ?,
                        stop_avg_volume = ?,

                        total_service_time = ?,

                        has_time_window = ?,

                        window_duration_sec = ?,

                        window_start_hour = ?,
                        window_end_hour = ?

                    WHERE

                        route_id = ?
                        AND
                        stop_id = ?

                """, (

                    package_count,

                    total_weight,
                    avg_weight,

                    total_volume,
                    avg_volume,

                    total_service_time,

                    has_time_window,

                    window_duration,

                    start_hour,
                    end_hour,

                    route_id,
                    stop_id
                ))

            # ----------------------------------------------
            # Update total packages for the whole route
            # ----------------------------------------------

            conn.execute("""
                UPDATE stops

                SET route_num_packages = ?

                WHERE route_id = ?

            """, (
                route_package_total,
                route_id
            ))

            count += 1

            if count % 500 == 0:

                conn.commit()

                print(
                    f"Package stop groups processed: {count}"
                )

    conn.commit()

    print()
    print(
        f"Finished package processing: {count}"
    )


# ============================================================
# STEP 3
# INSPECT EVENTS
# ============================================================

def inspect_events(conn):

    print()
    print("========================================")
    print("STEP 3: Inspecting delivery events")
    print("========================================")

    count = conn.execute("""
        SELECT COUNT(*)
        FROM package_events
    """).fetchone()[0]

    print(
        f"Package event records: {count}"
    )

    if count == 0:

        print()
        print(
            "WARNING:"
        )

        print(
            "No scan_status/status was found "
            "inside package_data.json."
        )

        print(
            "We should NOT fabricate the "
            "first-attempt label."
        )

        return False

    print()
    print("Example statuses:")

    rows = conn.execute("""
        SELECT
            scan_status,
            COUNT(*)

        FROM package_events

        GROUP BY scan_status

        LIMIT 20
    """).fetchall()

    for status, count in rows:

        print(
            f"  {status}: {count}"
        )

    return True


# ============================================================
# STEP 4
# BUILD LABEL
# ============================================================

def build_labels(conn):

    print()
    print("========================================")
    print("STEP 4: Building failure labels")
    print("========================================")

    failure_stops = set()

    # --------------------------------------------------------
    # Get attempted delivery events
    # --------------------------------------------------------

    rows = conn.execute("""
        SELECT
            route_id,
            stop_id,
            package_id,
            scan_status

        FROM package_events

        WHERE
            UPPER(scan_status)
            LIKE '%ATTEMPT%'
    """)

    for (
        route_id,
        stop_id,
        package_id,
        status
    ) in rows:

        failure_stops.add(
            (
                route_id,
                stop_id
            )
        )

    print(
        f"Failed-attempt stops found: "
        f"{len(failure_stops)}"
    )

    # --------------------------------------------------------
    # Mark failures
    # --------------------------------------------------------

    if failure_stops:

        conn.executemany("""
            UPDATE stops

            SET first_attempt_failure = 1

            WHERE
                route_id = ?
                AND
                stop_id = ?

        """, list(failure_stops))

    conn.commit()

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total = conn.execute("""
        SELECT COUNT(*)
        FROM stops
    """).fetchone()[0]

    failures = conn.execute("""
        SELECT COUNT(*)
        FROM stops

        WHERE first_attempt_failure = 1
    """).fetchone()[0]

    print()
    print("LABEL SUMMARY")
    print("----------------------------")
    print(
        f"Total stops  : {total}"
    )
    print(
        f"Failures     : {failures}"
    )

    if total:

        print(
            f"Failure rate : "
            f"{failures / total:.4%}"
        )


# ============================================================
# STEP 5
# EXPORT
# ============================================================

def export_dataset(conn, output_file):

    print()
    print("========================================")
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

            stop_total_weight,
            stop_avg_weight,

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

    # --------------------------------------------------------
    # IMPORTANT
    #
    # Write chunks to separate parquet files.
    # This prevents pandas from ever holding the whole
    # dataset in RAM.
    # --------------------------------------------------------

    output_dir = "failure_dataset_parts"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    chunk_number = 0

    for chunk in pd.read_sql_query(
        query,
        conn,
        chunksize=100_000
    ):

        chunk_number += 1

        # ----------------------------------------------
        # categorical columns
        # ----------------------------------------------

        for col in [
            "station_code",
            "zone_id",
            "route_date"
        ]:

            chunk[col] = (
                chunk[col]
                .fillna("UNKNOWN")
                .astype(str)
            )

        # ----------------------------------------------
        # numeric columns
        # ----------------------------------------------

        numeric_columns = [

            "executor_capacity",

            "latitude",
            "longitude",

            "route_num_stops",
            "route_num_packages",

            "stop_package_count",

            "stop_total_weight",
            "stop_avg_weight",

            "stop_total_volume",
            "stop_avg_volume",

            "total_service_time",

            "has_time_window",
            "window_duration_sec",

            "window_start_hour",
            "window_end_hour",

            "stop_position",
            "stop_position_ratio",
            "remaining_stops",

            "first_attempt_failure"
        ]

        for col in numeric_columns:

            chunk[col] = pd.to_numeric(
                chunk[col],
                errors="coerce"
            )

        output_path = os.path.join(
            output_dir,
            f"part_{chunk_number:04d}.parquet"
        )

        chunk.to_parquet(
            output_path,
            index=False
        )

        print(
            f"Written {output_path} "
            f"({len(chunk):,} rows)"
        )

        del chunk

    print()
    print(
        f"Dataset parts written to: "
        f"{output_dir}/"
    )

    print()
    print(
        "You can combine them later without "
        "loading the raw JSON again."
    )


# ============================================================
# MAIN
# ============================================================

def main(data_dir):

    route_file = os.path.join(
        data_dir,
        "model_build_inputs",
        "route_data.json"
    )

    package_file = os.path.join(
        data_dir,
        "model_build_inputs",
        "package_data.json"
    )

    if not os.path.exists(route_file):

        raise FileNotFoundError(
            f"Route file not found:\n{route_file}"
        )

    if not os.path.exists(package_file):

        raise FileNotFoundError(
            f"Package file not found:\n{package_file}"
        )

    print()
    print("==============================================")
    print(" RAM-EFFICIENT FAILURE DATASET BUILDER")
    print("==============================================")

    print()
    print(
        f"Route file:\n{route_file}"
    )

    print()
    print(
        f"Package file:\n{package_file}"
    )

    conn = create_database(
        DB_FILE
    )

    try:

        # ----------------------------------------------
        # Routes
        # ----------------------------------------------

        process_routes(
            route_file,
            conn
        )

        # ----------------------------------------------
        # Packages
        # ----------------------------------------------

        process_packages(
            package_file,
            conn
        )

        # ----------------------------------------------
        # Event inspection
        # ----------------------------------------------

        has_events = inspect_events(
            conn
        )

        # ----------------------------------------------
        # Only build labels if events exist
        # ----------------------------------------------

        if has_events:

            build_labels(
                conn
            )

        else:

            print()
            print(
                "STOPPING BEFORE LABEL CREATION."
            )

            print(
                "We need to inspect where the "
                "delivery scan status is stored."
            )

            return

        # ----------------------------------------------
        # Export
        # ----------------------------------------------

        export_dataset(
            conn,
            OUTPUT_FILE
        )

    finally:

        conn.close()

    print()
    print("==============================================")
    print(" DONE")
    print("==============================================")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_dir",
        default=DEFAULT_DATA_DIR
    )

    args = parser.parse_args()

    main(
        args.data_dir
    )