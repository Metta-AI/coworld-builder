#!/usr/bin/env python3
"""Edit the CITIES array of the Softmax Atlas' places.mjs.

Used by .github/workflows/atlas-update.yml (phase 75) to give a newly shipped
coworld a dot on https://softmax.com/atlas. It only ever touches CITIES: the
painting, the regions, the territories and IDEA_PLACES are left alone.

  python3 atlas_place.py --places <path/to/places.mjs> \
      --add '[["escrow","Escrow",512,470,"commons",null,"c"]]' \
      [--drop retired-slug,other-slug]

Entries are [slug, label, x, y, region, territory|null, anchor|null] — the same
seven slots README.md documents. A new entry is inserted after the last entry of
its own region, so the file stays grouped the way a human wrote it. Adding a slug
that is already placed is a no-op (the workflow is re-run on every retry), and so
is dropping a slug that is not there.

Exit codes: 0 = file written or already correct, 2 = bad input.
"""

import argparse
import json
import re
import sys


def fail(msg):
    print(f"atlas_place: {msg}", file=sys.stderr)
    sys.exit(2)


def load_regions(src):
    """Region key -> box [x0,y0,x1,y1], read out of the REGIONS literal."""
    m = re.search(r"export const REGIONS = \{(.*?)\n\};", src, re.S)
    if not m:
        fail("REGIONS block not found in places.mjs")
    regions = {}
    for key, body in re.findall(r"(\w+): \{(.*?)\n  \},", m.group(1) + "\n  },", re.S):
        box = re.search(r"box: \[([\d\s,.-]+)\]", body)
        if box:
            regions[key] = [float(v) for v in box.group(1).split(",")]
    return regions


def cities_span(lines):
    """(first, last) line indices of the body of the CITIES array."""
    start = next(
        (i for i, ln in enumerate(lines) if ln.startswith("export const CITIES = [")),
        None,
    )
    if start is None:
        fail("CITIES array not found in places.mjs")
    end = next((i for i in range(start + 1, len(lines)) if lines[i].rstrip() == "];"), None)
    if end is None:
        fail("unterminated CITIES array in places.mjs")
    return start + 1, end


def entries(lines, first, last):
    """[(start_idx, end_idx, slug, region)] for each entry, comments skipped."""
    out, depth, begin = [], 0, None
    for i in range(first, last):
        if depth == 0 and not lines[i].lstrip().startswith("["):
            continue  # a `// region` comment line between groups
        if depth == 0:
            begin = i
        depth += lines[i].count("[") - lines[i].count("]")
        if depth == 0:
            text = "\n".join(lines[begin : i + 1])
            quoted = re.findall(r'"([^"]*)"', text)
            if len(quoted) < 3:
                fail(f"cannot read slug/region from CITIES entry at line {begin + 1}")
            out.append((begin, i, quoted[0], quoted[2]))
    if depth != 0:
        fail("unbalanced brackets inside CITIES")
    return out


def render(entry):
    slug, label, x, y, region = entry[0], entry[1], entry[2], entry[3], entry[4]
    terr = entry[5] if len(entry) > 5 else None
    anchor = entry[6] if len(entry) > 6 else None
    slots = [json.dumps(slug), json.dumps(label), str(int(x)), str(int(y)), json.dumps(region)]
    if anchor:
        slots.append(json.dumps(terr) if terr else "null")
        slots.append(json.dumps(anchor))
    elif terr:
        slots.append(json.dumps(terr))
    return "  [" + ", ".join(slots) + "],"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--places", required=True)
    ap.add_argument("--add", default="[]", help="JSON array of CITIES entries")
    ap.add_argument("--drop", default="", help="comma-separated slugs to remove")
    args = ap.parse_args()

    src = open(args.places, encoding="utf-8").read()
    lines = src.split("\n")
    regions = load_regions(src)

    try:
        adds = json.loads(args.add or "[]")
    except json.JSONDecodeError as e:
        fail(f"--add is not valid JSON: {e}")
    if not isinstance(adds, list):
        fail("--add must be a JSON array of entries")

    for e in adds:
        if not isinstance(e, list) or len(e) < 5:
            fail(f"entry needs at least [slug,label,x,y,region]: {e!r}")
        region = e[4]
        if region not in regions:
            fail(f"{e[0]}: unknown region {region!r} (known: {', '.join(sorted(regions))})")
        x0, y0, x1, y1 = regions[region]
        if not (x0 <= float(e[2]) <= x1 and y0 <= float(e[3]) <= y1):
            fail(
                f"{e[0]}: ({e[2]},{e[3]}) is outside the {region} box "
                f"[{x0:g},{y0:g},{x1:g},{y1:g}] — pick coordinates inside it"
            )

    changed = []
    for slug in [s.strip() for s in args.drop.split(",") if s.strip()]:
        first, last = cities_span(lines)
        hit = [e for e in entries(lines, first, last) if e[2] == slug]
        if not hit:
            print(f"drop {slug}: not in CITIES, nothing to do")
            continue
        begin, end, _, _ = hit[0]
        del lines[begin : end + 1]
        changed.append(f"dropped {slug}")

    for e in adds:
        first, last = cities_span(lines)
        placed = entries(lines, first, last)
        if any(x[2] == e[0] for x in placed):
            print(f"add {e[0]}: already placed, nothing to do")
            continue
        same = [x for x in placed if x[3] == e[4]]
        if same:
            at = same[-1][1] + 1
        else:
            at = last
            lines.insert(at, f"  // {e[4]}")
            at += 1
        lines.insert(at, render(e))
        changed.append(f"added {e[0]} at {e[2]},{e[3]} in {e[4]}")

    if not changed:
        print("atlas_place: no change")
        return
    open(args.places, "w", encoding="utf-8").write("\n".join(lines))
    for c in changed:
        print(f"atlas_place: {c}")


if __name__ == "__main__":
    main()
