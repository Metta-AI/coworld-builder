#!/usr/bin/env python3
"""Pick a free spot on a continent of the Softmax Atlas.

Phase 75 runs this in the sandbox (no node needed) against the live places.mjs:

  gh api repos/Metta-AI/metta/contents/web/softmax.com/src/scripts/atlas/places.mjs \
    -H 'Accept: application/vnd.github.raw' > /tmp/places.mjs
  python3 tools/atlas_spot.py --places /tmp/places.mjs --region commons

It sweeps the continent's OUTLINE — `REGION_PATHS`, the same polygon the page
hover-highlights and flies to, not the rectangular `box`, whose corners are open
sea — and returns the candidate whose nearest neighbour is furthest away.
Neighbours are every city inside that polygon, the region's own name anchor and
the landmarks. Coordinates are in OVERVIEW units (the map as 1024x1024; world.jpg
is exactly 3x that).

`--min` is the clearance below which two labels start to overlap on the rendered
page; below it the script still prints its best spot but exits 3, which is a real
answer: the continent is full, and that belongs in the log.

Output: `x y clearance` on stdout, the runners-up and the reasoning on stderr.
"""

import argparse
import re
import sys


def parse(src):
    """(region -> {poly, anchor}, [(slug, x, y, region)], [(x, y)] landmarks)."""
    regions = {}
    block = re.search(r"export const REGIONS = \{(.*?)\n\};", src, re.S)
    if not block:
        sys.exit("atlas_spot: REGIONS block not found")
    for key, body in re.findall(r"\n  (\w+): \{(.*?)\n  \},", block.group(1) + "\n  },", re.S):
        xy = re.search(r"\n    x: ([-\d.]+),\n    y: ([-\d.]+),", body)
        box = re.search(r"box: \[([-\d\s,.]+)\]", body)
        regions[key] = {
            "poly": [],
            "box": [float(v) for v in box.group(1).split(",")] if box else None,
            "anchor": [float(xy.group(1)), float(xy.group(2))] if xy else None,
        }
    paths = re.search(r"export const REGION_PATHS = \{(.*?)\n\};", src, re.S)
    if not paths:
        sys.exit("atlas_spot: REGION_PATHS block not found")
    for key, body in re.findall(r"\n  (\w+): \[(.*?)\n  \],", paths.group(1) + "\n  ],", re.S):
        pts = [(float(a), float(b)) for a, b in re.findall(r"\[\s*([-\d.]+),\s*([-\d.]+),?\s*\]", body)]
        if key in regions and len(pts) >= 3:
            regions[key]["poly"] = pts

    cities = []
    start = src.index("export const CITIES = [")
    body = src[start : src.index("\n];", start)]
    for entry in re.findall(r"\[[^\[\]]*\]", body):
        quoted = re.findall(r'"([^"]*)"', entry)
        nums = re.findall(r"(?<![\w.])(\d+)(?![\w.])", entry)
        if len(quoted) >= 3 and len(nums) >= 2:
            cities.append((quoted[0], float(nums[0]), float(nums[1]), quoted[2]))
    marks = [(float(x), float(y)) for x, y in re.findall(r'\["[^"]*", (\d+), (\d+)\]', src)]
    return regions, cities, marks


def inside(pt, poly):
    x, y = pt
    hit = False
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            hit = not hit
    return hit


def edge_gap(pt, poly):
    """Distance from pt to the nearest edge of poly."""
    x, y = pt
    best = float("inf")
    for i in range(len(poly)):
        ax, ay = poly[i]
        bx, by = poly[i - 1]
        dx, dy = bx - ax, by - ay
        n = dx * dx + dy * dy
        t = 0.0 if n == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / n))
        best = min(best, ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) ** 0.5)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--min", type=float, default=22.0, help="labels below this overlap")
    ap.add_argument("--coast", type=float, default=14.0, help="keep this far inside the outline")
    ap.add_argument("--step", type=float, default=3.0)
    args = ap.parse_args()

    regions, cities, marks = parse(open(args.places, encoding="utf-8").read())
    if args.region not in regions:
        sys.exit(f"atlas_spot: unknown region {args.region!r} (known: {', '.join(sorted(regions))})")
    poly = regions[args.region]["poly"]
    if not poly:
        sys.exit(f"atlas_spot: {args.region} has no outline in REGION_PATHS")
    # The outline and the fly-to box do not coincide everywhere, and
    # tools/atlas_place.py (and a human reading README.md) validate against the
    # box. Stay inside both.
    bx0, by0, bx1, by1 = regions[args.region]["box"] or [0, 0, 1024, 1024]

    taken = [(c[1], c[2]) for c in cities if inside((c[1], c[2]), poly)] + marks
    if regions[args.region]["anchor"]:
        taken.append(tuple(regions[args.region]["anchor"]))

    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    best = []
    x = min(xs)
    while x <= max(xs):
        y = min(ys)
        while y <= max(ys):
            if (
                bx0 <= x <= bx1
                and by0 <= y <= by1
                and inside((x, y), poly)
                and edge_gap((x, y), poly) >= args.coast
            ):
                d = min((((x - a) ** 2 + (y - b) ** 2) ** 0.5 for a, b in taken), default=999.0)
                best.append((round(d, 2), x, y))
            y += args.step
        x += args.step
    if not best:
        sys.exit(f"atlas_spot: nothing at least {args.coast:g} units inside the {args.region} outline")
    # Prefer joining the cluster over hiding in the emptiest corner: of the
    # candidates that clear `--min`, take the one nearest the centre of the
    # continent's existing cities, so the new dot reads as part of the place.
    here = [(c[1], c[2]) for c in cities if c[3] == args.region]
    cx = sum(p[0] for p in here) / len(here) if here else (bx0 + bx1) / 2
    cy = sum(p[1] for p in here) / len(here) if here else (by0 + by1) / 2
    roomy = [b for b in best if b[0] >= args.min]
    if roomy:
        roomy.sort(key=lambda b: ((b[1] - cx) ** 2 + (b[2] - cy) ** 2) ** 0.5)
        d, x, y = roomy[0]
        shown = roomy[1:6]
    else:
        best.sort(reverse=True)
        d, x, y = best[0]
        shown = best[1:6]
    print(f"{int(x)} {int(y)} {d:.1f}")
    print(
        f"atlas_spot: {args.region}, {len(taken)} neighbours, {len(best)} candidate "
        f"points inside the outline, {len(roomy)} of them >= {args.min:g} clear; "
        "runners-up: " + ", ".join(f"({int(b)},{int(c)})@{a:.0f}" for a, b, c in shown),
        file=sys.stderr,
    )
    if d < args.min:
        print(
            f"atlas_spot: the roomiest spot in {args.region} is {d:.1f} units from its "
            f"nearest neighbour (want >= {args.min:g}) — the continent is crowded",
            file=sys.stderr,
        )
        sys.exit(3)


if __name__ == "__main__":
    main()
