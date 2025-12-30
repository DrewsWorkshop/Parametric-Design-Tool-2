def run(object_type: str) -> None:
    import os, json, random

    # Read config
    shuffle, seed = True, None
    try:
        conf_path = os.path.join("src", "ExploreTab", "Configuration.JSON")
        with open(conf_path, "r", encoding="utf-8") as f:
            conf = json.load(f)
        tconf = conf.get("Batch 1 Tournament", {})
        shuffle = bool(tconf.get("shuffle", True))
        seed = tconf.get("seed", None)
    except Exception:
        pass

    # Load Batch1 designs
    in_path = os.path.join("src", "ExploreTab", "tmp", "designs.txt")
    if not os.path.exists(in_path):
        print(f"[Batch1Tournament] Missing input: {in_path}")
        return
    with open(in_path, "r", encoding="utf-8") as f:
        designs = json.load(f)

    # Build index list and optionally shuffle
    idx = list(range(len(designs)))
    rnd = random.Random(seed)
    if shuffle:
        rnd.shuffle(idx)

    # Pair head-to-head
    matches = []
    for i in range(0, len(idx) - 1, 2):
        a = idx[i]
        b = idx[i + 1]
        matches.append({
            "match_id": len(matches) + 1,
            "a_index": a,
            "b_index": b
        })

    # Do not write matches to disk; generation only
    print(f"[Batch1Tournament] generated {len(matches)} matches (not writing file)")


