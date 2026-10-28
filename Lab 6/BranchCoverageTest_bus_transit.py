"""Branch coverage suite for the bus transit fare module."""

from bus_transit_fare import inspect_smartcard_turnstiles, process_commute_manifest


def test_regular_local_fare():
    result = process_commute_manifest(
        [{"route_active": True, "route_type": "local", "commuters": [{"zones": 2}]}], 2.0
    )
    assert result == {"total_fare": 4.5, "status": "COMPLETED"}


def test_inactive_and_unknown_routes_are_not_charged():
    result = process_commute_manifest(
        [
            {"route_active": False, "route_type": "express", "commuters": [{"zones": 1}]},
            {"route_active": True, "route_type": "night", "commuters": [{"zones": 1}]},
        ],
        2.0,
    )
    assert result == {"total_fare": 0.0, "status": "ZERO_RIDERSHIP"}


def test_route_prices_passenger_concessions_and_priority_fee():
    manifests = [
        {"route_active": True, "route_type": "express", "commuters": [{"zones": 2, "type": "student"}]},
        {"route_active": True, "route_type": "shuttle", "commuters": [{"zones": 3, "type": "senior"}]},
        {
            "route_active": True,
            "route_type": "local",
            "priority_boarding": True,
            "commuters": [{"zones": 2, "type": "visitor"}],
        },
    ]
    assert process_commute_manifest(manifests, 1.25) == {
        "total_fare": 13.1,
        "status": "COMPLETED",
    }


def test_invalid_zones_and_blacklisted_express_card():
    manifests = [
        {
            "route_active": True,
            "route_type": "express",
            "priority_boarding": True,
            "commuters": [
                {"zones": 0},
                {"zones": 2, "blacklisted": True},
                {"zones": 2},
            ],
        }
    ]
    # The blacklisted express card cancels commuter fares, but priority is added afterward.
    assert process_commute_manifest(manifests, 1.0) == {
        "total_fare": 1.0,
        "status": "COMPLETED",
    }


def test_blacklisted_non_express_card_and_rejected_rides_audit():
    manifests = [
        {"route_active": True, "route_type": "local", "commuters": [{"zones": 1, "blacklisted": True}]}
        for _ in range(5)
    ]
    assert process_commute_manifest(manifests, 0) == {
        "total_fare": 0.0,
        "status": "AUDIT_REJECTED",
    }


def test_rejects_invalid_manifest_argument():
    try:
        process_commute_manifest("not a list", 1.0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for a non-list manifests argument")


def test_rejects_negative_booking_fee():
    try:
        process_commute_manifest([], -0.01)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for a negative booking fee")


def test_empty_turnstile_data():
    assert inspect_smartcard_turnstiles([]) == "NO_DATA"


def test_two_consecutive_high_failure_readings_jam_a_turnstile():
    assert inspect_smartcard_turnstiles([[4, 5]]) == "TURNSTILE_JAM"


def test_normal_or_separated_high_readings_remain_operational():
    assert inspect_smartcard_turnstiles([[4, 3, 4], [0, 2, 3]]) == "OPERATIONAL"

