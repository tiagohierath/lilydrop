"""Read-only production checks: active links, design asset, and download bytes."""
import sys
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lilydrop

base = "https://files.navylily.tv"
def fetch(path, ranged=False):
    args = ["curl", "--fail", "--silent", "--show-error", "--max-time", "20"]
    if ranged:
        args += ["--range", "0-63"]
    return subprocess.check_output(args + [base + path])

state = lilydrop.load_state()
checked = 0
for token, share in state["shares"].items():
    if lilydrop.share_status(share) != "active":
        continue
    delivery = state["deliveries"].get(share.get("delivery_id"))
    if delivery:
        route = f"/{delivery['project_id']}/{delivery['number']}/{token}"
        package = Path(delivery["package_path"])
    else:
        route = f"/s/{token}"
        package = Path(share["legacy_file"])
    body = fetch(route).decode()
    assert 'class="hero"' in body and 'lilydrop-folder-chrome-isometric.png' in body
    with package.open("rb") as source:
        assert fetch(route + "/" + lilydrop.quote(package.name), True) == source.read(64)
    checked += 1
assert fetch("/lilydrop-folder-chrome-isometric.png") == (Path(lilydrop.__file__).parent / "assets/sophiedrop-folder-chrome-isometric.png").read_bytes()
assert checked > 0
print(f"Verified {checked} active links, download ranges, and exact design image.")
