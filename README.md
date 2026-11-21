# Mini-Courier Planner (DAA Capstone, ETCCDA302)

Prototype that takes parcels + a road network and produces a prioritised, optimally packed delivery trip with an ordered route.

## Run
```
pip install matplotlib        # only needed for benchmark.py
python courier_planner.py data/small.json    # demo with full DP/route output
python courier_planner.py data/large.json    # 500 parcels, 200 nodes
python benchmark.py                          # tests + runtime chart -> outputs/runtime_chart.png
```
Python 3.8+. `courier_planner.py` uses only the standard library.

## Phase 1 - Design
**Parcel:** `pid, weight (kg, int), value (priority score), deadline (hours), dest (graph node)`.
**Graph:** undirected weighted adjacency list `{u: [(v, travel_time), ...]}`; node 0 is the depot.
**Pipeline:**
```
parcels --merge sort (deadline, then value)--> ordered list
        --0/1 knapsack DP (capacity = van load)--> parcels for this trip
        --destinations--> Dijkstra distances between stops
        --nearest-neighbour TSP--> route depot -> stops -> depot
```
| Step | Algorithm | Why | Time |
|---|---|---|---|
| Prioritise | Merge sort | Stable, guaranteed O(n log n) | O(n log n) |
| Pack | 0/1 knapsack DP | Parcels can't be split; greedy is not optimal | O(nW) time & space |
| Shortest paths | Dijkstra (heap) | Non-negative road weights | O((V+E) log V) |
| Route | Nearest neighbour | TSP is NP-hard; fast heuristic | O(k (V+E) log V) |

## Phase 2 - Results (data/small.json, capacity 30 kg)
Sorted by deadline: P2, P4, P9, P8, P6, P5, P7, P3, P1, P0.
Knapsack optimum = **282**, selected **P8, P6, P1, P0** (28/30 kg). The DP table is returned by `knapsack()` for inspection; items are recovered by backtracking.

## Phase 3 - Results
Stops (destinations of selected parcels): nodes 7, 1, 6, 3.
Route: **0 -> 7 -> 1 -> 6 -> 3 -> 0**, length **37**.
Road-level path: 0 -> 7 -> 2 -> 1 -> 6 -> 3 -> 5 -> 0.

## Phase 4 - Testing and performance
Correctness (benchmark.py): knapsack matches brute force on 20 random cases; merge sort matches Python's `sorted`; nearest-neighbour route is on average 1.068x optimal (worst 1.26x) on 20 brute-forced instances.

| n | merge sort | built-in sorted | knapsack DP | Dijkstra | NN-TSP |
|---|---|---|---|---|---|
| 50 | 0.000074 | 0.000011 | 0.001015 | 0.000050 | 0.001104 |
| 100 | 0.000153 | 0.000022 | 0.004259 | 0.000095 | 0.003491 |
| 200 | 0.000346 | 0.000046 | 0.017892 | 0.000238 | 0.014254 |
| 400 | 0.000778 | 0.000148 | 0.075121 | 0.000731 | 0.066644 |
| 800 | 0.001711 | 0.000194 | 0.328760 | 0.001233 | 0.309874 |

(seconds; capacity grows with n.) See `outputs/runtime_chart.png`.

**Observations:** knapsack dominates and grows ~4x per doubling of n (since capacity also doubles, O(nW) is quadratic). Merge sort and Dijkstra scale near-linearly. Pure-Python merge sort is ~8x slower than built-in Timsort (C implementation).
**Improvements:** 1D rolling knapsack array (O(W) space, loses backtracking unless bitsets are kept); NumPy-vectorised DP rows; precompute all-pairs distances only for the stops; apply 2-opt after nearest neighbour to shrink route length; enforce deadlines inside the route order.

## Phase 5 - Files
`courier_planner.py` (system), `benchmark.py` (tests/charts), `data/` (sample datasets), `outputs/` (run traces, chart). Add your own screenshots of the terminal runs for submission.
