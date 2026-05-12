# MOSS Design Document

## Architecture Overview

MOSS is divided into three independent subsystems integrated by a unified CLI (`main.py`). Each subsystem is self-contained with its own data structures, algorithms, and event log.

```
main.py (MOSS class)
├── Subsystem A: Scheduler      (cpu_sched.py)
├── Subsystem B: MemoryManager  (mem.py)
└── Subsystem C: SyncManager    (sync.py)
```

## Subsystem A — CPU Scheduling

**Data structure:** Process Control Block (PCB) — stores pid, arrival, burst, priority, and computed metrics (CT, TAT, WT, RT).

**Algorithms:**
- FCFS: sort by arrival, run non-preemptively in order
- Round Robin: time-slice each process using a ready queue and quantum
- Priority: non-preemptive, lowest priority number runs first
- MLFQ: three queues (RR q=2, RR q=4, FCFS); processes demoted on timeout

**Output:** results table + ASCII Gantt chart

## Subsystem B — Memory Management

**Data structure:** fixed-size frame array; access log of every reference.

**Algorithms:**
- FIFO: evict the page that has been in memory the longest (queue-based)
- LRU: evict the page least recently used (recency tracking)
- Optimal: evict the page not needed for the longest future time (lookahead)

**Address translation:** `page = address // page_size`, `offset = address % page_size`

## Subsystem C — Synchronization & Protection

**Mutex:** single owner, FIFO wait queue, explicit handoff on release.

**Semaphore:** counting permits, blocks at 0, wakes one waiter on signal.

**Producer-Consumer:** bounded circular buffer; semaphore-coordinated (empty_slots + filled_slots + mutex).

**Access Control:** role hierarchy (admin > user > guest); per-resource read/write role thresholds.

## Integration — Vertical Slice

The `vertical_slice` command demonstrates a single process flowing through all three subsystems:
1. Process created and loaded into Scheduler
2. Scheduled using Priority algorithm
3. Memory accessed via LRU page replacement
4. Mutex acquired and access control checked

All four steps must pass for the vertical slice to succeed.
