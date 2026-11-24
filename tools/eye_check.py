"""Rate the eye-check chips of the RQ3 crown-health test in a local browser page.

The chips task of the extraction writes 200 colour chips of young trees from the 2025
flight, each with the 2 m circle drawn, and an empty sheet (eye_check.csv). This serves
them on 127.0.0.1 and writes each answer straight into the sheet: on_tree is yes or no.
Only that column changes; the rows, their order and the other columns stay as written.
The page shows neither tree identifiers nor the running share of misses, so the rating
stays blind to the 10% threshold. Standard library only.

    python tools/eye_check.py                # then open http://127.0.0.1:8765
"""
from __future__ import annotations

import argparse
import csv
import http.server
import json
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/processed/rq3_crown_health"
SHEET = "eye_check.csv"
COLUMNS = {"chip", "tree_id", "on_tree"}
ANSWERS = ("yes", "no", "")
CHIP = re.compile(r"^/chips/(\d{3}\.png)$")


def read_sheet(folder: Path) -> tuple[list[str], list[dict[str, str]]]:
    with (folder / SHEET).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    if not COLUMNS <= set(fields):
        raise ValueError(f"{SHEET} needs the columns chip, tree_id and on_tree.")
    return fields, rows


def write_sheet(folder: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    """Replace the sheet in one step, so an interrupted save never leaves half a file."""
    handle, temporary = tempfile.mkstemp(dir=folder, prefix=".eye_check.", suffix=".csv")
    try:
        os.chmod(temporary, (folder / SHEET).stat().st_mode & 0o777)  # keep the sheet's permissions
        with os.fdopen(handle, "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, folder / SHEET)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def progress(rows: list[dict[str, str]]) -> dict:
    return {"chips": [row["chip"] for row in rows],
            "answers": [row["on_tree"].strip().lower() for row in rows]}


def rate(folder: Path, chip: str, answer: str) -> dict:
    """Set on_tree for one chip (yes, no, or empty to clear) and return the progress."""
    answer = answer.strip().lower()
    if answer not in ANSWERS:
        raise ValueError(f"on_tree must be yes, no or empty, not {answer!r}.")
    fields, rows = read_sheet(folder)
    matches = [row for row in rows if row["chip"] == chip]
    if len(matches) != 1:
        raise ValueError(f"{chip!r} is not in the sheet.")
    matches[0]["on_tree"] = answer
    write_sheet(folder, fields, rows)
    return progress(rows)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Eye check</title>
<style>
:root {
  --bg: #f6f7f9; --panel: #ffffff; --ink: #1d2329; --muted: #5d6874; --line: #d8dde3;
  --accent: #1268b3; --yes: #2f7d46; --no: #b3402f; --track: #e3e8ee;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #14181c; --panel: #1c2227; --ink: #e8ecf0; --muted: #9aa5b1; --line: #313a42;
    --accent: #5aa7ea; --yes: #5fb87a; --no: #e07a68; --track: #2a3239;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.45 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }
main { max-width: 720px; margin: 0 auto; padding: 20px 16px 32px; }
header { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
h1 { font-size: 20px; margin: 0; }
.count { color: var(--muted); font-variant-numeric: tabular-nums; }
.bar { height: 6px; background: var(--track); border-radius: 3px; margin: 10px 0 18px; overflow: hidden; }
.bar > div { height: 100%; width: 0; background: var(--accent); transition: width .15s; }
.question { font-size: 18px; font-weight: 600; margin: 0 0 12px; }
figure { margin: 0; background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
img { width: min(100%, 520px, 58vh); aspect-ratio: 1; image-rendering: pixelated; border-radius: 4px;
  background: var(--track); }
figcaption { display: flex; gap: 10px; align-items: center; color: var(--muted); font-variant-numeric: tabular-nums; }
.badge { font-weight: 600; padding: 2px 10px; border-radius: 999px; border: 1px solid var(--line); }
.badge.yes { color: var(--yes); border-color: var(--yes); }
.badge.no { color: var(--no); border-color: var(--no); }
.actions { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
.nav { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px; }
button { font: inherit; padding: 12px; border-radius: 8px; border: 1px solid var(--line);
  background: var(--panel); color: var(--ink); cursor: pointer; }
button.yes { border-color: var(--yes); color: var(--yes); font-weight: 600; }
button.no { border-color: var(--no); color: var(--no); font-weight: 600; }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
kbd { font: 12px ui-monospace, Menlo, monospace; padding: 1px 5px; border: 1px solid var(--line);
  border-radius: 4px; color: var(--muted); }
.status { min-height: 1.4em; margin-top: 12px; color: var(--muted); font-size: 14px; }
.status.error { color: var(--no); }
.done { margin-top: 12px; padding: 10px 12px; border-radius: 8px; border: 1px solid var(--yes); color: var(--yes); display: none; }
</style>
</head>
<body>
<main>
  <header>
    <h1>Eye check, 2025 chips</h1>
    <span class="count" id="count">…</span>
  </header>
  <div class="bar"><div id="bar"></div></div>
  <p class="question">Does the magenta circle sit on the tree?</p>
  <figure>
    <img id="chip" alt="Chip">
    <figcaption><span id="label">…</span><span class="badge" id="badge">not rated</span></figcaption>
  </figure>
  <div class="actions">
    <button class="yes" id="yes">Yes <kbd>Y</kbd></button>
    <button class="no" id="no">No <kbd>N</kbd></button>
  </div>
  <div class="nav">
    <button id="back">Back <kbd>&larr;</kbd></button>
    <button id="clear">Clear <kbd>Del</kbd></button>
    <button id="next">Next <kbd>&rarr;</kbd></button>
  </div>
  <div class="done" id="done">All chips are rated, and the sheet is saved.</div>
  <div class="status" id="status"></div>
</main>
<script>
let chips = [], answers = [], at = 0, busy = false;
const $ = (id) => document.getElementById(id);

function firstOpen(from) {
  for (let k = 0; k < chips.length; k++) {
    const i = (from + k) % chips.length;
    if (!answers[i]) return i;
  }
  return -1;
}

function show() {
  const rated = answers.filter(Boolean).length;
  $("count").textContent = `${rated} of ${chips.length} rated`;
  $("bar").style.width = `${chips.length ? 100 * rated / chips.length : 0}%`;
  $("chip").src = `/chips/${chips[at]}`;
  $("chip").alt = `Chip ${chips[at]}`;
  $("label").textContent = `Chip ${at + 1} of ${chips.length}`;
  const answer = answers[at];
  $("badge").textContent = answer || "not rated";
  $("badge").className = `badge ${answer}`;
  $("done").style.display = rated === chips.length ? "block" : "none";
  const ahead = new Image();
  ahead.src = `/chips/${chips[(at + 1) % chips.length]}`;
}

async function save(answer) {
  if (busy) return;
  busy = true;
  $("status").className = "status";
  $("status").textContent = "Saving…";
  try {
    const response = await fetch("/rate", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({chip: chips[at], on_tree: answer}),
    });
    if (!response.ok) throw new Error(await response.text());
    ({chips, answers} = await response.json());
    $("status").textContent = "Saved.";
    if (answer) {
      const open = firstOpen(at + 1);
      at = open < 0 ? Math.min(at + 1, chips.length - 1) : open;
    }
    show();
  } catch (error) {
    $("status").className = "status error";
    $("status").textContent = `Not saved: ${error.message}`;
  } finally {
    busy = false;
  }
}

function move(step) {
  at = (at + step + chips.length) % chips.length;
  $("status").textContent = "";
  show();
}

$("yes").onclick = () => save("yes");
$("no").onclick = () => save("no");
$("clear").onclick = () => save("");
$("back").onclick = () => move(-1);
$("next").onclick = () => move(1);
document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  const key = event.key.toLowerCase();
  if (key === "y") save("yes");
  else if (key === "n") save("no");
  else if (key === "delete") save("");
  else if (key === "arrowleft" || key === "backspace") move(-1);
  else if (key === "arrowright") move(1);
  else return;
  event.preventDefault();
});

fetch("/state").then((r) => r.json()).then((data) => {
  ({chips, answers} = data);
  const open = firstOpen(0);
  at = open < 0 ? 0 : open;
  show();
}).catch((error) => {
  $("status").className = "status error";
  $("status").textContent = `Could not load the sheet: ${error.message}`;
});
</script>
</body>
</html>
"""


def handler(folder: Path, port: int) -> type[http.server.BaseHTTPRequestHandler]:
    origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}

    class Handler(http.server.BaseHTTPRequestHandler):
        def reply(self, status: int, kind: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            chip = CHIP.match(self.path)
            if self.path == "/":
                self.reply(200, "text/html; charset=utf-8", PAGE.encode())
            elif self.path == "/state":
                _, rows = read_sheet(folder)
                self.reply(200, "application/json", json.dumps(progress(rows)).encode())
            elif chip and (folder / "chips" / chip.group(1)).is_file():
                self.reply(200, "image/png", (folder / "chips" / chip.group(1)).read_bytes())
            else:
                self.reply(404, "text/plain", b"Not found")

        def do_POST(self) -> None:
            if self.path != "/rate" or self.headers.get("Origin", next(iter(origins))) not in origins:
                self.reply(403, "text/plain", b"Refused")
                return
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                result = rate(folder, str(body.get("chip", "")), str(body.get("on_tree", "")))
            except (ValueError, json.JSONDecodeError) as error:
                self.reply(400, "text/plain", str(error).encode())
                return
            self.reply(200, "application/json", json.dumps(result).encode())

        def log_message(self, *args) -> None:
            pass

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--folder", type=Path, default=FOLDER, help="folder with eye_check.csv and chips/")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    folder = args.folder.resolve()
    _, rows = read_sheet(folder)
    server = http.server.HTTPServer(("127.0.0.1", args.port), handler(folder, args.port))
    rated = sum(1 for row in rows if row["on_tree"].strip())
    print(f"Eye check: {rated} of {len(rows)} rated in {folder / SHEET}")
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
