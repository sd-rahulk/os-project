from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import Alert


def evaluate_alerts(db: Session, device_id: str, metrics: dict) -> None:
    now = datetime.now(timezone.utc)
    checks = [("high_cpu", "cpu_percent", 90, "critical", "CPU is above the critical threshold"), ("high_memory", "memory_percent", 92, "critical", "Memory is above the critical threshold"), ("low_disk", "disk_percent", 95, "critical", "Disk usage is above the critical threshold")]
    for kind, metric, threshold, severity, message in checks:
        value = metrics.get(metric)
        if value is None:
            continue
        active = float(value) >= threshold
        alert = db.query(Alert).filter_by(device_id=device_id, kind=kind, resolved=False).first()
        if active and not alert:
            db.add(Alert(device_id=device_id, kind=kind, severity=severity, message=message, metric=metric, threshold=threshold))
        elif active and alert:
            alert.last_observed_at = now
        elif alert:
            alert.resolved = True
            alert.last_observed_at = now

