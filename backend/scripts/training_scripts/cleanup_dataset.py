"""
Dataset cleanup for the female/male CCTV-crop dataset.

Reads:  /home/nihit/curated_dataset/dataset/{female,male}   (never modified)
Writes: /home/nihit/curated_dataset/split_clean/{train,valid,test}/{female,male}
        /home/nihit/curated_dataset/cleanup_report/          (audit trail)

Steps
 1. md5 + perceptual hash (pHash, 64-bit DCT) for every image, in parallel.
 2. Build duplicate graph:
      - exact-duplicate edges (same md5)
      - near-duplicate edges (pHash hamming distance <= PHASH_DIST, found via LSH banding)
 3. Connected components over that graph:
      - mixed-label component  -> DROP entirely (conflicting labels, can't trust either)
      - within-class exact duplicates -> keep one copy
 4. Assign each component atomically to train/valid/test (so no near-duplicate
    ever straddles a split boundary), filling fixed valid/test quotas per class.
 5. Materialize with hard links (same filesystem -> zero extra disk).

NOTE: person-level (entry/exit) grouping is impossible from filenames alone --
each file carries its own unique UUID. pHash catches re-saves/crops of the same
frame, but different frames of the same person remain unlinked. Documented in
the report.
"""
import os
import sys
import json
import random
import hashlib
import numpy as np
from multiprocessing import Pool
from collections import defaultdict
from PIL import Image
from scipy.fftpack import dct

SRC = "/home/nihit/curated_dataset/dataset"
OUT_SPLIT = "/home/nihit/curated_dataset/split_clean"
OUT_REPORT = "/home/nihit/curated_dataset/cleanup_report"
CLASSES = ("female", "male")
PHASH_DIST = 4          # max hamming distance to call two images near-duplicates
N_BANDS = 5             # LSH bands; pigeonhole guarantees a shared band at dist<=4
VALID_PER_CLASS = 2500
TEST_PER_CLASS = 2500
SEED = 42
WORKERS = 40


def phash64(img: Image.Image) -> int:
    """Standard 64-bit DCT pHash."""
    a = np.asarray(img.convert("L").resize((32, 32), Image.Resampling.LANCZOS),
                   dtype=np.float64)
    d = dct(dct(a, axis=0), axis=1)[:8, :8].flatten()
    med = np.median(d[1:])  # skip DC term
    bits = d > med
    bits[0] = False
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h


def hash_one(task):
    cls, fname = task
    path = os.path.join(SRC, cls, fname)
    try:
        with open(path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        with Image.open(path) as im:
            ph = phash64(im)
        return (cls, fname, md5, ph, None)
    except Exception as e:
        return (cls, fname, None, None, str(e)[:120])


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def band_keys(ph: int):
    """Split 64-bit hash into N_BANDS chunks (13,13,13,13,12 bits)."""
    widths = [13, 13, 13, 13, 12]
    keys, shift = [], 0
    for i, w in enumerate(widths):
        keys.append((i, (ph >> shift) & ((1 << w) - 1)))
        shift += w
    return keys


class DSU:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def main():
    os.makedirs(OUT_REPORT, exist_ok=True)
    random.seed(SEED)

    # ---------- 1. hash everything ----------
    tasks = [(c, f) for c in CLASSES for f in sorted(os.listdir(os.path.join(SRC, c)))]
    print(f"[1/5] Hashing {len(tasks)} images with {WORKERS} workers ...", flush=True)
    records, errors = [], []
    with Pool(WORKERS) as pool:
        for i, r in enumerate(pool.imap_unordered(hash_one, tasks, chunksize=200)):
            if r[4] is not None:
                errors.append(r)
            else:
                records.append(r[:4])
            if (i + 1) % 10000 == 0:
                print(f"  hashed {i + 1}/{len(tasks)}", flush=True)
    print(f"  done: {len(records)} ok, {len(errors)} errors", flush=True)

    n = len(records)
    cls_of = [r[0] for r in records]
    fname_of = [r[1] for r in records]
    md5_of = [r[2] for r in records]
    ph_of = [r[3] for r in records]

    # ---------- 2. duplicate graph ----------
    print("[2/5] Building duplicate graph ...", flush=True)
    dsu = DSU(n)

    md5_groups = defaultdict(list)
    for i, m in enumerate(md5_of):
        md5_groups[m].append(i)
    exact_dup_groups = {m: idxs for m, idxs in md5_groups.items() if len(idxs) > 1}
    for idxs in exact_dup_groups.values():
        for j in idxs[1:]:
            dsu.union(idxs[0], j)
    print(f"  exact-duplicate md5 groups: {len(exact_dup_groups)}", flush=True)

    buckets = defaultdict(list)
    for i, ph in enumerate(ph_of):
        for key in band_keys(ph):
            buckets[key].append(i)

    near_pairs = set()
    big_buckets = 0
    for key, idxs in buckets.items():
        if len(idxs) < 2:
            continue
        if len(idxs) > 2000:
            big_buckets += 1
            continue  # degenerate (flat/uniform images); exact-md5 already covers true dups
        for a in range(len(idxs)):
            ia = idxs[a]
            for b in range(a + 1, len(idxs)):
                ib = idxs[b]
                if md5_of[ia] == md5_of[ib]:
                    continue
                pair = (ia, ib) if ia < ib else (ib, ia)
                if pair in near_pairs:
                    continue
                if hamming(ph_of[ia], ph_of[ib]) <= PHASH_DIST:
                    near_pairs.add(pair)
    for ia, ib in near_pairs:
        dsu.union(ia, ib)
    print(f"  near-duplicate pairs (pHash dist<={PHASH_DIST}): {len(near_pairs)}"
          f"  (skipped {big_buckets} oversized buckets)", flush=True)

    # ---------- 3. component decisions ----------
    print("[3/5] Resolving components ...", flush=True)
    comps = defaultdict(list)
    for i in range(n):
        comps[dsu.find(i)].append(i)

    dropped_conflicts = []      # mixed-label components
    removed_exact_dups = []     # extra identical copies within a class
    kept_components = []        # (class, [indices to keep])

    for members in comps.values():
        classes = {cls_of[i] for i in members}
        if len(classes) > 1:
            dropped_conflicts.extend(members)
            continue
        # within-class: collapse exact duplicates, keep one per md5
        seen_md5, keep = {}, []
        for i in sorted(members, key=lambda x: fname_of[x]):
            if md5_of[i] in seen_md5:
                removed_exact_dups.append(i)
            else:
                seen_md5[md5_of[i]] = i
                keep.append(i)
        kept_components.append((classes.pop(), keep))

    n_conflict_imgs = len(dropped_conflicts)
    n_dedup = len(removed_exact_dups)
    kept_per_class = defaultdict(int)
    for cls, keep in kept_components:
        kept_per_class[cls] += len(keep)
    print(f"  dropped (conflicting labels): {n_conflict_imgs} images", flush=True)
    print(f"  removed (within-class exact dups): {n_dedup} images", flush=True)
    print(f"  kept: {dict(kept_per_class)}", flush=True)

    # ---------- 4. component-atomic split ----------
    print("[4/5] Assigning splits (component-atomic) ...", flush=True)
    by_class = defaultdict(list)
    for cls, keep in kept_components:
        by_class[cls].append(keep)

    assign = {}  # index -> split name
    split_counts = defaultdict(lambda: defaultdict(int))
    for cls in CLASSES:
        comps_c = by_class[cls]
        random.shuffle(comps_c)
        for keep in comps_c:
            if split_counts["valid"][cls] < VALID_PER_CLASS:
                split = "valid"
            elif split_counts["test"][cls] < TEST_PER_CLASS:
                split = "test"
            else:
                split = "train"
            for i in keep:
                assign[i] = split
            split_counts[split][cls] += len(keep)

    for s in ("train", "valid", "test"):
        print(f"  {s}: " + ", ".join(f"{c}={split_counts[s][c]}" for c in CLASSES),
              flush=True)

    # ---------- 5. materialize with hard links ----------
    print("[5/5] Materializing split_clean/ ...", flush=True)
    if os.path.exists(OUT_SPLIT):
        print(f"  ERROR: {OUT_SPLIT} already exists; refusing to overwrite.", flush=True)
        sys.exit(1)
    for s in ("train", "valid", "test"):
        for c in CLASSES:
            os.makedirs(os.path.join(OUT_SPLIT, s, c))
    linked = 0
    for i, split in assign.items():
        src = os.path.join(SRC, cls_of[i], fname_of[i])
        dst = os.path.join(OUT_SPLIT, split, cls_of[i], fname_of[i])
        try:
            os.link(src, dst)
        except OSError:
            import shutil
            shutil.copy2(src, dst)
        linked += 1
    print(f"  linked {linked} files", flush=True)

    # ---------- report ----------
    with open(os.path.join(OUT_REPORT, "dropped_label_conflicts.txt"), "w") as f:
        for i in sorted(dropped_conflicts, key=lambda x: (cls_of[x], fname_of[x])):
            f.write(f"{cls_of[i]}/{fname_of[i]}\tmd5={md5_of[i]}\n")
    with open(os.path.join(OUT_REPORT, "removed_exact_duplicates.txt"), "w") as f:
        for i in sorted(removed_exact_dups, key=lambda x: (cls_of[x], fname_of[x])):
            f.write(f"{cls_of[i]}/{fname_of[i]}\tmd5={md5_of[i]}\n")
    with open(os.path.join(OUT_REPORT, "near_duplicate_pairs.txt"), "w") as f:
        for ia, ib in sorted(near_pairs):
            f.write(f"{cls_of[ia]}/{fname_of[ia]}\t{cls_of[ib]}/{fname_of[ib]}\t"
                    f"dist={hamming(ph_of[ia], ph_of[ib])}\n")
    if errors:
        with open(os.path.join(OUT_REPORT, "hash_errors.txt"), "w") as f:
            for cls, fname, _, _, err in errors:
                f.write(f"{cls}/{fname}\t{err}\n")
    summary = {
        "source": SRC,
        "output_split": OUT_SPLIT,
        "phash_distance_threshold": PHASH_DIST,
        "seed": SEED,
        "input_images": len(tasks),
        "hash_errors": len(errors),
        "dropped_label_conflict_images": n_conflict_imgs,
        "removed_within_class_exact_duplicates": n_dedup,
        "near_duplicate_pairs": len(near_pairs),
        "kept_per_class": dict(kept_per_class),
        "split_counts": {s: dict(split_counts[s]) for s in ("train", "valid", "test")},
        "caveat_person_level": (
            "Entry/exit shots of the same person carry unrelated UUID filenames and "
            "cannot be grouped without re-identification; pHash links re-saved/cropped "
            "frames only. Components never straddle split boundaries."
        ),
    }
    with open(os.path.join(OUT_REPORT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)
    print(f"\nDone. Report: {OUT_REPORT}  Split: {OUT_SPLIT}", flush=True)


if __name__ == "__main__":
    main()
