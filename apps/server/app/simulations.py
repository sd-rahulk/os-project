from dataclasses import dataclass


@dataclass
class Job:
    pid: str
    arrival: int
    burst: int
    priority: int


def _metrics(order: list[tuple[str, int, int]], jobs: dict[str, Job]) -> dict:
    time = 0
    first: dict[str, int] = {}
    completion: dict[str, int] = {}
    gantt = []
    for pid, start, duration in order:
        gantt.append({"pid": pid, "start": start, "end": start + duration})
        first.setdefault(pid, start)
        time = start + duration
        completion[pid] = time
    rows = []
    for pid, job in jobs.items():
        end = completion.get(pid, job.arrival)
        rows.append({"pid": pid, "waiting": max(0, end - job.arrival - job.burst), "turnaround": max(0, end - job.arrival), "response": max(0, first.get(pid, job.arrival) - job.arrival)})
    total_time = max((item["end"] for item in gantt), default=0)
    return {"gantt": gantt, "rows": rows, "average_waiting": sum(r["waiting"] for r in rows) / len(rows) if rows else 0, "average_turnaround": sum(r["turnaround"] for r in rows) / len(rows) if rows else 0, "cpu_utilization": sum(j.burst for j in jobs.values()) / total_time * 100 if total_time else 0, "throughput": len(jobs) / total_time if total_time else 0}


def fcfs(jobs: list[Job]) -> dict:
    current = 0
    order = []
    for job in sorted(jobs, key=lambda j: (j.arrival, j.pid)):
        current = max(current, job.arrival)
        order.append((job.pid, current, job.burst))
        current += job.burst
    return _metrics(order, {j.pid: j for j in jobs})


def non_preemptive(jobs: list[Job], key) -> dict:
    pending, current, order = jobs[:], 0, []
    while pending:
        available = [j for j in pending if j.arrival <= current]
        if not available:
            current = min(j.arrival for j in pending)
            available = [j for j in pending if j.arrival <= current]
        job = min(available, key=key)
        pending.remove(job)
        order.append((job.pid, current, job.burst))
        current += job.burst
    return _metrics(order, {j.pid: j for j in jobs})


def preemptive(jobs: list[Job], shortest: bool) -> dict:
    remaining = {j.pid: j.burst for j in jobs}
    current, segments, finished = 0, [], set()
    while len(finished) < len(jobs):
        available = [j for j in jobs if j.arrival <= current and j.pid not in finished]
        if not available:
            current = min(j.arrival for j in jobs if j.pid not in finished)
            continue
        job = min(available, key=(lambda j: (remaining[j.pid], j.arrival, j.pid)) if shortest else (lambda j: (j.priority, j.arrival, j.pid)))
        if segments and segments[-1][0] == job.pid and segments[-1][2] == current:
            pid, start, _ = segments[-1]
            segments[-1] = (pid, start, current + 1)
        else:
            segments.append((job.pid, current, current + 1))
        remaining[job.pid] -= 1
        current += 1
        if remaining[job.pid] <= 0:
            finished.add(job.pid)
    return _metrics([(pid, start, end - start) for pid, start, end in segments], {j.pid: j for j in jobs})


def round_robin(jobs: list[Job], quantum: int) -> dict:
    pending = sorted(jobs, key=lambda j: (j.arrival, j.pid))
    remaining = {j.pid: j.burst for j in jobs}
    current, queue, order = 0, [], []
    while pending or queue:
        while pending and pending[0].arrival <= current:
            queue.append(pending.pop(0))
        if not queue:
            current = pending[0].arrival
            continue
        job = queue.pop(0)
        duration = min(quantum, remaining[job.pid])
        order.append((job.pid, current, duration))
        current += duration
        remaining[job.pid] -= duration
        while pending and pending[0].arrival <= current:
            queue.append(pending.pop(0))
        if remaining[job.pid] > 0:
            queue.append(job)
    return _metrics(order, {j.pid: j for j in jobs})


def compare(jobs: list[Job], quantum: int = 2) -> dict:
    return {"fcfs": fcfs(jobs), "sjf": non_preemptive(jobs, lambda j: (j.burst, j.arrival, j.pid)), "srtf": preemptive(jobs, True), "round_robin": round_robin(jobs, quantum), "priority": non_preemptive(jobs, lambda j: (j.priority, j.arrival, j.pid))}


def allocate(blocks: list[int], requests: list[int], strategy: str) -> dict:
    free = blocks[:]
    placements = []
    for request in requests:
        candidates = [(i, size) for i, size in enumerate(free) if size >= request]
        if not candidates:
            placements.append({"request": request, "block": None, "status": "fragmented_or_insufficient"})
            continue
        index, size = (min(candidates, key=lambda item: item[1]) if strategy == "best_fit" else max(candidates, key=lambda item: item[1]) if strategy == "worst_fit" else candidates[0])
        free[index] -= request
        placements.append({"request": request, "block": index, "remaining": free[index], "status": "allocated"})
    return {"placements": placements, "remaining": free, "external_fragmentation": sum(size for size in free if size > 0)}
