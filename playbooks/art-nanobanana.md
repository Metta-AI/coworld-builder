# Board art with nano-banana (Gemini image generation)

Every coworld ships board art, and the sandbox has no GPU, no Docker and no art tool — but it
does have `curl`, `python3` and a vault credential `GEMINI_API_KEY` that is substituted at egress
for `generativelanguage.googleapis.com`. Use it. **Procedurally drawn 64 px rigs are the
fallback, not the target**: sprites are nano-banana renders of the Softmax cog, one kit per role,
so a spectator can tell roles apart at board scale without reading a label.

The worked example is `Metta-AI/cogame-raid` PR #2 (`scripts/art/source/cogs_sheet.png` +
`scripts/art/split_cog_sheet.py`): three cogs on one sheet — tank with a riveted tower shield,
healer with a white medic canister + spray wand, dps with twin energy blades — keyed, split and
padded into `cog_<role>.png`.

## Rules

- The key is **never** printed, never written to a file, never passed as a URL parameter.
  It is the header `x-goog-api-key: $GEMINI_API_KEY`; the vault substitutes it on egress to
  `generativelanguage.googleapis.com` only. `$GEMINI_API_KEY` in the sandbox is a placeholder,
  so `echo $GEMINI_API_KEY` proves nothing and leaks nothing — still don't.
- Model: `gemini-2.5-flash-image` (this is what "nano-banana" means). Endpoint:
  `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent`.
- Commit the **source render** under `scripts/art/source/` and the **script** that turns it into
  sprites, the same way the procedural generators are committed: the assets must be reproducible,
  not mysterious. Commit the derived PNGs too (CI does not regenerate art).
- Budget: at most ~10 generations per coworld. One sheet per character family beats one call per
  sprite — a single render keeps the style consistent across roles.
- Keep the Softmax cog as the character: wheeled robot, screen face, riveted shoulders. Pass the
  canonical reference as an `inline_data` part so the style is anchored (every starter ships one
  under `client/art/` or `data/art/`; `coworld-tools/games/games/cogony/docs/img/cog.png` is the
  original).

## Recipe

### 1. Generate a sheet on a flat chroma backdrop

```bash
python3 - <<'PY'
import base64, json, urllib.request, os
ref = base64.b64encode(open("client/art/cog.png", "rb").read()).decode()   # style anchor
prompt = """Using this robot character ("cog") as the exact character design reference, draw
THREE of these cogs side by side in one row, evenly spaced, same size, full body, front-facing,
same clean cartoon rendering. Background: perfectly flat, solid, uniform pure bright green
(#00FF00), no shadows, no gradients, no floor — it will be chroma-keyed out.
LEFT — TANK: blue (#4B7BEC) plating, big riveted steel tower shield, heavy pauldrons.
MIDDLE — HEALER: green (#2ECC71) accents, white medic canister with a green cross, spray wand.
RIGHT — DPS: gold (#F2C14E) accents, twin glowing energy blades. No text, no labels."""
body = {"contents": [{"parts": [
    {"inline_data": {"mime_type": "image/png", "data": ref}},
    {"text": prompt}]}],
  "generationConfig": {"responseModalities": ["IMAGE"]}}
req = urllib.request.Request(
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent",
  data=json.dumps(body).encode(),
  headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "content-type": "application/json"})
resp = json.load(urllib.request.urlopen(req))
part = next(p for p in resp["candidates"][0]["content"]["parts"] if "inlineData" in p)
os.makedirs("scripts/art/source", exist_ok=True)
open("scripts/art/source/cogs_sheet.png", "wb").write(base64.b64decode(part["inlineData"]["data"]))
PY
```

(`curl` works just as well: `-H "x-goog-api-key: $GEMINI_API_KEY"` and the same JSON body. The
vault substitutes on either.) A non-200 is logged with its body — a 429 is quota, wait a minute;
a 400 `SAFETY`/`IMAGE_OTHER` means re-word the prompt, not retry it.

### 2. Key, split, pad

Gemini does not return alpha, and the "pure green" you asked for comes back as *some* green with
a tinted edge. Flood-fill from the image border (so green accents inside a character survive),
take the backdrop colour as the **median of the border** (corners sometimes carry a smudge), then
split the row on empty columns and pad each part to a square. `Pillow` is the only dependency:

```bash
python3 -c 'import PIL' 2>/dev/null || python3 -m pip install --user pillow
```

Copy `scripts/art/split_cog_sheet.py` from `Metta-AI/cogame-raid` (it is ~90 lines: key →
split → pad → resize to 128 px) and adjust `ROLES` to your file names. Run it, copy the output
into both art directories the starter uses (`data/art/` and `client/art/` in raid; paintbot
lineage uses only one), and leave the procedural generator in place for the assets you did not
replace — note in its docstring which files it no longer owns.

### 3. Draw it so the kit reads

A 128 px sprite drawn at 28 px is the old rig again. The raid viewer draws cogs at **48 px**
anchored at the feet, moves the role-tint ring to a **ground ellipse under the wheels** (a ring
around the body hides the shield/canister/blades), and lifts the alias label above the head.
Check the result with a real render — headless Chrome against a synthetic frame is enough:

```bash
"/path/to/chrome" --headless=new --screenshot=/tmp/shot.png --window-size=1235,659 \
  --virtual-time-budget=4000 http://127.0.0.1:8531/_harness.html
```

(the sandbox has no Chrome; in the cloud let CI's `viewer_smoke.mjs` screenshot do it and read
the artifact back.)

## Checklist (goes in the review-loop report)

- [ ] Every cog sprite is a nano-banana render of the Softmax cog, not a procedural rig.
- [ ] Each role carries a distinct, large item; the roles are tellable apart with labels hidden.
- [ ] `scripts/art/source/*.png` and the split script are committed; the generator docstring says
      which files it no longer owns.
- [ ] No key in any file, log, commit, or CI input.
