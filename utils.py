import os
import random
import pandas as pd
import numpy as np
from collections import namedtuple

Delivery = namedtuple('Delivery',
                      'id goods_type weight_kg volume_m3 goods_ready delivery_window gha pickup_location '
                      'available_weight available_volume loaded_goods_ids')

def time_to_slot(minutes: int, slot_duration: int) -> int:
    return minutes // slot_duration

def generate_instances(num_instances: int, i_name: str,
                       goods_types: list,
                       locations: list,
                       min_weight: int,
                       max_weight: int,
                       min_volume: float,
                       max_volume: float,
                       deliveries_per_instance: int,
                       max_gha: int,
                       max_ready_offset_min: int,
                       delivery_window_min: int,
                       delivery_window_duration_min: int,
                       seed: int = 12345,
                       slot_duration: int = 15):
    """
    Generate delivery instances with discretized time fields.
    Time is represented in integer slots of `slot_duration` minutes.

    Output:
      - Instances/*.csv (1 per instance)
      - Instances/distance_matrix.csv
      - Instances/incompatibility_pairs.csv
    """

    random.seed(seed)
    np.random.seed(seed)

    os.makedirs("Instances", exist_ok=True)

    # Incompatibilities
    # all_pairs = [(a, b) for i, a in enumerate(goods_types) for b in goods_types[i+1:]]
    # num_incompat = int(len(all_pairs) * incompatibility_pairs_ratio)
    # incompatibility_pairs = set(random.sample(all_pairs, num_incompat))

    # Distance matrix
    locs = locations + ["Mpx"] if "Mpx" not in locations else locations
    n_loc = len(locs)
    dist_matrix = np.zeros((n_loc, n_loc), dtype=int)
    for i in range(n_loc):
        for j in range(i+1, n_loc):
            dist = random.randint(10, 100)
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist
    dist_df = pd.DataFrame(dist_matrix, index=locs, columns=locs)
    dist_df.to_csv(f"Instances/{i_name}/distance_matrix.csv")

    # Save incompatibility pairs
    #incompat_df = pd.DataFrame(list(incompatibility_pairs), columns=["GoodsType1", "GoodsType2"])
    #incompat_df.to_csv("Instances/incompatibility_pairs.csv", index=False)

    for inst_id in range(num_instances):
        deliveries = []
        total_weight = 0
        total_volume = 0

        for i in range(deliveries_per_instance):
            # Base: 8:00 → slot = 32 (8*60 / slot_duration)
            ready_offset_min = random.randint(0, max_ready_offset_min)
            window_offset_min = random.randint(delivery_window_min, delivery_window_min + 60)
            window_duration_min = delivery_window_duration_min

            ready_slot = time_to_slot(8*60 + ready_offset_min, slot_duration)
            window_start_slot = time_to_slot(8*60 + ready_offset_min + window_offset_min, slot_duration)
            window_end_slot = window_start_slot + time_to_slot(window_duration_min, slot_duration)

            weight = random.randint(min_weight, max_weight)
            volume = round(random.uniform(min_volume, max_volume), 2)

            total_weight += weight
            total_volume += volume

            deliveries.append(Delivery(
                id=f"D{i}",
                goods_type=random.choice(goods_types),
                weight_kg=weight,
                volume_m3=volume,
                goods_ready=ready_slot,
                delivery_window=(window_start_slot, window_end_slot),
                gha=f"GHA{random.randint(1, max_gha)}",
                pickup_location=random.choice(locations),
                available_weight=weight,
                available_volume=volume,
                loaded_goods_ids=[]
            ))

        df_del = pd.DataFrame([{
            "id": d.id,
            "goods_type": d.goods_type,
            "weight_kg": d.weight_kg,
            "volume_m3": d.volume_m3,
            "goods_ready_slot": d.goods_ready,
            "window_start_slot": d.delivery_window[0],
            "window_end_slot": d.delivery_window[1],
            "gha": d.gha,
            "pickup_location": d.pickup_location,
            "available_weight": d.available_weight,
            "available_volume": d.available_volume,
            "loaded_goods_ids": ",".join(d.loaded_goods_ids)
        } for d in deliveries])

        filename = f"Instances/{i_name}/Instance_{inst_id}.csv"
        df_del.to_csv(filename, index=False)
        print(f"Saved instance {inst_id+1}/{num_instances} to {filename}")


def read_instance_files(instances_folder):
    """
    Read all instance CSVs, distance matrix and incompatibility pairs from folder,
    using discretized time (minutes from midnight as integers).

    Args:
        instances_folder: folder path containing CSV files.

    Returns:
        tuple: (list_of_deliveries_lists, distance_df, incompatibility_set)
    """
    deliveries_list = []
    incompatibility_set = set()
    for file in sorted(os.listdir(instances_folder)):
        if file.startswith("Instance_") and file.endswith(".csv"):
            path = os.path.join(instances_folder, file)
            df = pd.read_csv(path)

            df.columns = [col.strip().lower() for col in df.columns]

            deliveries = []
            for _, row in df.iterrows():
                deliveries.append(Delivery(
                    id=row['id'],
                    goods_type=row['goods_type'],
                    weight_kg=float(row['weight_kg']),
                    volume_m3=float(row['volume_m3']),
                    goods_ready=int(row['goods_ready_slot']),
                    delivery_window=(int(row['window_start_slot']), int(row['window_end_slot'])),
                    gha=row['gha'],
                    pickup_location=row['pickup_location'],
                    available_weight=float(row['available_weight']),
                    available_volume=float(row['available_volume']),
                    loaded_goods_ids=row['loaded_goods_ids'].split(',') if isinstance(row['loaded_goods_ids'], str) and row['loaded_goods_ids'] else []
                ))
            deliveries_list.append(deliveries)

    dist_df = pd.read_csv(os.path.join(instances_folder, "distance_matrix.csv"), index_col=0)
    #incompat_df = pd.read_csv(os.path.join(instances_folder, "incompatibility_pairs.csv"))
    #incompatibility_set = set(zip(incompat_df["GoodsType1"], incompat_df["GoodsType2"]))

    return deliveries_list, dist_df, incompatibility_set



