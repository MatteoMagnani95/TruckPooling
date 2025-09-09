import os
import time
from utils import generate_instances, read_instance_files
from Trip_generation import generate_feasible_trips
from Set_covering import solve_set_covering
from collections import namedtuple

Delivery = namedtuple('Delivery',
                      'id goods_type weight_kg volume_m3 goods_ready delivery_window gha pickup_location '
                      'available_weight available_volume loaded_goods_ids')

NUM_TRANSPORTERS = 10
MAX_PICKUPS = 3

i_dir = "Test"
LOGDIR = os.path.join("Output", i_dir, "Logs")
SOLDIR = os.path.join("Output", i_dir, "Solutions")
INSDIR = os.path.join("Instances", i_dir)

os.makedirs(SOLDIR, exist_ok=True)
os.makedirs(LOGDIR, exist_ok=True)
os.makedirs(INSDIR, exist_ok=True)

if __name__ == "__main__":
    generate_instances(
        num_instances=10, i_name=i_dir,
        goods_types=["Pharma"],
        locations=["Linate", "Bergamo", "Piacenza", "Varese"],
        min_weight=200,
        max_weight=1000,
        min_volume=0.5,
        max_volume=3.0,
        deliveries_per_instance=5,
        max_gha=3,
        max_ready_offset_min=120,
        delivery_window_min=30,
        delivery_window_duration_min=60)

    deliveries_list, dist_df, incompat_set = read_instance_files(INSDIR)
    print(f"Loaded {len(deliveries_list)} instances")

    for idx, deliveries in enumerate(deliveries_list):
        i_name = f"instance_{idx}"
        start_time = time.time()

        # Transporter info
        capacity_kg = 4000
        capacity_m3 = 15.0

        # Generate feasible trips
        feasible_trips = generate_feasible_trips(
            deliveries=deliveries,
            capacity_kg=capacity_kg,
            capacity_m3=capacity_m3,
            dist_matrix=dist_df,
            incompat_set=incompat_set
        )
        # write feasible trips to a log file
        with open(os.path.join(LOGDIR, f"{i_name}.log"), "w") as f:
            f.write(f"Feasible trips for {i_name}:\n")
            for trip in feasible_trips:
                f.write(f"Source: {trip['source']}, total_km: {trip['total_km']:.2f}, "
                        f"total_weight: {trip['total_weight']:.2f}, "
                        f"total_volume: {trip['total_volume']:.2f}, score: {trip['score']:.2f}\n")
                f.write(f"Deliveries: {', '.join(trip['shipment_ids'])}\n\n")
        print(f"Generated {len(feasible_trips)} feasible trips for {i_name}")

        # print the matrix of feasible trips
        print("Feasible trips matrix:")
        for trip in feasible_trips:
            print(f"Source: {trip['source']}, Total KM: {trip['total_km']:.2f}, "
                  f"Weight: {trip['total_weight']:.2f}, Volume: {trip['total_volume']:.2f}, "
                  f"score: {trip['score']:.2f}, Deliveries: {', '.join(trip['shipment_ids'])}")

        # Solve set covering
        solutions = solve_set_covering(LOGDIR, i_name, feasible_trips, deliveries)

        elapsed = time.time() - start_time

        for sol in solutions:
            solnum = sol["solution_number"]
            sol_filename = os.path.join(SOLDIR, f"{i_name}_sol{solnum}.sol")
            with open(sol_filename, "w") as fsol:
                fsol.write(f"# Solution {solnum} for {i_name}\n")
                fsol.write(f"# Objective value: {sol['obj']:.6f}\n")
                fsol.write(f"# Number of deliveries: {len(deliveries)}\n")
                fsol.write(f"# Number of feasible trips generated: {len(feasible_trips)}\n")
                fsol.write(f"# Number of trips selected: {len(sol['selected_trip_indices'])}\n\n")
                for t in sol["selected_trips"]:
                    fsol.write(f"Source: {t['source']}, total_km: {t['total_km']:.2f}, "
                               f"weight: {t['total_weight']:.2f}, volume: {t['total_volume']:.2f}, "
                               f"score: {t['score']:.2f}\n")
                    fsol.write(f"Deliveries: {', '.join(t['shipment_ids'])}\n\n")

        # --- Append to one master log file ------------------------------------------
        log_filename = os.path.join(LOGDIR, f"{i_name}.log")
        with open(log_filename, "a") as flog:
            flog.write(f"\n=== Summary for {i_name} ===\n")
            flog.write(f"Deliveries count: {len(deliveries)}\n")
            flog.write(f"Feasible trips generated: {len(feasible_trips)}\n")
            flog.write(f"Solutions in pool: {len(solutions)}\n")
            for sol in solutions:
                flog.write(f"Solution {sol['solution_number']} | "
                           f"obj={sol['obj']:.6f}, "
                           f"trips={len(sol['selected_trip_indices'])}, "
                           f"total_km={sol['total_km']:.2f}\n")