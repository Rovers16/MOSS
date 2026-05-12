import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'sched'))
from cpu_sched import Scheduler, SUCCESS, ERR_INVALID

WORKLOAD = [
    {"pid": 1, "arrival": 0, "burst": 5, "priority": 2},
    {"pid": 2, "arrival": 1, "burst": 3, "priority": 1},
    {"pid": 3, "arrival": 2, "burst": 7, "priority": 3},
    {"pid": 4, "arrival": 3, "burst": 2, "priority": 0},
]

def make_scheduler():
    s = Scheduler()
    s.sched_load_from_list(WORKLOAD)
    return s


# ── Test 1: FCFS basic correctness ───────────────────────────────────────────
def test_fcfs_completion_times():
    s = make_scheduler()
    r = s.sched_run("FCFS")
    ct = {p["pid"]: p["completion"] for p in r["processes"]}
    # P1 arrives 0, burst 5 → completes at 5
    assert ct[1] == 5,  f"P1 CT expected 5, got {ct[1]}"
    # P2 starts at 5, burst 3 → completes at 8
    assert ct[2] == 8,  f"P2 CT expected 8, got {ct[2]}"
    # P3 starts at 8, burst 7 → completes at 15
    assert ct[3] == 15, f"P3 CT expected 15, got {ct[3]}"
    # P4 starts at 15, burst 2 → completes at 17
    assert ct[4] == 17, f"P4 CT expected 17, got {ct[4]}"


# ── Test 2: FCFS waiting times ────────────────────────────────────────────────
def test_fcfs_waiting_times():
    s = make_scheduler()
    r = s.sched_run("FCFS")
    wt = {p["pid"]: p["waiting"] for p in r["processes"]}
    assert wt[1] == 0,  f"P1 WT expected 0, got {wt[1]}"
    assert wt[2] == 4,  f"P2 WT expected 4, got {wt[2]}"
    assert wt[3] == 6,  f"P3 WT expected 6, got {wt[3]}"
    assert wt[4] == 12, f"P4 WT expected 12, got {wt[4]}"


# ── Test 3: Round Robin — all processes complete ──────────────────────────────
def test_rr_all_complete():
    s = make_scheduler()
    r = s.sched_run("RR", quantum=2)
    assert len(r["processes"]) == 4
    for p in r["processes"]:
        assert p["completion"] > 0, f"P{p['pid']} never completed"
        assert p["waiting"] >= 0


# ── Test 4: Priority — lower number runs first ────────────────────────────────
def test_priority_order():
    s = make_scheduler()
    r = s.sched_run("PRIORITY")
    # P4 has priority 0 (highest) and arrives at t=3
    # P1 arrives at 0 with priority 2 — runs first since P4 hasn't arrived
    # After P1 finishes at t=5, P4 (priority 0) should run next
    gantt_pids = [entry[0] for entry in s.gantt_log]
    p4_idx = gantt_pids.index(4)
    p3_idx = gantt_pids.index(3)
    assert p4_idx < p3_idx, "P4 (priority 0) should run before P3 (priority 3)"


# ── Test 5: MLFQ — all processes complete with correct pass count ─────────────
def test_mlfq_completes():
    s = make_scheduler()
    r = s.sched_run("MLFQ", quantum=2)
    assert len(r["processes"]) == 4
    for p in r["processes"]:
        assert p["completion"] > 0, f"P{p['pid']} never completed in MLFQ"


# ── Test 6: Invalid burst rejected ───────────────────────────────────────────
def test_invalid_burst():
    s = Scheduler()
    result = s.sched_add_process(99, 0, 0)   # burst=0 is invalid
    assert result == ERR_INVALID


# ── Test 7: Averages are correct ─────────────────────────────────────────────
def test_fcfs_averages():
    s = make_scheduler()
    r = s.sched_run("FCFS")
    expected_avg_tat = (5 + 7 + 13 + 14) / 4   # 9.75
    assert abs(r["avg_turnaround"] - expected_avg_tat) < 0.01


# ── Test 8: Reset between algorithms gives independent results ────────────────
def test_independence_between_runs():
    s = make_scheduler()
    r1 = s.sched_run("FCFS")
    r2 = s.sched_run("RR", quantum=2)
    # FCFS and RR should produce different completion times for at least one process
    ct_fcfs = {p["pid"]: p["completion"] for p in r1["processes"]}
    ct_rr   = {p["pid"]: p["completion"] for p in r2["processes"]}
    assert ct_fcfs != ct_rr, "FCFS and RR should not produce identical results"


# ── Test 9: Gantt log populated after run ────────────────────────────────────
def test_gantt_log_populated():
    s = make_scheduler()
    s.sched_run("FCFS")
    assert len(s.gantt_log) > 0
    for entry in s.gantt_log:
        pid, start, end = entry
        assert end > start, f"Gantt entry end ({end}) must be > start ({start})"


# ── Test 10: Single-process edge case ────────────────────────────────────────
def test_single_process():
    s = Scheduler()
    s.sched_add_process(1, 0, 5)
    r = s.sched_run("FCFS")
    assert r["processes"][0]["completion"] == 5
    assert r["processes"][0]["waiting"] == 0


# ── Manual demo runner (not a pytest test) ───────────────────────────────────
if __name__ == "__main__":
    print("\n" + "#"*55)
    print("  MOSS — Subsystem A: CPU Scheduling Demo")
    print("#"*55)
    s = make_scheduler()
    for algo in ["FCFS", "RR", "PRIORITY", "MLFQ"]:
        r = s.sched_run(algo, quantum=2)
        s.sched_print_table(r)
        s.sched_print_gantt()
