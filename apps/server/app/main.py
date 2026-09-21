import csv
import io
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from .agent_manager import AgentConnection, manager
from .alerts import evaluate_alerts
from .auth import create_access_token, current_user, hash_password, verify_password
from .config import get_settings
from .db import Base, SessionLocal, engine, get_db
from .models import AdminUser, AuditLog, CommandRecord, Device, MetricSample
from .schemas import AlertOut, DeviceOut, EnrollmentRequest, EnrollmentResponse, LoginRequest, LoginResponse, ProcessTuningRequest, TerminateRequest

settings = get_settings()
app = FastAPI(title="SmartLab OS API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(AdminUser).filter_by(username="admin").first():
            db.add(AdminUser(username="admin", password_hash=hash_password("smartlab-admin"), role="admin"))
            db.commit()
    finally:
        db.close()


def device_status(device: Device) -> str:
    if device.revoked:
        return "disconnected"
    if not device.approved:
        return "pending"
    if not device.last_seen_at:
        return "disconnected"
    age = (datetime.now(timezone.utc) - device.last_seen_at).total_seconds()
    if age > 15:
        return "stale"
    metrics = device.latest_metrics or {}
    if metrics.get("cpu_percent", 0) >= 90 or metrics.get("memory_percent", 0) >= 92:
        return "overloaded"
    if metrics.get("cpu_percent", 0) >= 75 or metrics.get("memory_percent", 0) >= 80:
        return "warning"
    return "connected"


def device_out(device: Device) -> DeviceOut:
    return DeviceOut.model_validate({"device_id": device.device_id, "name": device.name, "os_name": device.os_name, "os_version": device.os_version, "architecture": device.architecture, "agent_version": device.agent_version, "ip_address": device.ip_address, "approved": device.approved, "status": device_status(device), "last_seen_at": device.last_seen_at, "last_heartbeat_at": device.last_heartbeat_at, "metrics": device.latest_metrics or {}})


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": "smartlab-server", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(AdminUser).filter_by(username=payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    db.add(AuditLog(actor=user.username, action="login", outcome="success"))
    db.commit()
    return LoginResponse(access_token=create_access_token(user.username), user={"username": user.username, "role": user.role})


@app.get("/api/auth/me")
def me(user: AdminUser = Depends(current_user)) -> dict:
    return {"username": user.username, "role": user.role}


@app.post("/api/agents/enroll", response_model=EnrollmentResponse)
def enroll(payload: EnrollmentRequest, db: Session = Depends(get_db)) -> EnrollmentResponse:
    device = db.query(Device).filter_by(device_id=payload.device_id).first()
    if not device:
        device = Device(device_id=payload.device_id, name=payload.name, os_name=payload.os_name, os_version=payload.os_version, architecture=payload.architecture, agent_version=payload.agent_version, enrollment_code=payload.enrollment_code)
        db.add(device)
    elif device.enrollment_code and device.enrollment_code != payload.enrollment_code and not device.approved:
        raise HTTPException(status_code=403, detail="Enrollment code rejected")
    for field in ("name", "os_name", "os_version", "architecture", "agent_version"):
        setattr(device, field, getattr(payload, field))
    if device.approved and not device.credential_hash:
        token = secrets.token_urlsafe(32)
        device.credential_hash = hash_password(token)
        db.commit()
        return EnrollmentResponse(device_id=device.device_id, approved=True, agent_token=token, message="Agent approved and credential issued")
    db.commit()
    return EnrollmentResponse(device_id=device.device_id, approved=device.approved, message="Enrollment request recorded; approve it from the Control Center")


@app.post("/api/agents/{device_id}/approve")
def approve_agent(device_id: str, db: Session = Depends(get_db), user: AdminUser = Depends(current_user)) -> dict:
    device = db.query(Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.approved, device.revoked = True, False
    token = secrets.token_urlsafe(32)
    device.credential_hash = hash_password(token)
    db.add(AuditLog(actor=user.username, action="device_enrollment_approved", device_id=device_id, outcome="success"))
    db.commit()
    return {"device_id": device_id, "agent_token": token}


@app.post("/api/agents/{device_id}/revoke")
def revoke_agent(device_id: str, db: Session = Depends(get_db), user: AdminUser = Depends(current_user)) -> dict:
    device = db.query(Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.revoked, device.credential_hash = True, None
    db.add(AuditLog(actor=user.username, action="device_revoked", device_id=device_id, outcome="success"))
    db.commit()
    return {"device_id": device_id, "revoked": True}


def validate_agent(device_id: str, token: str, db: Session) -> Device:
    device = db.query(Device).filter_by(device_id=device_id).first()
    if not device or not device.approved or device.revoked or not device.credential_hash or not verify_password(token, device.credential_hash):
        raise HTTPException(status_code=403, detail="Agent authentication failed")
    return device


@app.get("/api/devices", response_model=list[DeviceOut])
def devices(_: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> list[DeviceOut]:
    return [device_out(item) for item in db.query(Device).order_by(Device.name).all()]


@app.get("/api/devices/{device_id}", response_model=DeviceOut)
def get_device(device_id: str, _: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> DeviceOut:
    device = db.query(Device).filter_by(device_id=device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_out(device)


@app.get("/api/devices/{device_id}/metrics")
def metrics(device_id: str, minutes: int = Query(15, ge=1, le=10080), _: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    samples = db.query(MetricSample).filter(MetricSample.device_id == device_id, MetricSample.observed_at >= since).order_by(MetricSample.observed_at).all()
    return [{"observed_at": item.observed_at.isoformat(), "cpu_percent": item.cpu_percent, "memory_percent": item.memory_percent, "disk_percent": item.disk_percent, "upload_bps": item.upload_bps, "download_bps": item.download_bps} for item in samples]


async def dispatch(device_id: str, command_type: str, payload: dict, db: Session, actor: str) -> dict:
    command_id = str(uuid.uuid4())
    record = CommandRecord(command_id=command_id, device_id=device_id, command_type=command_type, status="queued", request=payload)
    db.add(record)
    db.add(AuditLog(actor=actor, action=command_type, device_id=device_id, command_id=command_id, outcome="queued", details=payload))
    db.commit()
    connection = manager.connections.get(device_id)
    if not connection:
        result = {"ok": False, "reason": "device_disconnected"}
        record.status, record.result = "device_disconnected", result
        record.completed_at = datetime.now(timezone.utc)
        db.commit()
        return result
    record.status = "running"
    db.commit()
    result = await connection.send_command(command_type, {**payload, "command_id": command_id})
    record.status, record.result = ("succeeded" if result.get("ok") else "failed"), result
    record.completed_at = datetime.now(timezone.utc)
    db.add(AuditLog(actor=actor, action=command_type, device_id=device_id, command_id=command_id, outcome=record.status, details=result))
    db.commit()
    await manager.broadcast_dashboard({"type": "command_result", "device_id": device_id, "command_id": command_id, "result": result})
    return result


@app.get("/api/devices/{device_id}/processes")
async def processes(device_id: str, _: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    result = await dispatch(device_id, "list_processes", {}, db, "admin")
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Unable to list processes"))
    return result


@app.get("/api/devices/{device_id}/processes/{pid}")
async def process_detail(device_id: str, pid: int, create_time: float, _: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    result = await dispatch(device_id, "process_detail", {"pid": pid, "create_time": create_time}, db, "admin")
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "Unable to inspect process"))
    return result


@app.post("/api/devices/{device_id}/processes/{pid}/terminate")
async def terminate(device_id: str, pid: int, payload: TerminateRequest, user: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    if pid != payload.pid:
        raise HTTPException(status_code=400, detail="PID mismatch")
    return await dispatch(device_id, "terminate_process", payload.model_dump(), db, user.username)


@app.post("/api/devices/{device_id}/processes/{pid}/priority")
async def priority(device_id: str, pid: int, payload: ProcessTuningRequest, user: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return await dispatch(device_id, "set_priority", payload.model_dump(), db, user.username)


@app.post("/api/devices/{device_id}/processes/{pid}/affinity")
async def affinity(device_id: str, pid: int, payload: ProcessTuningRequest, user: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    return await dispatch(device_id, "set_affinity", payload.model_dump(), db, user.username)


@app.get("/api/alerts", response_model=list[AlertOut])
def alerts(_: AdminUser = Depends(current_user), db: Session = Depends(get_db)):
    from .models import Alert
    return db.query(Alert).order_by(desc(Alert.last_observed_at)).limit(200).all()


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, user: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    from .models import Alert
    alert = db.query(Alert).filter_by(id=alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    db.add(AuditLog(actor=user.username, action="alert_acknowledged", device_id=alert.device_id, outcome="success", details={"alert_id": alert.id}))
    db.commit()
    return {"id": alert.id, "acknowledged": True}


@app.get("/api/activity")
def activity(_: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": item.id, "actor": item.actor, "action": item.action, "device_id": item.device_id, "outcome": item.outcome, "created_at": item.created_at.isoformat(), "details": item.details} for item in db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(100).all()]


@app.get("/api/reports/resource.csv")
def resource_csv(_: AdminUser = Depends(current_user), db: Session = Depends(get_db)) -> StreamingResponse:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["device_id", "observed_at", "cpu_percent", "memory_percent", "disk_percent", "upload_bps", "download_bps"])
    for item in db.query(MetricSample).order_by(MetricSample.observed_at.desc()).limit(10000).all():
        writer.writerow([item.device_id, item.observed_at.isoformat(), item.cpu_percent, item.memory_percent, item.disk_percent, item.upload_bps, item.download_bps])
    stream.seek(0)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=smartlab-resource-report.csv"})


@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    manager.dashboard_sockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.dashboard_sockets.discard(websocket)


@app.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    connection = None
    db = SessionLocal()
    try:
        hello = await websocket.receive_json()
        if hello.get("type") != "hello":
            await websocket.close(code=1008)
            return
        device_id, token = hello.get("device_id"), hello.get("token")
        device = validate_agent(device_id, token, db)
        connection = AgentConnection(websocket, device_id)
        await manager.register(connection)
        device.ip_address = websocket.client.host if websocket.client else None
        device.last_seen_at = device.last_heartbeat_at = datetime.now(timezone.utc)
        db.commit()
        await websocket.send_json({"type": "hello_ack", "device_id": device_id, "server_time": datetime.now(timezone.utc).isoformat()})
        await manager.broadcast_dashboard({"type": "device_status", "device_id": device_id, "status": "connected"})
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "telemetry":
                payload = message.get("payload", {})
                device.latest_metrics = payload
                device.last_seen_at = device.last_heartbeat_at = datetime.now(timezone.utc)
                db.add(MetricSample(device_id=device_id, cpu_percent=payload.get("cpu_percent"), memory_percent=payload.get("memory_percent"), disk_percent=payload.get("disk_percent"), upload_bps=payload.get("upload_bps"), download_bps=payload.get("download_bps"), payload=payload))
                evaluate_alerts(db, device_id, payload)
                db.commit()
                await manager.broadcast_dashboard({"type": "telemetry", "device_id": device_id, "payload": payload, "status": device_status(device)})
            elif message.get("type") == "heartbeat":
                device.last_seen_at = device.last_heartbeat_at = datetime.now(timezone.utc)
                db.commit()
            elif message.get("type") == "command_result":
                connection.resolve(message.get("request_id", ""), message.get("result", {}))
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close(code=1011)
    finally:
        if connection:
            await manager.unregister(connection.device_id, connection)
            await manager.broadcast_dashboard({"type": "device_status", "device_id": connection.device_id, "status": "disconnected"})
        db.close()

