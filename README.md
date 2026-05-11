# MOSS — Mini OS Services Simulator
**COSC 514 | Bowie State University | Spring 2026**

A fully integrated command-line simulator covering three core OS subsystems: CPU Scheduling, Memory Management, and Synchronization & Protection. All three subsystems run together in a single interactive shell.

---

## Requirements

- Python 3.8 or higher
- No external libraries required for the simulator itself
- `pytest` required only for running tests: `pip install pytest`

---

## Files

| File | Description |
|---|---|
| `main.py` | Entry point — interactive CLI that wires all three subsystems |
| `cpu_sched.py` | Subsystem A: CPU Scheduling (FCFS, RR, Priority, MLFQ) |
| `mem.py` | Subsystem B: Memory Management (FIFO, LRU, Optimal) |
| `sync.py` | Subsystem C: Synchronization & Protection |
| `test_sched.py` | pytest tests for Subsystem A |
| `test_mem.py` | pytest tests for Subsystem B |
| `test_sync.py` | pytest tests for Subsystem C |

All files must be in the **same directory**.

---

## How to Run

```bash
python3 main.py
```

You will see the MOSS prompt:
```
moss>
```

Type `help` to see all available commands. Type `exit` to quit.

---

## Quick Start — Vertical Slice Demo

The fastest way to see everything working is to run the built-in end-to-end demo:

```
moss> vertical_slice
```

This automatically runs one process through all three subsystems in sequence and prints four checkmarks confirming each step passed.

---

## Subsystem A — CPU Scheduling

Create processes and run scheduling algorithms. Each run prints a results table and a Gantt chart.

```
moss> create_process 1 0 5 2      # pid=1, arrival=0, burst=5, priority=2
moss> create_process 2 1 3 1
moss> create_process 3 2 7 3
moss> create_process 4 3 2 0
moss> list_processes               # show all loaded processes

moss> schedule FCFS                # First Come First Served
moss> schedule RR 2                # Round Robin, quantum=2
moss> schedule PRIORITY            # Priority (lower number = higher priority)
moss> schedule MLFQ 2              # Multilevel Feedback Queue, quantum=2
```

**Output includes:** PID, Arrival Time, Burst Time, Priority, Completion Time, Turnaround Time, Waiting Time, Response Time, and a text Gantt chart.

---

## Subsystem B — Memory Management

Simulate virtual memory address translation and page replacement.

```
moss> mem_algo FIFO                # set algorithm: FIFO, LRU, or OPTIMAL
moss> mem_run 1 2 3 2 4 1 3       # run a page reference string
moss> mem_stats                    # show hit/fault rate summary

moss> mem_config 4 256             # reconfigure: 4 frames, 256-byte pages
moss> mem_algo LRU
moss> access_memory 0x1AF3         # simulate a single memory access
```

**Output includes:** step-by-step trace of every access (HIT or FAULT), what page was evicted, and the current state of all frames.

---

## Subsystem C — Synchronization & Protection

Simulate mutex locks, semaphores, producer-consumer, and role-based access control.

**Mutex:**
```
moss> create_mutex printer_lock
moss> lock printer_lock 1          # P1 acquires lock
moss> lock printer_lock 2          # P2 blocks (lock held by P1)
moss> unlock printer_lock 1        # P1 releases, P2 gets it
```

**Semaphore:**
```
moss> create_semaphore slots 3     # counting semaphore, 3 permits
moss> sem_wait slots 1             # P1 acquires a permit
moss> sem_wait slots 2
moss> sem_signal slots 1           # P1 returns a permit
```

**Producer-Consumer:**
```
moss> setup_pc 5                   # bounded buffer, capacity=5
moss> produce 1 42                 # P1 produces item 42
moss> produce 1 99
moss> consume 2                    # P2 consumes one item
```

**Access Control:**
```
moss> add_user 1 admin             # roles: admin, user, guest
moss> add_user 2 user
moss> add_user 3 guest
moss> add_resource kernel_log admin admin   # resource: name, read_role, write_role
moss> add_resource user_file user user
moss> add_resource public_doc guest user
moss> check_access 1 kernel_log read       # admin  → GRANTED
moss> check_access 2 kernel_log read       # user   → DENIED
moss> check_access 3 public_doc read       # guest  → GRANTED
moss> show_sync_logs                        # print full event log
```

**Permission matrix:**
| Role | READ | WRITE |
|---|---|---|
| admin | ✓ all resources | ✓ all resources |
| user | ✓ user-level and below | ✓ user-level and below |
| guest | ✓ guest-level only | ✗ never |

---

## System Commands

```
moss> vertical_slice    # end-to-end demo through all three subsystems
moss> show_log          # full system event log for this session
moss> reset             # wipe all state and start fresh
moss> help              # full command reference
moss> exit              # quit
```

---

## Running the Tests

```bash
pip install pytest
python3 -m pytest test_sched.py test_mem.py test_sync.py -v
```

Expected output: **36 tests passed**.

To run a single subsystem's tests:
```bash
python3 -m pytest test_sched.py -v   # Subsystem A only
python3 -m pytest test_mem.py -v     # Subsystem B only
python3 -m pytest test_sync.py -v    # Subsystem C only
```

---

## Example Session

```
moss> create_process 1 0 5 2
moss> create_process 2 1 3 1
moss> schedule RR 2
moss> mem_algo LRU
moss> mem_run 1 2 3 2 4 1 3
moss> add_user 1 admin
moss> add_resource kernel_log admin admin
moss> check_access 1 kernel_log write
moss> show_log
moss> exit
```

---

## Project Structure

```
MOSS/
├── main.py          ← run this
├── cpu_sched.py
├── mem.py
├── sync.py
├── test_sched.py
├── test_mem.py
└── test_sync.py
```
