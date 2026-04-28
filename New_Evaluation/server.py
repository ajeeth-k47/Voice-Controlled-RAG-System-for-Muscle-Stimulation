import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_PATH = BASE_DIR / "data" / "submissions.json"
WEB_DIR = BASE_DIR / "web"
MOTION_DIR = BASE_DIR / "motion"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_config() -> dict:
    cfg = read_json(CONFIG_PATH, {})
    if not cfg:
        raise RuntimeError("config.json is missing or invalid.")
    return cfg


# --- Data models ---

class BPQRating(BaseModel):
    body_part: str
    label: str  # Good | Partially Good | Bad | Not Relevant

class MovementResponse(BaseModel):
    movement_id: str
    intended_command: str | None = None
    wbs: int = Field(ge=1, le=5)
    bpq: list[BPQRating]

class SubmissionPayload(BaseModel):
    participant_id: str | None = None
    comment: str | None = None
    responses: list[MovementResponse]

app = FastAPI(title="Movement Evaluation (Li et al. 2025)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config")
def get_config():
    return load_config()


@app.post("/api/submit")
def submit(payload: SubmissionPayload):
    cfg = load_config()
    movement_ids = {m["id"] for m in cfg["movements"]}

    if len(payload.responses) != len(cfg["movements"]):
        raise HTTPException(status_code=400, detail=f"Expected {len(cfg['movements'])} responses.")

    movement_cfg_by_id = {m["id"]: m for m in cfg["movements"]}
    for r in payload.responses:
        if r.movement_id not in movement_ids:
            raise HTTPException(status_code=400, detail=f"Unknown movement: {r.movement_id}")
        mv_cfg = movement_cfg_by_id[r.movement_id]
        if mv_cfg.get("custom") and not (r.intended_command or "").strip():
            raise HTTPException(status_code=400, detail=f"Missing intended_command for {r.movement_id}")
        if not r.bpq:
            raise HTTPException(status_code=400, detail=f"Missing BPQ ratings for {r.movement_id}")

    all_submissions = read_json(DATA_PATH, [])
    record = {
        "submission_id": f"sub_{int(datetime.utcnow().timestamp() * 1000)}",
        "participant_id": (payload.participant_id or "").strip() or None,
        "comment": (payload.comment or "").strip() or None,
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "responses": [r.model_dump() for r in payload.responses],
    }
    all_submissions.append(record)
    write_json(DATA_PATH, all_submissions)
    return {"success": True, "submission_id": record["submission_id"]}


@app.get("/api/results")
def results():
    cfg = load_config()
    submissions = read_json(DATA_PATH, [])
    movements = cfg["movements"]
    movement_map = {m["id"]: m for m in movements}

    if not submissions:
        return {
            "submission_count": 0,
            "wbs_per_movement": [],
            "overall_wbs": 0.0,
            "bpq_per_movement": [],
            "bpq_summary_hand": [],
            "bpq_summary_soccer": [],
            "custom_by_participant": [],
        }

    # --- WBS per movement ---
    wbs_by_movement: dict[str, list[int]] = {m["id"]: [] for m in movements}
    for sub in submissions:
        for r in sub["responses"]:
            mid = r["movement_id"]
            if mid in wbs_by_movement:
                wbs_by_movement[mid].append(r["wbs"])

    wbs_per_movement = []
    for m in movements:
        scores = wbs_by_movement[m["id"]]
        avg = round(sum(scores) / len(scores), 2) if scores else 0.0
        intended_commands = []
        if m.get("custom"):
            for sub in submissions:
                for r in sub.get("responses", []):
                    if r.get("movement_id") == m["id"]:
                        txt = (r.get("intended_command") or "").strip()
                        if txt:
                            intended_commands.append(txt)
        wbs_per_movement.append({
            "movement_id": m["id"],
            "command": m["command"],
            "category": m["category"],
            "custom": bool(m.get("custom")),
            "intended_commands": intended_commands,
            "mean_wbs": avg,
            "ratings": scores,
            "n": len(scores),
        })

    all_means = [w["mean_wbs"] for w in wbs_per_movement if w["n"] > 0]
    overall_wbs = round(sum(all_means) / len(all_means), 2) if all_means else 0.0

    # --- BPQ per movement per body part ---
    bpq_by_movement: dict[str, dict[str, list[str]]] = {}
    for m in movements:
        if m.get("custom"):
            bpq_by_movement[m["id"]] = {}
        else:
            bpq_by_movement[m["id"]] = {bp: [] for bp in m["body_parts"]}

    for sub in submissions:
        for r in sub["responses"]:
            mid = r["movement_id"]
            if mid not in bpq_by_movement:
                continue
            for bpq_entry in r.get("bpq", []):
                bp = bpq_entry["body_part"]
                if bp not in bpq_by_movement[mid]:
                    bpq_by_movement[mid][bp] = []
                bpq_by_movement[mid][bp].append(bpq_entry["label"])

    bpq_per_movement = []
    for m in movements:
        parts = []
        body_parts = list(bpq_by_movement[m["id"]].keys())
        for bp in body_parts:
            labels = bpq_by_movement[m["id"]].get(bp, [])
            relevant = [l for l in labels if l != "Not Relevant"]
            total_relevant = len(relevant)
            good_count = sum(1 for l in relevant if l == "Good")
            partial_count = sum(1 for l in relevant if l == "Partially Good")
            bad_count = sum(1 for l in relevant if l == "Bad")
            not_relevant_count = sum(1 for l in labels if l == "Not Relevant")
            parts.append({
                "body_part": bp,
                "good_pct": round(good_count / total_relevant * 100, 1) if total_relevant else 0.0,
                "partial_pct": round(partial_count / total_relevant * 100, 1) if total_relevant else 0.0,
                "bad_pct": round(bad_count / total_relevant * 100, 1) if total_relevant else 0.0,
                "not_relevant": not_relevant_count,
                "total_ratings": len(labels),
            })
        bpq_per_movement.append({
            "movement_id": m["id"],
            "command": m["command"],
            "custom": bool(m.get("custom")),
            "body_parts": parts,
        })

    def summarize_bpq(body_parts_allow: set[str], movement_ids_allow: set[str]) -> list[dict[str, Any]]:
        totals: dict[str, dict[str, int]] = {}
        for mid, parts_map in bpq_by_movement.items():
            if mid not in movement_ids_allow:
                continue
            for bp, labels in parts_map.items():
                if bp not in body_parts_allow:
                    continue
                bucket = totals.setdefault(bp, {"Good": 0, "Partially Good": 0, "Bad": 0, "Not Relevant": 0, "Total": 0})
                for lab in labels:
                    bucket["Total"] += 1
                    if lab in bucket:
                        bucket[lab] += 1

        rows = []
        for bp, counts in totals.items():
            denom = counts["Good"] + counts["Partially Good"] + counts["Bad"]
            rows.append({
                "body_part": bp,
                "good_pct": round(counts["Good"] / denom * 100, 1) if denom else 0.0,
                "partial_pct": round(counts["Partially Good"] / denom * 100, 1) if denom else 0.0,
                "bad_pct": round(counts["Bad"] / denom * 100, 1) if denom else 0.0,
                "not_relevant": counts["Not Relevant"],
                "total_ratings": counts["Total"],
                "relevant_ratings": denom,
            })
        rows.sort(key=lambda r: r["body_part"])
        return rows

    hand_parts = {"Thumb", "Index Finger", "Middle Finger", "Ring Finger", "Little Finger"}
    soccer_parts = {"Hip", "Knee", "Ankle", "Foot"}
    hand_movement_ids = {
        m["id"]
        for m in movements
        if ("Finger" in " ".join(m.get("body_parts", []))) or (m.get("category") != "Lower Limb" and m["id"] != "soccer_kick")
    }
    # The custom movements are hand-only by your study design.
    for m in movements:
        if m.get("custom"):
            hand_movement_ids.add(m["id"])

    soccer_movement_ids = {"soccer_kick"} if "soccer_kick" in movement_map else set()

    custom_ids = [m["id"] for m in movements if m.get("custom")]
    custom_by_participant = []
    comments = []
    for sub in submissions:
        rows = []
        resp_by_id = {r.get("movement_id"): r for r in sub.get("responses", [])}
        for cid in custom_ids:
            r = resp_by_id.get(cid) or {}
            rows.append({
                "movement_id": cid,
                "intended_command": (r.get("intended_command") or "").strip() or None,
                "wbs": r.get("wbs"),
                "bpq": r.get("bpq", []),
            })
        custom_by_participant.append({
            "submission_id": sub.get("submission_id"),
            "participant_id": sub.get("participant_id"),
            "timestamp_utc": sub.get("timestamp_utc"),
            "custom": rows,
        })
        comment_text = (sub.get("comment") or "").strip()
        if comment_text:
            comments.append({
                "submission_id": sub.get("submission_id"),
                "participant_id": sub.get("participant_id"),
                "comment": comment_text,
            })

    return {
        "submission_count": len(submissions),
        "wbs_per_movement": wbs_per_movement,
        "overall_wbs": overall_wbs,
        "bpq_per_movement": bpq_per_movement,
        "bpq_summary_hand": summarize_bpq(hand_parts, hand_movement_ids),
        "bpq_summary_soccer": summarize_bpq(soccer_parts, soccer_movement_ids),
        "custom_by_participant": custom_by_participant,
        "comments": comments,
    }


app.mount("/motion", StaticFiles(directory=str(MOTION_DIR)), name="motion")
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8010, reload=True)
