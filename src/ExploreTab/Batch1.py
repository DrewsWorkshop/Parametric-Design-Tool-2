def run(object_type: str) -> None:
    o = (object_type or "").strip().lower()
    if o == "vase":
        from geometry.vase.config import vaseSliderConfig as get_cfg
    elif o == "table":
        from geometry.table.config import tableSliderConfig as get_cfg
    elif o == "stool":
        from geometry.stool.config import stoolSliderConfig as get_cfg
    else:
        print("[Batch1] Unknown object type")
        return

    cfg = get_cfg()
    print(f"[Batch1] {object_type} slider ranges:")
    for name, bounds, _ in cfg:
        print(f"- {name}: [{bounds[0]}, {bounds[1]}]")

    # Generate Latin Hypercube samples using Configuration.JSON
    try:
        from scipy.stats import qmc
        import os, json

        # Read config
        n, seed = 16, None
        try:
            conf_path = os.path.join("src", "ExploreTab", "Configuration.JSON")
            with open(conf_path, "r", encoding="utf-8") as f:
                conf = json.load(f)
            b1 = conf.get("Batch 1", {})
            n = int(b1.get("n_designs", 16))
            seed = b1.get("seed", None)
        except Exception:
            pass

        dims = len(cfg)
        sampler = qmc.LatinHypercube(d=dims, seed=seed)
        samples = sampler.random(n=n)  # in [0,1)^d

        print(f"[Batch1] {object_type} LHS ({n} samples) -> file")
        designs = []
        for i, row in enumerate(samples):
            params = {}
            for (name, bounds, _), u in zip(cfg, row):
                lo, hi = bounds
                val = lo + u * (hi - lo)
                if name == "Segment Count":
                    val = int(round(val))
                params[name] = val
            designs.append({
                "Name": (chr(65 + i) if i < 26 else f"N{i+1}"),
                "object_type": object_type,
                "Rating": None,
                "parameters": params,
            })

        out_dir = os.path.join("src", "ExploreTab", "tmp")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "designs.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(designs, f, indent=2)
        print(f"[Batch1] wrote: {out_path}")

        # Run Explore Error Check to refine parameters in place
        try:
            from ExploreTab.ExpErrorCheck.ExploreErrorCheck import main as error_check
            error_check(out_path)
            print("[Batch1] error check completed")
        except Exception as e:
            print(f"[Batch1] error check error: {e}")
    except Exception as e:
        print(f"[Batch1] LHS error: {e}")


