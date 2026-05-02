import asyncio
import csv
import io
import json
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.engine import default_dorks, geolocate_url, run_session_with_stop


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


class StartSessionRequest(BaseModel):
    dorks: List[str] = Field(default_factory=default_dorks)
    per_dork_limit: int = Field(default=10, ge=1, le=100)
    pause_min: int = Field(default=1, ge=0, le=30)
    pause_max: int = Field(default=2, ge=0, le=60)
    check_tor: bool = True
    proxy: str = "http://127.0.0.1:8118"


@dataclass
class SessionState:
    session_id: str
    created_at: float
    config: Dict[str, Any]
    status: str = "queued"
    summary: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    listeners: List[queue.Queue] = field(default_factory=list)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    worker_thread: Optional[threading.Thread] = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def to_dict(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "status": self.status,
                "config": self.config,
                "summary": self.summary,
                "events": self.events[-100:],
            }


SESSIONS: Dict[str, SessionState] = {}
SESSIONS_LOCK = threading.Lock()
GEO_CACHE: Dict[str, Dict[str, Any]] = {}
GEO_CACHE_LOCK = threading.Lock()

app = FastAPI(title="Nour-Net Command Center", version="2.1")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _push_event(session: SessionState, event: str, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
    payload = {
        "ts": time.time(),
        "event": event,
        "level": level,
        "message": message,
        "data": data or {},
    }
    with session.lock:
        session.events.append(payload)
        if len(session.events) > 2000:
            session.events = session.events[-1000:]
        listeners = list(session.listeners)

    for listener in listeners:
        try:
            listener.put_nowait(payload)
        except Exception:
            continue


def _run_session(session_id: str) -> None:
    with SESSIONS_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        return

    with session.lock:
        session.status = "running"

    def emitter(event: str, message: str, level: str = "info", data: Optional[Dict[str, Any]] = None) -> None:
        _push_event(session, event=event, message=message, level=level, data=data)

    try:
        summary = run_session_with_stop(
            config=session.config,
            emit=emitter,
            should_stop=session.cancel_event.is_set,
        )
        with session.lock:
            if any(e["event"] == "SESSION_ABORTED" for e in session.events):
                session.status = "aborted"
            elif summary.get("stopped"):
                session.status = "stopped"
            else:
                session.status = "completed"
            session.summary = summary
    except Exception as exc:
        _push_event(session, event="SESSION_FAILED", message=f"Erreur critique: {exc}", level="error")
        with session.lock:
            session.status = "failed"


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": "nour-net-command-center"}


@app.get("/api/sessions")
def list_sessions() -> Dict[str, Any]:
    with SESSIONS_LOCK:
        items = [session.to_dict() for session in SESSIONS.values()]
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"sessions": items[:25]}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str) -> Dict[str, Any]:
    with SESSIONS_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.post("/api/sessions")
def create_session(payload: StartSessionRequest) -> Dict[str, Any]:
    if payload.pause_min > payload.pause_max:
        raise HTTPException(status_code=400, detail="pause_min must be <= pause_max")

    session_id = uuid.uuid4().hex[:10]
    state = SessionState(
        session_id=session_id,
        created_at=time.time(),
        config=payload.model_dump(),
    )
    _push_event(
        state,
        event="SESSION_QUEUED",
        message="Session en file d'attente",
        level="info",
    )

    with SESSIONS_LOCK:
        SESSIONS[session_id] = state

    thread = threading.Thread(target=_run_session, args=(session_id,), daemon=True)
    state.worker_thread = thread
    thread.start()

    return {"session_id": session_id, "status": "queued"}


@app.post("/api/sessions/{session_id}/stop")
def stop_session(session_id: str) -> Dict[str, Any]:
    with SESSIONS_LOCK:
        session = SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    with session.lock:
        current_status = session.status

    if current_status not in {"queued", "running"}:
        return {"session_id": session_id, "status": current_status, "stoppable": False}

    session.cancel_event.set()
    _push_event(
        session,
        event="STOP_REQUESTED",
        message="Demande d'arret recue, interruption en cours",
        level="warning",
    )

    return {"session_id": session_id, "status": "stopping", "stoppable": True}


@app.get("/api/sessions/{session_id}/export")
def export_session(session_id: str, format: str = Query(default="json", pattern="^(json|csv)$")) -> Response:
    with SESSIONS_LOCK:
        session = SESSIONS.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    data = session.to_dict()
    filename = f"nour-session-{session_id}.{format}"

    if format == "json":
        body = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "event", "level", "message", "data"])
    for event in data.get("events", []):
        writer.writerow([
            event.get("ts"),
            event.get("event"),
            event.get("level"),
            event.get("message"),
            json.dumps(event.get("data", {}), ensure_ascii=False),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/geolocate")
def geolocate(target_url: str = Query(..., min_length=3)) -> Dict[str, Any]:
    with GEO_CACHE_LOCK:
        cached = GEO_CACHE.get(target_url)
    if cached is not None:
        return {"cached": True, **cached}

    result = geolocate_url(target_url)
    with GEO_CACHE_LOCK:
        GEO_CACHE[target_url] = result
    return {"cached": False, **result}


@app.websocket("/api/sessions/{session_id}/ws")
async def session_stream(websocket: WebSocket, session_id: str) -> None:
    await websocket.accept()

    with SESSIONS_LOCK:
        session = SESSIONS.get(session_id)
    if not session:
        await websocket.send_json({"event": "ERROR", "message": "Session not found", "level": "error"})
        await websocket.close(code=1008)
        return

    listener: queue.Queue = queue.Queue()
    with session.lock:
        session.listeners.append(listener)
        snapshot = list(session.events[-150:])

    try:
        await websocket.send_json({"event": "SNAPSHOT", "data": {"events": snapshot, "session": session.to_dict()}})
        while True:
            loop = asyncio.get_running_loop()
            event = await loop.run_in_executor(None, listener.get)
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        with session.lock:
            if listener in session.listeners:
                session.listeners.remove(listener)
