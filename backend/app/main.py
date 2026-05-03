"""FastAPI app: receives uploads + simulation payload, dispatches to Celery,
exposes status polling and ZIP download endpoints (spec 1.2)."""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .celery_app import celery_app
from .schemas import SimulationPayload
from .tasks import run_generation
from .parser import (
    parse, transform_titles, extract_genetic_traits, extract_death_reasons,
)


app = FastAPI(title="CK3 Character History Generator", version="7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Upload helpers — frontend sends raw .txt; backend parses + returns AST
# previewable by the UI before the heavy simulation runs.
# ---------------------------------------------------------------------------

@app.post("/upload/titles")
async def upload_titles(file: UploadFile = File(...)) -> dict:
    text = (await file.read()).decode("utf-8", errors="ignore")
    ast = parse(text)
    return {
        "filename": file.filename,
        "titles": transform_titles(ast),
        "raw": text,
    }


@app.post("/upload/traits")
async def upload_traits(file: UploadFile = File(...)) -> dict:
    text = (await file.read()).decode("utf-8", errors="ignore")
    ast = parse(text)
    return {
        "filename": file.filename,
        "traits": extract_genetic_traits(ast),
        "raw": text,
    }


@app.post("/upload/deaths")
async def upload_deaths(file: UploadFile = File(...)) -> dict:
    text = (await file.read()).decode("utf-8", errors="ignore")
    ast = parse(text)
    return {
        "filename": file.filename,
        "deaths": extract_death_reasons(ast),
        "raw": text,
    }


@app.post("/upload/names")
async def upload_names(file: UploadFile = File(...)) -> dict:
    """Each line: `<list_id>: name1, name2, name3`."""
    text = (await file.read()).decode("utf-8", errors="ignore")
    name_lists: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, vals = line.split(":", 1)
        names = [v.strip() for v in vals.split(",") if v.strip()]
        if names:
            name_lists[key.strip()] = names
    return {"filename": file.filename, "name_lists": name_lists, "raw": text}


# ---------------------------------------------------------------------------
# Generation endpoints
# ---------------------------------------------------------------------------

@app.post("/generate")
def generate(payload: SimulationPayload) -> dict:
    """Dispatch the simulation to the Celery worker and return a task ID."""
    task = run_generation.delay(payload.model_dump())
    return {"task_id": task.id}


@app.get("/status/{task_id}")
def status(task_id: str) -> JSONResponse:
    task = celery_app.AsyncResult(task_id)
    body: dict = {"task_id": task_id, "state": task.state}
    if task.state == "PROGRESS" and isinstance(task.info, dict):
        body["message"] = task.info.get("message", "")
    elif task.state == "SUCCESS":
        body["result"] = {
            k: v for k, v in (task.result or {}).items()
            if k != "zip_b64"
        }
        body["message"] = "Done."
    elif task.state == "FAILURE":
        body["error"] = str(task.info)
    return JSONResponse(body)


@app.get("/download/{task_id}")
def download(task_id: str):
    task = celery_app.AsyncResult(task_id)
    if task.state != "SUCCESS":
        raise HTTPException(status_code=409, detail=f"Task is {task.state}")
    result = task.result or {}
    zip_path = result.get("zip_path")
    if not zip_path or not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Result file missing")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"ck3_history_{task_id[:8]}.zip",
    )
