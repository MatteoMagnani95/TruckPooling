import os
import time
from utils import generate_instances, read_instance_files
from Trip_generation import generate_feasible_trips
from Set_covering import solve_set_covering
from collections import namedtuple

Delivery = namedtuple('Delivery',
                      'id goods_type weight_kg volume_m3 goods_ready delivery_window gha pickup_location '
                      'available_weight available_volume loaded_goods_ids')

NUM_TRANSPORTERS = 5
MAX_PICKUPS = 3

# Ensure output dirs exist
os.makedirs("Output/Sols", exist_ok=True)
os.makedirs("Output/Logs", exist_ok=True)

if __name__ == "__main__":
    generate_instances(
        num_instances=3,
        goods_types=["Pharma", "Chemical", "Food", "Fragile"],
        locations=["Linate", "Bergamo", "Piacenza", "Varese"],
        min_weight=200,
        max_weight=1000,
        min_volume=0.5,
        max_volume=3.0,
        deliveries_per_instance=5,
        max_gha=3,
        max_ready_offset_min=120,
        delivery_window_min=30,
        delivery_window_duration_min=60,
        incompatibility_pairs_ratio=0.3,
        seed=42
    )

    deliveries_list, dist_df, incompat_set = read_instance_files()
    print(f"Loaded {len(deliveries_list)} instances")

    for idx, deliveries in enumerate(deliveries_list):
        i_name = f"instance_{idx}"
        start_time = time.time()

        # Transporter info
        transporter_id = f"T{idx}"
        capacity_kg = 4000
        capacity_m3 = 15.0

        # Generate feasible trips
        feasible_trips = generate_feasible_trips(
            deliveries=deliveries,
            transporter_id=transporter_id,
            capacity_kg=capacity_kg,
            capacity_m3=capacity_m3,
            dist_matrix=dist_df,
            incompat_set=incompat_set
        )
        # Solve set covering
        selected_trips = solve_set_covering(i_name, feasible_trips, deliveries)

        elapsed = time.time() - start_time

        # Save solution .sol file
        sol_path = f"Output/Sols/{i_name}.sol"
        with open(sol_path, "w") as fsol:
            fsol.write(f"# Solution for {i_name}\n")
            fsol.write(f"# Number of deliveries: {len(deliveries)}\n")
            fsol.write(f"# Number of feasible trips generated: {len(feasible_trips)}\n")
            fsol.write(f"# Number of trips selected: {len(selected_trips)}\n\n")
            for t in selected_trips:
                fsol.write(f"Trip transporter_id: {t['transporter_id']}, total_km: {t['total_km']:.2f}, "
                           f"weight: {t['total_weight']:.2f}, volume: {t['total_volume']:.2f}\n")
                fsol.write(f"Deliveries: {', '.join(t['shipment_ids'])}\n\n")

        # Save log .log file
        log_path = f"Output/Logs/{i_name}.log"
        with open(log_path, "a") as flog:
            flog.write(f"Deliveries count: {len(deliveries)}\n")
            flog.write(f"Feasible trips generated: {len(feasible_trips)}\n")
            flog.write(f"Trips selected: {len(selected_trips)}\n")
            flog.write(f"Elapsed time (seconds): {elapsed:.2f}\n")

