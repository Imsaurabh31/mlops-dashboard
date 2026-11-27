"""
Generic split (+ optional train balancing) for a flat class-folder dataset.

  <src>/<class>/*.jpg  ->  <dst>/valid/<class>  (N random originals per class)
                           <dst>/train/<class>  (the rest)

With --balance, the smaller train class is augmented up to the larger using
dataset_1.augment_images (split-first, so augmented images never reach valid).
Sources are copied, never moved. No test split.

Usage:
  python prepare_split.py --src /path/to/data --dst /path/to/out --valid 400 [--balance]
"""
import os
import sys
import random
import shutil
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset_1 import augment_images, move_augmented_images_to_subfolder

IMG_EXTS = (".jpg", ".jpeg", ".png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--valid", type=int, required=True, help="valid images per class")
    ap.add_argument("--balance", action="store_true",
                    help="augment the smaller train class up to the larger")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    if os.path.exists(args.dst):
        sys.exit(f"ERROR: {args.dst} already exists; refusing to overwrite.")

    classes = sorted(d for d in os.listdir(args.src)
                     if os.path.isdir(os.path.join(args.src, d)))
    if not classes:
        sys.exit(f"ERROR: no class folders found in {args.src}")
    print(f"Classes: {classes}")

    for split in ("train", "valid"):
        for c in classes:
            os.makedirs(os.path.join(args.dst, split, c))

    for c in classes:
        files = sorted(f for f in os.listdir(os.path.join(args.src, c))
                       if f.lower().endswith(IMG_EXTS))
        if len(files) <= args.valid:
            sys.exit(f"ERROR: class '{c}' has only {len(files)} images, "
                     f"cannot take {args.valid} for valid.")
        random.shuffle(files)
        valid, train = files[:args.valid], files[args.valid:]
        for split, names in (("valid", valid), ("train", train)):
            for f in names:
                shutil.copy2(os.path.join(args.src, c, f),
                             os.path.join(args.dst, split, c, f))
        print(f"{c}: {len(valid)} valid, {len(train)} train")

    if args.balance:
        counts = {c: len(os.listdir(os.path.join(args.dst, "train", c))) for c in classes}
        target = max(counts.values())
        for c, n in counts.items():
            need = target - n
            if need > 0:
                src_folder = os.path.join(args.dst, "train", c)
                aug_folder = os.path.join(args.dst, "train", f"{c}_augmented")
                print(f"Augmenting {need} images for train/{c} ...")
                augment_images(src_folder, need, aug_folder)
                move_augmented_images_to_subfolder(aug_folder, src_folder)

    final = {s: {c: len(os.listdir(os.path.join(args.dst, s, c))) for c in classes}
             for s in ("train", "valid")}
    print("Final counts:", final)


if __name__ == "__main__":
    main()
