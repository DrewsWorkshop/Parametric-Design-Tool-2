import json
import sys
from collections import defaultdict
import matplotlib.pyplot as plt


def plot_tournament(designs_path: str, results_path: str, *, horizontal_compression: float = 0.6, output_path: str | None = None) -> None:
    """
    Plot a tournament bracket from the provided input files.

    Parameters
    - designs_path: path to designs.txt (JSON array with 'Name' and 'parameters')
    - results_path: path to results.txt (JSON array of match dictionaries)
    - horizontal_compression: 0 < value <= 1; smaller values pull rounds closer together
    """
    # -------------------------------
    # 1. Load designs (A, B, C, ...)
    # -------------------------------
    with open(designs_path, "r") as f:
        designs = json.load(f)

    # Map index -> name and optionally store a short param summary
    index_to_name = {}
    index_to_info = {}

    for idx, d in enumerate(designs):
        name = d["Name"]
        params = d["parameters"]

        index_to_name[idx] = name

        # Short one-line summary (customize if you like)
        info = (
            f"Seg:{params['Segment Count']}, "
            f"W:{params['Object Width']:.2f}, "
            f"Twist:{params['Twist Angle']:.1f}°"
        )
        index_to_info[idx] = info

    # -------------------------------
    # 2. Load tournament results
    # -------------------------------
    with open(results_path, "r") as f:
        matches = json.load(f)

    # Group matches by round
    rounds = defaultdict(list)
    for m in matches:
        rnd = m.get("round", 0)
        rounds[rnd].append(m)

    round_numbers = sorted(rounds.keys())

    # -------------------------------
    # 3. Build text blocks per round
    # -------------------------------
    round_blocks = []  # list of list-of-strings, one list per round

    for rnd in round_numbers:
        block = []
        for m in rounds[rnd]:
            a_idx = m["a_index"]
            b_idx = m["b_index"]
            w_idx = m["winner_index"]

            a_name = index_to_name.get(a_idx, f"#{a_idx}")
            b_name = index_to_name.get(b_idx, f"#{b_idx}")
            w_name = index_to_name.get(w_idx, f"#{w_idx}")

            a_info = index_to_info.get(a_idx, "")
            b_info = index_to_info.get(b_idx, "")

            text = (
                f"Round {rnd} - Match {m['match_id']}\n"
                f"{a_name} ({a_info})\nvs\n"
                f"{b_name} ({b_info})\n"
                f"→ Winner: {w_name}"
            )
            block.append(text)
        round_blocks.append(block)

    # -------------------------------
    # 4. Plot bracket-style layout
    # -------------------------------
    fig, ax = plt.subplots(figsize=(14, 8))

    # Evenly space base positions within margins, centered around 0.5
    left_margin = 0.1
    right_margin = 0.1
    num_rounds = len(round_blocks)

    def base_x_at(i: int) -> float:
        if num_rounds <= 1:
            return 0.5
        span = 1.0 - left_margin - right_margin
        return left_margin + (span * i) / (num_rounds - 1)

    for i, block in enumerate(round_blocks):
        base_x = base_x_at(i)
        x = 0.5 + horizontal_compression * (base_x - 0.5)
        # Vertical layout within each round
        y_start = 0.9
        # Adjust step depending on how many matches per round you have
        y_step = 0.18 if len(block) <= 4 else 0.12

        for j, text in enumerate(block):
            y = y_start - j * y_step
            ax.text(
                x,
                y,
                text,
                ha="center",
                va="top",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.4", fc="lightyellow", ec="black"),
            )

    # Lock axes to a fixed 0..1 space so centering is stable
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    ax.set_title("Batch 1 Tournament Results", fontsize=16)
    ax.axis("off")
    plt.tight_layout()

    # Save to PNG (use provided path or default) and close (no popup window)
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
    else:
        plt.savefig("TournamentResults.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    # Allow calling with: python TournamentPlot.py designs.txt results.txt
    # Fallback to local defaults if not provided.
    if len(sys.argv) >= 3:
        designs_arg = sys.argv[1]
        results_arg = sys.argv[2]
    else:
        designs_arg = "designs.txt"
        results_arg = "Batch1TournamentResults.txt"

    # Optional third arg: output PNG path
    output_arg = None
    if len(sys.argv) >= 4:
        output_arg = sys.argv[3]

    plot_tournament(designs_arg, results_arg, output_path=output_arg)
