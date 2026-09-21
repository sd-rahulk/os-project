from apps.server.app.simulations import Job, allocate, compare


def test_scheduling_algorithms_return_real_metrics():
    jobs = [Job("P1", 0, 5, 2), Job("P2", 1, 2, 1), Job("P3", 2, 1, 3)]
    results = compare(jobs, quantum=2)
    assert set(results) == {"fcfs", "sjf", "srtf", "round_robin", "priority"}
    assert all("gantt" in item and "average_waiting" in item for item in results.values())
    assert results["fcfs"]["average_waiting"] == 3


def test_memory_fit_strategies_are_not_hardcoded():
    result = allocate([100, 300, 200], [180, 90], "best_fit")
    assert result["placements"][0]["block"] == 2
    assert result["placements"][1]["block"] == 0
    assert allocate([50], [60], "first_fit")["placements"][0]["status"] == "fragmented_or_insufficient"
