"""Phase 4: correctness tests + runtime benchmarks + chart."""
import time, itertools, random
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from courier_planner import *

def timeit(f, *a):
    s = time.perf_counter(); r = f(*a); return time.perf_counter() - s, r

# ---- correctness checks ----
def brute_knap(ps, cap):
    best = 0
    for k in range(len(ps) + 1):
        for c in itertools.combinations(ps, k):
            if sum(p.weight for p in c) <= cap: best = max(best, sum(p.value for p in c))
    return best
for seed in range(20):
    ps = make_parcels(10, 8, seed)
    assert knapsack(ps, 30)[0] == brute_knap(ps, 30), "knapsack mismatch"
    key = lambda p: (p.deadline, -p.value)
    assert [p.pid for p in merge_sort(ps, key)] == [p.pid for p in sorted(ps, key=key)], "sort mismatch"
def brute_tsp(g, stops):
    D = {u: dijkstra(g, u)[0] for u in [0] + stops}
    return min(sum(D[a][b] for a, b in zip((0,) + p, p + (0,))) for p in itertools.permutations(stops))
ratios = []
for seed in range(20):
    g = make_graph(12, seed=seed); stops = random.Random(seed).sample(range(1, 12), 6)
    _, L = nearest_neighbour_route(g, 0, stops); ratios.append(L / brute_tsp(g, stops))
print("Correctness: knapsack == brute force (20 cases), merge sort == sorted (20 cases)")
print(f"NN-TSP vs optimal: avg ratio {sum(ratios)/len(ratios):.3f}, worst {max(ratios):.3f}\n")

# ---- runtime benchmark ----
sizes = [50, 100, 200, 400, 800]
rows = {"merge sort": [], "built-in sorted": [], "knapsack DP": [], "Dijkstra (1 src)": [], "NN-TSP route": []}
for m in sizes:
    nodes = m; ps = make_parcels(m, nodes); g = make_graph(nodes)
    rows["merge sort"].append(timeit(merge_sort, ps, lambda p: (p.deadline, -p.value))[0])
    rows["built-in sorted"].append(timeit(sorted, ps, lambda p: (p.deadline, -p.value))[0] if False else timeit(lambda: sorted(ps, key=lambda p: (p.deadline, -p.value)))[0])
    ordered = prioritize(ps)
    t, (best, chosen, _) = timeit(knapsack, ordered, 5 * m // 2)   # capacity grows with n
    rows["knapsack DP"].append(t)
    rows["Dijkstra (1 src)"].append(timeit(dijkstra, g, 0)[0])
    stops = sorted({p.dest for p in chosen})
    rows["NN-TSP route"].append(timeit(nearest_neighbour_route, g, 0, stops)[0])
print(f"{'n':>6} | " + " | ".join(f"{k:>16}" for k in rows))
for i, m in enumerate(sizes):
    print(f"{m:>6} | " + " | ".join(f"{rows[k][i]:>16.6f}" for k in rows))

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for k, v in rows.items():
    ax[0].plot(sizes, v, marker="o", label=k); ax[1].plot(sizes, v, marker="o", label=k)
ax[0].set_title("Runtime vs input size (linear)"); ax[1].set_title("Runtime vs input size (log scale)")
ax[1].set_yscale("log")
for a in ax: a.set_xlabel("n (parcels = graph nodes)"); a.set_ylabel("seconds"); a.grid(alpha=.3)
ax[0].legend(); plt.tight_layout(); plt.savefig("runtime_chart.png", dpi=130)
