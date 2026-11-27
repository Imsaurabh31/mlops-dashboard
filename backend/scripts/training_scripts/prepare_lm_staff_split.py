"""
Balance + split for lm_staff (staffs_noid vs customers_noid).

Order is split-FIRST, then augment train only, so no augmented copy of a
training image can leak into valid. Sources in lm_staff/ are never modified
(files are copied, not moved).

  lm_staff/{staffs_noid,customers_noid}
    -> lm_staff_split/valid/<class>   (200 random originals per class)
    -> lm_staff_split/train/<class>   (the rest; smaller class augmented up
                                       to the larger using dataset_1.augment_images)

No test split. Seeded for reproducibility.
"""
import os
import sys
import random
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset_1 import augment_images, move_augmented_images_to_subfolder

SRC = "/home/nihit/model_train/lm_staff"
DST = "/home/nihit/model_train/lm_staff_split"
CLASSES = ("staffs_noid", "customers_noid")
VALID_PER_CLASS = 200
SEED = 42
IMG_EXTS = (".jpg", ".jpeg", ".png")


def main():
    random.seed(SEED)
    if os.path.exists(DST):
        sys.exit(f"ERROR: {DST} already exists; refusing to overwrite.")

    for split in ("train", "valid"):
        for c in CLASSES:
            os.makedirs(os.path.join(DST, split, c))

    # 1. split originals: 200 random per class -> valid, rest -> train
    for c in CLASSES:
        files = sorted(f for f in os.listdir(os.path.join(SRC, c))
                       if f.lower().endswith(IMG_EXTS))
        random.shuffle(files)
        valid, train = files[:VALID_PER_CLASS], files[VALID_PER_CLASS:]
        for split, names in (("valid", valid), ("train", train)):
            for f in names:
                shutil.copy2(os.path.join(SRC, c, f),
                             os.path.join(DST, split, c, f))
        print(f"{c}: {len(valid)} valid, {len(train)} train")

    # 2. balance train only: augment the smaller class up to the larger
    counts = {c: len(os.listdir(os.path.join(DST, "train", c))) for c in CLASSES}
    target = max(counts.values())
    for c, n in counts.items():
        need = target - n
        if need > 0:
            src_folder = os.path.join(DST, "train", c)
            aug_folder = os.path.join(DST, "train", f"{c}_augmented")
            print(f"Augmenting {need} images for train/{c} ...")
            augment_images(src_folder, need, aug_folder)
            move_augmented_images_to_subfolder(aug_folder, src_folder)

    final = {s: {c: len(os.listdir(os.path.join(DST, s, c))) for c in CLASSES}
             for s in ("train", "valid")}
    print("Final counts:", final)


if __name__ == "__main__":
    main()
