from geometry.vase.geometry import overhangVaseCheck
from geometry.vase.config import vaseSliderConfig
import json


def main():
    # Object type configurations
    object_configs = {
        "Vase": (overhangVaseCheck, vaseSliderConfig),
        # "Cylinder": (overhangCylinderCheck, cylinderSliderConfig),
        # etc.
    }
    
    # Read designs from designsGA.txt
    with open('src/tmp/designsGA.txt', 'r') as f:
        designs = json.load(f)
    
    print(f"Processing {len(designs)} designs from designsGA.txt\n")

    # Process each design
    for i, design in enumerate(designs, 1):
        print(f"Design {i}:")
        
        # Get object type and corresponding functions
        object_type = design["object_type"]
        if object_type not in object_configs:
            print(f"  ERROR: Unknown object type '{object_type}'")
            continue
            
        check_func, config_func = object_configs[object_type]
        print(f"  Object type: {object_type}")
        
        # Convert design parameters to our format
        design_params = design["parameters"]
        params = {
            "segment_count": design_params["Segment Count"],
            "object_width": design_params["Object Width"],
            "twist_angle": design_params["Twist Angle"],
            "twist_groove_depth": design_params["Twist Groove Depth"],
            "vertical_wave_freq": design_params["Vertical Wave Frequency"],
            "vertical_wave_depth": design_params["Vertical Wave Depth"],
        }

        def check(p):
            return check_func(
                segment_count=int(round(p["segment_count"])),
                object_width=p["object_width"],
                twist_angle=p["twist_angle"],
                twist_groove_depth=p["twist_groove_depth"],
                vertical_wave_freq=int(round(p["vertical_wave_freq"])),
                vertical_wave_depth=p["vertical_wave_depth"],
            )

        # Config map and sweep helpers
        cfg = {label: bounds for (label, bounds, _d) in config_func()}
        order = [
            ("Segment Count", "segment_count", "int"),
            ("Object Width", "object_width", "float"),
            ("Twist Angle", "twist_angle", "float"),
            ("Twist Groove Depth", "twist_groove_depth", "float"),
            ("Vertical Wave Frequency", "vertical_wave_freq", "int"),
            ("Vertical Wave Depth", "vertical_wave_depth", "float"),
        ]

        def sweep_integer(key_label, key_name, p_orig):
            (min_v, max_v) = cfg[key_label]
            start = int(round(p_orig[key_name]))
            start_norm = (start - min_v) / (max_v - min_v)
            
            for v in range(start - 1, int(min_v) - 1, -1):
                p = dict(p_orig)
                p[key_name] = v
                if not check(p):
                    v_norm = (v - min_v) / (max_v - min_v)
                    delta_norm = start_norm - v_norm
                    return v, delta_norm
            return None, None

        def sweep_continuous(key_label, key_name, p_orig, step_fraction=0.05):
            (min_v, max_v) = cfg[key_label]
            start = float(p_orig[key_name])
            if start <= min_v:
                return None, None
            
            # Normalize to 0-1 range
            start_norm = (start - min_v) / (max_v - min_v)
            step_norm = step_fraction
            
            v_norm = start_norm
            while v_norm - step_norm >= 0:
                v_norm = max(0, v_norm - step_norm)
                # Convert back to original units
                v = min_v + v_norm * (max_v - min_v)
                p = dict(p_orig)
                p[key_name] = v
                if not check(p):
                    delta_norm = start_norm - v_norm
                    return v, delta_norm
            return None, None
        
        # Check initial overhang
        initial_overhang = check(params)
        
        if not initial_overhang:
            print("  PASS")
        else:
            print("  FAIL")
            print("  Sweeping parameters...")
            
            best_label = None
            best_value = None
            best_delta = float('inf')
            
            for label, key, kind in order:
                if kind == "int":
                    res, delta_norm = sweep_integer(label, key, params)
                    if res is None:
                        print(f"    [{label}] FAIL - no passing value within bounds")
                    else:
                        print(f"    [{label}] PASS at {res} (Δu={delta_norm:.3f})")
                        if delta_norm < best_delta:
                            best_delta = delta_norm
                            best_label = label
                            best_value = res
                else:
                    res, delta_norm = sweep_continuous(label, key, params)
                    if res is None:
                        print(f"    [{label}] FAIL - no passing value within bounds")
                    else:
                        print(f"    [{label}] PASS at {res:.6f} (Δu={delta_norm:.3f})")
                        if delta_norm < best_delta:
                            best_delta = delta_norm
                            best_label = label
                            best_value = res
            
            # Print best slider and refined parameters
            if best_label is not None:
                print(f"  Best slider: {best_label} (Δu={best_delta:.3f})")
                refined_params = dict(params)
                # Find the key name for the best label
                for label, key, kind in order:
                    if label == best_label:
                        refined_params[key] = best_value
                        break
                
                print("  Refined parameters:")
                for key, value in refined_params.items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.6f}")
                    else:
                        print(f"    {key}: {value}")
                
                # Update the design in the designs list
                design["parameters"]["Segment Count"] = refined_params["segment_count"]
                design["parameters"]["Object Width"] = refined_params["object_width"]
                design["parameters"]["Twist Angle"] = refined_params["twist_angle"]
                design["parameters"]["Twist Groove Depth"] = refined_params["twist_groove_depth"]
                design["parameters"]["Vertical Wave Frequency"] = refined_params["vertical_wave_freq"]
                design["parameters"]["Vertical Wave Depth"] = refined_params["vertical_wave_depth"]
                
                print("  Updated designsGA.txt with refined parameters")
            else:
                print("  No slider could eliminate overhang within bounds.")
        
        print()  # Empty line between designs

    # Write updated designs back to file
    with open('src/tmp/designsGA.txt', 'w') as f:
        json.dump(designs, f, indent=2)
    print("Saved updated designs to designsGA.txt")


if __name__ == "__main__":
    main()


