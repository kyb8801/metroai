"""
SEM depth — NIST mds2-3838 segmentation accuracy & detection limits  [YOUR PC, ~420 MB]
=======================================================================================
NIST 'Detection Limits for SEM Image Segmentation': SIMULATED SEM images augmented with
Poisson noise + contrast, plus mask GROUND TRUTH. Threshold/Otsu segment -> IoU & CD vs
mask -> accuracy vs noise/contrast = the detection limit.

HONEST: this is SIMULATED data (not measured), so it is ★★ not ★★★. But mask = ground
truth, so accuracy IS measurable (like OCD's known-Pi cross-validation). 420 MB download.

DOWNLOAD (PowerShell, in this folder):
  $B="https://data.nist.gov/od/ds/mds2-3838"
  iwr "$B/intensity_sets.zip" -OutFile intensity_sets.zip   # 420 MB (SEM images)
  iwr "$B/mask_sets.zip"      -OutFile mask_sets.zip         # masks (ground truth)
  iwr "$B/README.txt"         -OutFile sem_README.txt        # check exact folder/file names
  Expand-Archive intensity_sets.zip -DestinationPath intensity ; Expand-Archive mask_sets.zip -DestinationPath mask

RUN:  pip install pillow scikit-image numpy ; python sem_depth_mds3838_segmentation.py

NOTE: folder/file naming inside the zips — adjust GLOB/`pair_mask` to match sem_README.txt.
"""
import glob, os
import numpy as np
from PIL import Image
from skimage.filters import threshold_otsu


def load_gray(path):
    return np.asarray(Image.open(path).convert("L"), dtype=float)


def iou(seg, gt):
    seg = seg.astype(bool); gt = gt.astype(bool)
    u = (seg | gt).sum()
    return (seg & gt).sum() / u if u else 1.0


def linewidth_px(binary):
    # mean run of foreground per row (simple CD proxy); adapt to your feature geometry
    rows = [r.sum() for r in binary if r.any()]
    return float(np.mean(rows)) if rows else 0.0


def pair_mask(img_path):
    # ADAPT to README: here we assume one mask per collection in ./mask
    masks = glob.glob(os.path.join("mask", "**", "*.png"), recursive=True)
    return masks[0] if masks else None


if __name__ == "__main__":
    imgs = sorted(glob.glob(os.path.join("intensity", "**", "*.png"), recursive=True))
    if not imgs:
        raise SystemExit("No images found under ./intensity — unzip first and check README folder names.")
    print(f"found {len(imgs)} SEM images")
    results = []
    for p in imgs:
        im = load_gray(p)
        seg = im > threshold_otsu(im)
        mpath = pair_mask(p)
        if mpath:
            gt = load_gray(mpath) > 127
            results.append((os.path.basename(p), iou(seg, gt), linewidth_px(seg), linewidth_px(gt)))
    print(f"{'image':30s} {'IoU':>6s} {'CD_seg':>8s} {'CD_gt':>8s} {'CD_err':>8s}")
    for name, j, cds, cdg in results[:20]:
        print(f"  {name[:28]:30s} {j:6.3f} {cds:8.1f} {cdg:8.1f} {abs(cds-cdg):8.1f}")
    if results:
        ious = np.array([r[1] for r in results]); cderr = np.array([abs(r[2]-r[3]) for r in results])
        print(f"\n  mean IoU={ious.mean():.3f}  mean CD error={cderr.mean():.1f}px")
        print("  Group by the noise/contrast level encoded in each collection's folder name")
        print("  to plot accuracy-vs-noise = the detection limit (the ★★ deliverable).")
