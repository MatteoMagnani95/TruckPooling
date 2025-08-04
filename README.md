# TruckPooling
This repository provides a Python-based solution for optimizing last-mile delivery routing using a set covering approach. Given a set of deliveries, the script generates feasible trip combinations for transporters under capacity and compatibility constraints, and then selects the optimal subset of trips to cover all deliveries with minimal total kilometers traveled.

## Features
Instance Generation: Synthetic delivery instances with customizable parameters.

Feasible Trip Generation: All compatible delivery groupings respecting weight, volume, and incompatibilities.

Set Covering Solver: Selects the minimal-cost set of trips to cover all deliveries.

Logging and Output: Saves both detailed solution files and execution logs for each instance.

## Project Structure
├── main.py                  # Main execution script
├── utils.py                 # Utilities for instance generation and parsing
├── Trip_generation.py       # Feasible trip generation logic
├── Set_covering.py          # Set covering solver
├── Output/
│   ├── Sols/                # Solutions (.sol files)
│   └── Logs/                # Logs (.log files)
### How to Run
Install dependencies (if any external libraries are used).

Run the script:

python main.py
This will:

Generate 3 delivery instances.

For each instance:

Generate all feasible trips under transporter constraints.

Solve the set covering problem to find the best combination of trips.

Output solution details and logs.

## Parameters
Modify main.py to adjust parameters such as:

goods_types, locations

min_weight, max_weight

delivery_window_duration_min

capacity_kg, capacity_m3

incompatibility_pairs_ratio

These control the nature of deliveries, transport capacity, and problem complexity.

## Output Files
For each instance, two files are saved:

Output/Sols/instance_X.sol: Human-readable summary of selected trips.

Output/Logs/instance_X.log: Basic statistics and timing info.
