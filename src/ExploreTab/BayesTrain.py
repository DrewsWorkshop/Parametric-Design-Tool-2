import json
import numpy as np
import itertools
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C, WhiteKernel
import importlib
import sys
import os
import traceback

# ---------------------------
# 1) PARAMETER RANGES (from geometry.<object_type>.config)
# ---------------------------
# These will be loaded dynamically based on the first object's object_type
# found in the dataset within load_data().



import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pyplot as plt
import numpy as np


import time

def log_training_run(
    log_path: str,
    num_samples: int,
    kernel_str: str,
    grid_std: np.ndarray,
    r2_train: float,
    coverage_cells: int,
    coverage_pct: int,
):
    mean_std = float(np.mean(grid_std))
    median_std = float(np.median(grid_std))
    min_std = float(np.min(grid_std))
    max_std = float(np.max(grid_std))

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"Training Run @ {timestamp}\n")
        f.write(f"Training samples: {num_samples}\n")
        f.write(f"Kernel: {kernel_str}\n")
        f.write(f"R² (training): {r2_train:.6f}\n")
        f.write(f"Coverage: {coverage_cells}/64 cells = {coverage_pct}%\n")
        f.write("Grid Predictive Std Summary:\n")
        f.write(f"  Mean   std: {mean_std:.6f}\n")
        f.write(f"  Median std: {median_std:.6f}\n")
        f.write(f"  Min    std: {min_std:.6f}\n")
        f.write(f"  Max    std: {max_std:.6f}\n")


def plot_uncertainty_and_occupancy(grid_norm, grid_std, X_train_norm):
    """
    grid_norm: shape (64,6), values 0.25/0.75
    grid_std:  shape (64,), predictive std for each grid point
    X_train_norm: shape (n,6), training points normalized to [0,1]
    """

    # ------------------------------
    # Uncertainty heatmap (8x8)
    # ------------------------------
    bits_g = (grid_norm > 0.5).astype(int)
    r_g = bits_g[:, 0] * 4 + bits_g[:, 1] * 2 + bits_g[:, 2]
    c_g = bits_g[:, 3] * 4 + bits_g[:, 4] * 2 + bits_g[:, 5]

    M_unc = np.full((8, 8), np.nan)
    for i, (r, c) in enumerate(zip(r_g, c_g)):
        M_unc[r, c] = grid_std[i]

    # ------------------------------
    # Training occupancy heatmap (8x8)
    # ------------------------------
    bits_t = (X_train_norm > 0.5).astype(int)
    r_t = bits_t[:, 0] * 4 + bits_t[:, 1] * 2 + bits_t[:, 2]
    c_t = bits_t[:, 3] * 4 + bits_t[:, 4] * 2 + bits_t[:, 5]

    M_occ = np.zeros((8, 8), dtype=int)
    for r, c in zip(r_t, c_t):
        M_occ[r, c] += 1

    # ------------------------------
    # Plot: two subplots
    # ------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # ---- Left: uncertainty ----
    im1 = ax1.imshow(M_unc, cmap="viridis", origin="lower")
    plt.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04, label="Predictive Std (Uncertainty)")
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.set_title("Uncertainty over 64 Grid Centers")

    # Annotate uncertainty values
    for r in range(8):
        for c in range(8):
            val = M_unc[r, c]
            if not np.isnan(val):
                ax1.text(c, r, f"{val:.2f}", ha="center", va="center", color="white", fontsize=9)

    # ---- Right: occupancy ----
    im2 = ax2.imshow(M_occ, cmap="Reds", origin="lower")
    plt.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04, label="# Training Points")
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.set_title("Training Point Occupancy")

    # Annotate occupancy counts
    for r in range(8):
        for c in range(8):
            count = M_occ[r, c]
            if count > 0:
                ax2.text(c, r, str(count), ha="center", va="center", color="black", fontsize=10)

    # Coverage stats
    coverage_cells = int(np.count_nonzero(M_occ > 0))
    coverage_pct = int(round(100.0 * coverage_cells / 64.0))

    ax2.text(
        0.5,
        -0.08,
        f"Coverage: {coverage_cells}/64 cells = {coverage_pct}%",
        transform=ax2.transAxes,
        ha="center",
        va="top",
        fontsize=12
    )

    plt.tight_layout()
    fig.savefig("uncertainty_and_occupancy.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    return coverage_cells, coverage_pct


# ---------------------------
# 2) LOAD + NORMALIZE DATA
# ---------------------------
def load_data(filepath):
    print(f"[BayesTrain] load_data: filepath={os.path.abspath(filepath)}")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    X, y = [], []

    # Detect object type from first valid item
    ot = None
    for obj in data:
        t = obj.get("object_type")
        if t:
            ot = t
            break
    ot_lower = (ot or "Vase").lower()
    print(f"[BayesTrain] detected object_type={ot_lower}")

    # Load slider config for this object type
    try:
        mod = importlib.import_module(f"geometry.{ot_lower}.config")
        print("[BayesTrain] using import path: geometry")
    except ModuleNotFoundError:
        mod = importlib.import_module(f"src.geometry.{ot_lower}.config")
        print("[BayesTrain] using import path: src.geometry")
    slider = getattr(mod, f"{ot_lower}SliderConfig")()
    ordered_keys = [name for name, _rng, _default in slider]
    bounds = {name: rng for name, rng, _default in slider}
    print(f"[BayesTrain] slider keys: {ordered_keys}")

    for obj in data:
        if obj.get("object_type", "").lower() != ot_lower:
            continue

        rating = obj.get("Rating")
        if rating is None:
            continue

        params = obj["parameters"]
        row = []
        for key in ordered_keys:
            mn, mx = bounds[key]
            v = params[key]
            row.append((v - mn) / (mx - mn))  # normalize to [0, 1]

        X.append(row)
        y.append(rating)

    X_arr = np.array(X, dtype=float)
    y_arr = np.array(y, dtype=float)
    print(f"[BayesTrain] dataset sizes: X={X_arr.shape}, y={y_arr.shape}")
    if y_arr.size > 0:
        print(f"[BayesTrain] y stats: min={float(np.min(y_arr)):.4f}, max={float(np.max(y_arr)):.4f}, mean={float(np.mean(y_arr)):.4f}")
    else:
        print("[BayesTrain] WARNING: no training samples found")
    return X_arr, y_arr


# ---------------------------
# 3) TRAIN BAYESIAN MODEL
# ---------------------------
def train_bayesian_gp(X, y):
    kernel = (
        C(1.0, (1e-3, 1e3)) *
        RBF(length_scale=np.ones(6), length_scale_bounds=(1e-2, 2)) +
        WhiteKernel(noise_level=1e-2, noise_level_bounds=(1e-6, 1e0))
    )

    model = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        n_restarts_optimizer=5,
        random_state=0
    )

    model.fit(X, y)
    print("Trained kernel:", model.kernel_)
    return model


def run_bayes_train(data_path: str):
    print(f"[BayesTrain] run_bayes_train: start, cwd={os.getcwd()}")
    print(f"[BayesTrain] data_path={os.path.abspath(data_path)}")
    # Load and normalize data
    X, y = load_data(data_path)
    if len(y) == 0:
        print("[BayesTrain] ERROR: zero samples; aborting training")
        raise ValueError("No samples available for training")
    # Train model
    model = train_bayesian_gp(X, y)
    # Training metrics
    y_pred, y_std = model.predict(X, return_std=True)
    r2_train = model.score(X, y)
    print("R² (training):", r2_train)
    # 64-point grid in normalized space
    grid_norm = np.asarray(list(itertools.product([0.25, 0.75], repeat=6)), dtype=float)
    _, grid_std = model.predict(grid_norm, return_std=True)
    # Plot/save and compute coverage
    coverage_cells, coverage_pct = plot_uncertainty_and_occupancy(grid_norm, grid_std, X)
    # Log
    log_path = "logger.txt"
    abs_log_path = os.path.abspath(log_path)
    print(f"[BayesTrain] writing log to {abs_log_path}")
    log_training_run(
        log_path=log_path,
        num_samples=len(y),
        kernel_str=str(model.kernel_),
        grid_std=grid_std,
        r2_train=r2_train,
        coverage_cells=coverage_cells,
        coverage_pct=coverage_pct,
    )
    print(f"\nLogged training run to {abs_log_path} ✅")
    # Summary
    print("\nGrid uncertainty summary:")
    print("Mean std:", np.mean(grid_std))
    print("Median std:", np.median(grid_std))
    print("Min std:", np.min(grid_std))
    print("Max std:", np.max(grid_std))
    return {
        "r2_train": float(r2_train),
        "coverage_cells": int(coverage_cells),
        "coverage_pct": int(coverage_pct),
        "kernel": str(model.kernel_),
        "grid_std_mean": float(np.mean(grid_std)),
        "grid_std_median": float(np.median(grid_std)),
        "grid_std_min": float(np.min(grid_std)),
        "grid_std_max": float(np.max(grid_std)),
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "designsPairwise2.txt"
    run_bayes_train(path)
