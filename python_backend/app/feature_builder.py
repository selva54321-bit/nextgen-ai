import math
import pandas as pd


def derive_features(request):

    route = request.route
    stop = request.stop

    packages = stop.packages

    # -------------------------
    # Package features
    # -------------------------

    package_count = len(packages)

    volumes = []

    total_service_time = 0

    window_starts = []
    window_ends = []

    for pkg in packages:

        d = pkg.dimensions

        volume = (
            d.depth_cm
            * d.width_cm
            * d.height_cm
        )

        volumes.append(volume)

        total_service_time += (
            pkg.planned_service_time_seconds
        )

        if pkg.time_window:

            if pkg.time_window.start_time_utc:
                window_starts.append(
                    pd.to_datetime(
                        pkg.time_window.start_time_utc,
                        utc=True
                    )
                )

            if pkg.time_window.end_time_utc:
                window_ends.append(
                    pd.to_datetime(
                        pkg.time_window.end_time_utc,
                        utc=True
                    )
                )

    # -------------------------
    # Volume
    # -------------------------

    total_volume = sum(volumes)

    avg_volume = (
        total_volume / package_count
        if package_count > 0
        else 0
    )

    # -------------------------
    # Time window
    # -------------------------

    has_time_window = int(
        len(window_starts) > 0
        and len(window_ends) > 0
    )

    window_duration_sec = 0
    window_start_hour = None
    window_end_hour = None

    if has_time_window:

        earliest_start = min(window_starts)
        latest_end = max(window_ends)

        window_duration_sec = (
            latest_end - earliest_start
        ).total_seconds()

        window_start_hour = (
            earliest_start.hour
            + earliest_start.minute / 60
        )

        window_end_hour = (
            latest_end.hour
            + latest_end.minute / 60
        )

    # -------------------------
    # Day of week
    # -------------------------

    route_date = pd.to_datetime(route.date)

    dow = route_date.dayofweek

    # -------------------------
    # Final model row
    # -------------------------

    features = {

        "station_code":
            route.station_code,

        "executor_capacity":
            route.executor_capacity_cm3,

        "zone_id":
            stop.zone_id,

        "route_num_stops":
            route.stops,

        "route_num_packages":
            route.route_num_packages,

        "stop_package_count":
            package_count,

        "stop_total_volume":
            total_volume,

        "stop_avg_volume":
            avg_volume,

        "total_service_time":
            total_service_time,

        "has_time_window":
            has_time_window,

        "window_duration_sec":
            window_duration_sec,

        "window_start_hour":
            window_start_hour,

        "window_end_hour":
            window_end_hour,

        "dow":
            dow
    }

    return pd.DataFrame([features])