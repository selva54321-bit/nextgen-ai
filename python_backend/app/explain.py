FACTOR_NAMES = {

    "total_service_time":
        "High planned service time",

    "route_num_stops":
        "Large number of route stops",

    "route_num_packages":
        "Large route package load",

    "stop_package_count":
        "High package count at stop",

    "stop_total_volume":
        "High total package volume",

    "stop_avg_volume":
        "Large average package size",

    "window_duration_sec":
        "Tight delivery time window",

    "window_start_hour":
        "Early delivery window",

    "window_end_hour":
        "Late delivery window",

    "has_time_window":
        "Delivery time-window constraint",

    "executor_capacity":
        "Vehicle capacity",

    "station_code":
        "Dispatch station",

    "zone_id":
        "Delivery zone",

    "dow":
        "Day of week"
}


FACTOR_DESCRIPTIONS = {

    "total_service_time":
        "The planned service time at the delivery stop is relatively high, which may increase the time required to complete the delivery.",

    "route_num_stops":
        "The route contains many delivery stops, increasing the workload and the possibility of delays later in the route.",

    "route_num_packages":
        "The route contains a large number of packages, which may increase handling time and operational workload.",

    "stop_package_count":
        "This delivery stop contains many packages, which may require additional handling and service time.",

    "stop_total_volume":
        "The total volume of packages at this stop is high, potentially increasing handling and unloading time.",

    "stop_avg_volume":
        "The average package size at this stop is relatively large, which may increase handling difficulty and service time.",

    "window_duration_sec":
        "The delivery time window is relatively tight, leaving less flexibility to accommodate route delays.",

    "window_start_hour":
        "The delivery is scheduled during an early time window, which may affect delivery feasibility depending on route conditions.",

    "window_end_hour":
        "The delivery is scheduled during a later time window, potentially increasing sensitivity to delays accumulated earlier in the route.",

    "has_time_window":
        "The shipment has a delivery time-window constraint, limiting the flexibility available when planning the route.",

    "executor_capacity":
        "Vehicle capacity constraints may affect how many packages can be carried and delivered efficiently on the route.",

    "station_code":
        "The dispatch station associated with this shipment may influence route characteristics and delivery operations.",

    "zone_id":
        "The delivery zone has characteristics that may influence delivery time, route complexity, or historical delivery performance.",

    "dow":
        "The day of the week may influence traffic, delivery demand, customer availability, and route conditions."
}


def get_top_factors(model, pool, feature_names, top_k=3):

    shap_values = model.get_feature_importance(
        pool,
        type="ShapValues"
    )

    # Last column is the model's expected value.
    contributions = shap_values[0][:-1]

    factors = []

    for feature, contribution in zip(
        feature_names,
        contributions
    ):

        factors.append({
            "feature": feature,
            "contribution": float(contribution)
        })

    # Strongest absolute contributions
    factors.sort(
        key=lambda x: abs(x["contribution"]),
        reverse=True
    )

    result = []

    for factor in factors[:top_k]:

        feature = factor["feature"]
        contribution = factor["contribution"]

        result.append({

            "feature": feature,

            "factor":
                FACTOR_NAMES.get(
                    feature,
                    feature
                ),

            "description":
                FACTOR_DESCRIPTIONS.get(
                    feature,
                    "This feature contributed to the predicted delivery risk."
                ),

            "impact":
                "increases_risk"
                if contribution > 0
                else "reduces_risk",

            "contribution":
                contribution
        })

    return result