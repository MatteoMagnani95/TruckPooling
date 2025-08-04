from utils import *
from itertools import combinations
from typing import List, Dict, Set
import pandas as pd


MAX_PICKUPS = 5  # max number of pickups allowed in a single trip
MAX_WAIT_SLOT = 2 # max 2 slots wait time allowed
MAX_DISTANCE_INCREASE_RATIO = 0.2  # max 20% detour allowed


def compute_trip_distance(loc_sequence: List[str], dist_matrix: pd.DataFrame) -> float:
    dist = 0.0
    for i in range(len(loc_sequence) - 1):
        dist += dist_matrix.at[loc_sequence[i], loc_sequence[i + 1]]
    return dist


def max_wait_time(deliveries: List[Delivery]) -> float:
    times = sorted(d.goods_ready for d in deliveries)
    if len(times) < 2:
        return 0.0
    waits = [(t2 - t1) for t1, t2 in zip(times, times[1:])]
    return max(waits)


def check_capacity(deliveries: List[Delivery], max_weight: float, max_volume: float) -> bool:
    total_weight = sum(d.weight_kg for d in deliveries)
    total_volume = sum(d.volume_m3 for d in deliveries)
    # Check also available weight and volume individually (assuming available_* is capacity left)
    avail_weight_ok = all(d.available_weight >= d.weight_kg for d in deliveries)
    avail_volume_ok = all(d.available_volume >= d.volume_m3 for d in deliveries)
    return total_weight <= max_weight and total_volume <= max_volume and avail_weight_ok and avail_volume_ok


def check_time_window(deliveries: List[Delivery]) -> bool:
    latest_ready = max(d.goods_ready for d in deliveries)
    earliest_due = min(d.delivery_window[1] for d in deliveries)
    return latest_ready <= earliest_due


def check_incompatibility(goods_types: List[str], incompat_set: Set[tuple]) -> bool:
    for i, g1 in enumerate(goods_types):
        for g2 in goods_types[i + 1:]:
            if (g1, g2) in incompat_set or (g2, g1) in incompat_set:
                return False
    return True


def generate_feasible_trips(deliveries: List[Delivery],
                            transporter_id: str,
                            capacity_kg: float,
                            capacity_m3: float,
                            dist_matrix: pd.DataFrame,
                            incompat_set: Set[tuple]) -> List[Dict]:
    feasible_trips = []
    for r in range(1, MAX_PICKUPS + 1):
        for combo in combinations(deliveries, r):
            if not check_capacity(combo, capacity_kg, capacity_m3):
                continue
            if not check_time_window(combo):
                continue
            goods_types = [d.goods_type for d in combo]
            #if not check_incompatibility(goods_types, incompat_set):
            #    continue
            if max_wait_time(combo) > MAX_WAIT_SLOT:
                continue

            loc_sequence = [d.pickup_location for d in combo] + ["Mpx"]
            trip_distance = compute_trip_distance(loc_sequence, dist_matrix)

            direct_distances = sum(compute_trip_distance([d.pickup_location, "Mpx"], dist_matrix) for d in combo)
            if trip_distance > direct_distances * (1 + MAX_DISTANCE_INCREASE_RATIO):
                continue

            score = trip_distance / len(combo)
            feasible_trips.append({
                "transporter_id": transporter_id,
                "shipment_ids": [d.id for d in combo],
                "total_km": trip_distance,
                "total_weight": sum(d.weight_kg for d in combo),
                "total_volume": sum(d.volume_m3 for d in combo),
                "score": score
            })

    return feasible_trips
