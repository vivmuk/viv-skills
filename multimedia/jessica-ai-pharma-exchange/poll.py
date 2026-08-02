import requests, json, time, sys
from pathlib import Path

state_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("queue_state.json")
outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

with open(Path.home() / ".hermes/config.yaml") as f:
    import yaml
    cfg = yaml.safe_load(f)
api_key = cfg.get("api_key") or cfg.get("model", {}).get("api_key")
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

state = json.loads(state_path.read_text())
model = state["model"]

mapping = {
    state["seg1_queue_id"]: outdir / "seg1.mp4",
    state["seg2_queue_id"]: outdir / "seg2.mp4",
}

pending = dict(mapping)
while pending:
    for qid, outpath in list(pending.items()):
        resp = requests.post(
            "https://api.venice.ai/api/v1/video/retrieve",
            headers=headers,
            json={"model": model, "queue_id": qid},
            timeout=120,
        )
        ct = resp.headers.get("Content-Type", "")
        if ct == "video/mp4":
            outpath.write_bytes(resp.content)
            print(f"Downloaded {outpath.name}")
            del pending[qid]
        else:
            data = resp.json()
            status = data.get("status")
            print(f"{outpath.name}: {status}")
            if status in ("COMPLETED", "FAILED", "CANCELLED"):
                if status != "COMPLETED":
                    print(f"ERROR {outpath.name}: {data}")
                del pending[qid]
    if pending:
        time.sleep(30)
print("All done.")
