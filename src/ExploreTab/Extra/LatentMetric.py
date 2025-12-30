import json
import os
import numpy as np
from ExploreTab.BayesTrain import run_bayes_train

def compute_latent_values(designs_file, ratings_file):
    # ---- Load designs (to get number + names) ----
    with open(designs_file, "r") as f:
        designs = json.load(f)

    num_designs = len(designs)
    names = [d["Name"] for d in designs]

    # ---- Load comparisons from designsRatings.txt ----
    # The file contains: comparisons = [(w,l), ...]
    with open(ratings_file, "r") as f:
        text = f.read()

    ns = {}
    exec(text, ns)                     # pulls out variable 'comparisons'
    comparisons = ns["comparisons"]

    # ---- Build A and b for least-squares ----
    M = len(comparisons)
    A = np.zeros((M, num_designs))
    b = np.ones(M)

    for i, (w, l) in enumerate(comparisons):
        A[i, w] =  1.0
        A[i, l] = -1.0

    # ---- Solve A f = b ----
    f, *_ = np.linalg.lstsq(A, b, rcond=None)

    # ---- Center scores ----
    f = f - np.mean(f)

    return names, f


# ---------------------------
# UPDATE designs.txt RATINGS
# ---------------------------
def update_designs_ratings(designs_file, ratings_file, *, decimals=3):
    names, scores = compute_latent_values(designs_file, ratings_file)
    name_to_score = {n: float(s) for n, s in zip(names, scores)}

    with open(designs_file, "r") as f:
        designs = json.load(f)

    for d in designs:
        n = d.get("Name")
        if n in name_to_score:
            val = name_to_score[n]
            d["Rating"] = round(val, decimals) if decimals is not None else val

    with open(designs_file, "w") as f:
        json.dump(designs, f, indent=2)
        f.write("\n")

    return designs


# ---------------------------
# RUN AND PRINT RESULTS
# ---------------------------
if __name__ == "__main__":
    # Resolve tmp directory relative to this file
    this_dir = os.path.dirname(__file__)
    tmp_dir = os.path.abspath(os.path.join(this_dir, "..", "tmp"))
    designs_path = os.path.join(tmp_dir, "designs.txt")
    ratings_path = os.path.join(tmp_dir, "designsRatings.txt")

    print(f"[LatentMetric] tmp_dir={tmp_dir}")
    print(f"[LatentMetric] designs_path={designs_path}")
    print(f"[LatentMetric] ratings_path={ratings_path}")

    updated = update_designs_ratings(designs_path, ratings_path)
    print(f"[LatentMetric] Updated {len(updated)} designs with latent 'Rating' values.")

    # Train Bayesian model on updated designs
    try:
        print("[LatentMetric] Starting training...")
        run_bayes_train(designs_path)
        print("[LatentMetric] Training finished.")
    except Exception as e:
        print(f"[BayesTrain] error: {e}")
        raise
