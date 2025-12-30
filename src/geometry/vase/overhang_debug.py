import os
import sys


# Ensure '<project>/src' is on sys.path when running this file directly
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # points to .../src
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from geometry.vase.geometry import vaseGeometry, overhangVaseCheck


def run_case(name: str, params: dict, max_overhang_angle: float = 50.0):
    # Mesh path
    mesh_result = vaseGeometry(
        segment_count=int(params.get("segment_count", 50)),
        object_width=float(params.get("object_width", 1.0)),
        twist_angle=float(params.get("twist_angle", 20.0)),
        twist_groove_depth=float(params.get("twist_groove_depth", 1.0)),
        vertical_wave_freq=float(params.get("vertical_wave_freq", 3.0)),
        vertical_wave_depth=float(params.get("vertical_wave_depth", 1.0)),
        wall_thickness=float(params.get("wall_thickness", 0.5)),
        max_overhang_angle=float(max_overhang_angle),
    )
    mesh_has_overhang = False
    if isinstance(mesh_result, tuple) and len(mesh_result) == 4:
        mesh_has_overhang = bool(mesh_result[3])

    # Lightweight path
    lite_has_overhang = overhangVaseCheck(
        segment_count=int(params.get("segment_count", 50)),
        object_width=float(params.get("object_width", 1.0)),
        twist_angle=float(params.get("twist_angle", 20.0)),
        twist_groove_depth=float(params.get("twist_groove_depth", 1.0)),
        vertical_wave_freq=float(params.get("vertical_wave_freq", 3.0)),
        vertical_wave_depth=float(params.get("vertical_wave_depth", 1.0)),
        wall_thickness=float(params.get("wall_thickness", 0.5)),
        max_overhang_angle=float(max_overhang_angle),
    )

    # Output in requested format
    print(f"parameters ({name}): {params}")
    print(f"- mesh has overhang: {mesh_has_overhang}")
    print(f"- lightweight has overhang: {lite_has_overhang}")
    print("")


def main():
    # Simple set of sample parameter cases (deterministic)
    cases = [
        ("default", {
            "segment_count": 50,
            "object_width": 1.0,
            "twist_angle": 20.0,
            "twist_groove_depth": 1.0,
            "vertical_wave_freq": 3.0,
            "vertical_wave_depth": 1.0,
            "wall_thickness": 0.5,
        }),
        ("twist_high", {
            "segment_count": 50,
            "object_width": 1.0,
            "twist_angle": 60.0,
            "twist_groove_depth": 1.0,
            "vertical_wave_freq": 3.0,
            "vertical_wave_depth": 1.0,
            "wall_thickness": 0.5,
        }),
        ("wave_deep", {
            "segment_count": 50,
            "object_width": 1.0,
            "twist_angle": 20.0,
            "twist_groove_depth": 1.0,
            "vertical_wave_freq": 5.0,
            "vertical_wave_depth": 5.0,
            "wall_thickness": 0.5,
        }),
        ("thin_wall", {
            "segment_count": 50,
            "object_width": 1.0,
            "twist_angle": 35.0,
            "twist_groove_depth": 2.0,
            "vertical_wave_freq": 6.0,
            "vertical_wave_depth": 3.0,
            "wall_thickness": 0.3,
        }),
        ("wide_object", {
            "segment_count": 50,
            "object_width": 1.5,
            "twist_angle": 25.0,
            "twist_groove_depth": 2.0,
            "vertical_wave_freq": 4.0,
            "vertical_wave_depth": 2.0,
            "wall_thickness": 0.6,
        }),
    ]

    for name, params in cases:
        run_case(name, params, max_overhang_angle=50.0)

    # Sample many random parameter sets and compare
    import random
    random.seed(42)

    def randf(a, b):
        return a + (b - a) * random.random()

    mismatches = 0
    total = 0
    NUM_RANDOM = 200  # increase for more coverage

    for idx in range(NUM_RANDOM):
        params = {
            "segment_count": 50,  # keep sampling identical to geometry
            "object_width": randf(0.6, 2.0),
            "twist_angle": randf(0.0, 70.0),
            "twist_groove_depth": randf(0.0, 5.0),
            "vertical_wave_freq": randf(0.0, 20.0),
            "vertical_wave_depth": randf(0.0, 5.0),
            "wall_thickness": randf(0.2, 0.9),
        }

        # Mesh path
        mesh_result = vaseGeometry(
            segment_count=int(params["segment_count"]),
            object_width=float(params["object_width"]),
            twist_angle=float(params["twist_angle"]),
            twist_groove_depth=float(params["twist_groove_depth"]),
            vertical_wave_freq=float(params["vertical_wave_freq"]),
            vertical_wave_depth=float(params["vertical_wave_depth"]),
            wall_thickness=float(params["wall_thickness"]),
            max_overhang_angle=50.0,
        )
        mesh_has_overhang = False
        if isinstance(mesh_result, tuple) and len(mesh_result) == 4:
            mesh_has_overhang = bool(mesh_result[3])

        # Lightweight path
        lite_has_overhang = overhangVaseCheck(
            segment_count=int(params["segment_count"]),
            object_width=float(params["object_width"]),
            twist_angle=float(params["twist_angle"]),
            twist_groove_depth=float(params["twist_groove_depth"]),
            vertical_wave_freq=float(params["vertical_wave_freq"]),
            vertical_wave_depth=float(params["vertical_wave_depth"]),
            wall_thickness=float(params["wall_thickness"]),
            max_overhang_angle=50.0,
        )

        total += 1
        if mesh_has_overhang != lite_has_overhang:
            mismatches += 1
            print(f"parameters (random_{idx}): {params}")
            print(f"- mesh has overhang: {mesh_has_overhang}")
            print(f"- lightweight has overhang: {lite_has_overhang}")
            print("")

    print(f"Summary: total={total}, mismatches={mismatches}, matches={total - mismatches}")


if __name__ == "__main__":
    main()


