# =============================================================================
# sched.py  —  Subsystem A: Process Management & CPU Scheduling
# COSC 514 | MOSS Project
# =============================================================================
# This module simulates CPU scheduling. It maintains Process Control Blocks
# (PCBs), manages a ready queue, and implements four scheduling algorithms:
#   - FCFS  (First-Come, First-Served)        — non-preemptive
#   - RR    (Round Robin)                     — preemptive
#   - PRIORITY                                — non-preemptive
#   - MLFQ  (Multilevel Feedback Queue)       — preemptive  [514 requirement]
#
# Direct Python port of the C reference code from OS-Lab-5-main.c,
# with Priority and MLFQ added for COSC 514.
# =============================================================================

from collections import deque   # deque = efficient queue (O(1) pop from front)
from typing import List


# -----------------------------------------------------------------------------
# CONSTANTS  (mirror the C code's return value conventions)
# -----------------------------------------------------------------------------

SUCCESS     =  0
ERR_INVALID = -1


# -----------------------------------------------------------------------------
# PCB — Process Control Block
# Mirrors the C struct PCB exactly, field for field.
# This is the OS's internal record for every process.
# -----------------------------------------------------------------------------

class PCB:

    def __init__(self, pid: int, arrival: int, burst: int, priority: int = 0):
        """
        pid      : unique process ID
        arrival  : time the process enters the ready queue
        burst    : total CPU time the process needs to finish
        priority : lower number = higher priority (used by PRIORITY + MLFQ)
        """
        # --- inputs (never change after creation) ---
        self.pid      = pid
        self.arrival  = arrival
        self.burst    = burst
        self.priority = priority

        # --- computed fields (reset before each algorithm run) ---
        self.remaining   = burst   # how much CPU time is still needed
        self.completion  = 0       # time the process finished
        self.turnaround  = 0       # completion - arrival  (total time in system)
        self.waiting     = 0       # turnaround - burst    (time spent waiting)
        self.response    = -1      # first CPU time - arrival  (-1 = not started)

        # --- flags used by Round Robin and MLFQ ---
        self.started  = False      # has this process received CPU time yet?
        self.enqueued = False      # is this process currently in a queue?

        # --- MLFQ state ---
        self.queue_level = 0       # which priority queue level this process is in


    def reset(self):
        """
        Reset all computed fields back to initial state.
        Called before running each scheduling algorithm so they don't
        interfere with each other — mirrors reset_fields() in the C code.
        """
        self.remaining   = self.burst
        self.completion  = 0
        self.turnaround  = 0
        self.waiting     = 0
        self.response    = -1
        self.started     = False
        self.enqueued    = False
        self.queue_level = 0


    def __repr__(self):
        return (f"PCB(pid={self.pid}, arrival={self.arrival}, "
                f"burst={self.burst}, priority={self.priority})")


# -----------------------------------------------------------------------------
# Scheduler class
# Owns the process list and runs scheduling algorithms on it.
# -----------------------------------------------------------------------------

class Scheduler:

    def __init__(self):
        """
        processes   : the list of all PCBs (loaded once, reused across algorithms)
        gantt_log   : records (pid, start_time, end_time) for Gantt chart output
        """
        self.processes: List[PCB] = []
        self.gantt_log: List[tuple] = []


    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def sched_add_process(self, pid: int, arrival: int, burst: int,
                          priority: int = 0) -> int:
        """
        Create a new PCB and add it to the process list.
        Returns SUCCESS or ERR_INVALID (if burst <= 0).
        """
        if burst <= 0:
            return ERR_INVALID
        self.processes.append(PCB(pid, arrival, burst, priority))
        return SUCCESS


    def sched_load_from_list(self, process_list: list) -> int:
        """
        Bulk-load processes from a list of dicts.
        Each dict must have: pid, arrival, burst
        Optional key: priority (defaults to 0)

        Example:
            [{"pid": 1, "arrival": 0, "burst": 5},
             {"pid": 2, "arrival": 1, "burst": 3, "priority": 1}]
        """
        self.processes = []
        for p in process_list:
            result = self.sched_add_process(
                pid      = p["pid"],
                arrival  = p["arrival"],
                burst    = p["burst"],
                priority = p.get("priority", 0)   # .get() = use 0 if key missing
            )
            if result != SUCCESS:
                return ERR_INVALID
        return SUCCESS


    def sched_run(self, algorithm: str, quantum: int = 2) -> dict:
        """
        Run a scheduling algorithm on the current process list.

        algorithm : "FCFS", "RR", "PRIORITY", or "MLFQ"
        quantum   : time slice for RR and MLFQ (ignored by FCFS and PRIORITY)

        Returns a results dict with per-process metrics and averages.
        """
        algorithm = algorithm.upper()

        if not self.processes:
            return {"error": "No processes loaded"}

        # reset all PCBs so each run is independent (mirrors reset_fields in C)
        for p in self.processes:
            p.reset()

        # sort by arrival time, then pid as tiebreaker
        # this mirrors qsort(p, n, sizeof(PCB), cmp_arrival) in the C code
        self.processes.sort(key=lambda p: (p.arrival, p.pid))

        self.gantt_log = []   # clear Gantt chart for this run

        # dispatch to the right algorithm
        if algorithm == "FCFS":
            self._fcfs()
        elif algorithm == "RR":
            self._rr(quantum)
        elif algorithm == "PRIORITY":
            self._priority()
        elif algorithm == "MLFQ":
            self._mlfq(quantum)
        else:
            return {"error": f"Unknown algorithm: {algorithm}"}

        return self._build_results(algorithm, quantum)


    def sched_print_table(self, results: dict):
        """
        Print a formatted results table.
        Mirrors print_table() in the C code.
        Columns: PID, AT (arrival), BT (burst), CT (completion),
                 TAT (turnaround), WT (waiting), RT (response)
        """
        algo = results["algorithm"]
        print(f"\n{'='*55}")
        print(f"  {algo}")
        print(f"{'='*55}")
        print(f"{'PID':<5} {'AT':<5} {'BT':<5} {'PRI':<5} {'CT':<5} {'TAT':<5} {'WT':<5} {'RT':<5}")
        print(f"{'-'*55}")

        for p in results["processes"]:
            print(f"{p['pid']:<5} {p['arrival']:<5} {p['burst']:<5} "
                  f"{p['priority']:<5} {p['completion']:<5} "
                  f"{p['turnaround']:<5} {p['waiting']:<5} {p['response']:<5}")

        print(f"{'-'*55}")
        print(f"  Avg TAT: {results['avg_turnaround']:.2f}   "
              f"Avg WT: {results['avg_waiting']:.2f}   "
              f"Avg RT: {results['avg_response']:.2f}")
        print(f"{'='*55}\n")


    def sched_print_gantt(self):
        """
        Print a text-based Gantt chart from gantt_log.
        Each entry in gantt_log is (pid, start, end).
        Mirrors the Gantt output in the C RR function.
        """
        if not self.gantt_log:
            print("  (No Gantt data)\n")
            return

        print("\n  Gantt Chart:")
        bar   = ""
        times = ""

        for (pid, start, end) in self.gantt_log:
            width = max((end - start) * 3, 4)   # scale width by duration
            bar   += f"| P{pid} ".ljust(width)
            times += str(start).ljust(width)

        bar   += "|"
        times += str(self.gantt_log[-1][2])   # append final end time

        print(f"  {bar}")
        print(f"  {times}")
        print()


    # =========================================================================
    # SCHEDULING ALGORITHMS  (private — not part of the public API)
    # =========================================================================

    def _fcfs(self):
        """
        First-Come, First-Served — Non-preemptive.

        Direct Python port of fcfs() in the C code.
        Processes are already sorted by arrival time.
        Each process runs to completion before the next starts.

        Timeline logic:
          t starts at 0.
          If CPU is idle (t < arrival), jump t forward to arrival.
          Record response time (first time on CPU = t - arrival).
          Run entire burst: t += burst.
          Compute CT, TAT, WT.
        """
        t = 0   # current time — mirrors 'int t = 0' in C

        for p in self.processes:

            # if CPU is idle between processes, jump forward in time
            # e.g. process arrives at t=5 but CPU finished last job at t=3
            if t < p.arrival:
                t = p.arrival

            # response time = moment first CPU access - arrival time
            # for FCFS this equals waiting time since no preemption
            p.response = t - p.arrival

            self.gantt_log.append((p.pid, t, t + p.burst))

            # run the entire burst (non-preemptive — no interruptions)
            t += p.burst

            # compute final metrics
            p.completion = t
            p.turnaround = t - p.arrival          # total time in system
            p.waiting    = p.turnaround - p.burst  # time spent waiting (not on CPU)


    def _rr(self, quantum: int):
        """
        Round Robin — Preemptive.

        Direct Python port of rr() in the C code.
        Each process gets at most 'quantum' time units per turn.
        If not finished, it goes to the back of the queue.

        Key insight: processes are added to the queue as they ARRIVE,
        not all at once. So we check for new arrivals after every tick.
        """
        q        = deque()    # ready queue — mirrors Queue in C
        t        = 0          # current time
        finished = 0          # number of completed processes
        n        = len(self.processes)

        # enqueue all processes that have already arrived at t=0
        self._enqueue_arrivals(q, t)

        while finished < n:

            # if no process is ready, advance time and check for arrivals
            # mirrors the 'if (q_empty(&q))' block in C
            if not q:
                t += 1
                self._enqueue_arrivals(q, t)
                continue

            p = q.popleft()   # get next process — mirrors q_pop in C

            # first time this process touches the CPU → record response time
            if not p.started:
                p.response = t - p.arrival
                p.started  = True

            # run for either the quantum OR however much is left
            # mirrors: int run = (p[i].remaining < qtime) ? p[i].remaining : qtime
            run = min(p.remaining, quantum)

            self.gantt_log.append((p.pid, t, t + run))

            p.remaining -= run
            t           += run

            # check for new arrivals AFTER running this slice
            self._enqueue_arrivals(q, t)

            if p.remaining > 0:
                # process not done → put it at the BACK of the queue
                q.append(p)
            else:
                # process finished
                p.completion = t
                p.turnaround = t - p.arrival
                p.waiting    = p.turnaround - p.burst
                finished    += 1


    def _priority(self):
        """
        Priority Scheduling — Non-preemptive.
        Lower priority number = higher priority (e.g. priority 0 runs before priority 2).

        At each scheduling decision point, pick the highest-priority process
        among ALL processes that have arrived by the current time.

        This is the COSC 514 addition over the C lab code.
        """
        t        = 0
        finished = 0
        n        = len(self.processes)
        done     = [False] * n   # track which processes have completed

        while finished < n:

            # find all processes that have arrived and are not done
            ready = [
                (i, p) for i, p in enumerate(self.processes)
                if p.arrival <= t and not done[i]
            ]

            if not ready:
                # no process ready — advance time to the next arrival
                next_arrival = min(
                    p.arrival for i, p in enumerate(self.processes) if not done[i]
                )
                t = next_arrival
                continue

            # pick the process with the LOWEST priority number (= highest priority)
            # tiebreak by arrival time, then pid
            idx, p = min(ready, key=lambda x: (x[1].priority, x[1].arrival, x[1].pid))

            # first time on CPU
            p.response = t - p.arrival

            self.gantt_log.append((p.pid, t, t + p.burst))

            # run to completion (non-preemptive)
            t            += p.burst
            p.completion  = t
            p.turnaround  = t - p.arrival
            p.waiting     = p.turnaround - p.burst

            done[idx]  = True
            finished  += 1


    def _mlfq(self, base_quantum: int):
        """
        Multilevel Feedback Queue — Preemptive.
        COSC 514 requirement.

        Structure: 3 priority queues.
          Queue 0 (highest priority): quantum = base_quantum       e.g. 2
          Queue 1 (medium priority) : quantum = base_quantum * 2   e.g. 4
          Queue 2 (lowest priority) : quantum = base_quantum * 4   e.g. 8 (FCFS-like)

        Rules:
          1. New processes always enter Queue 0.
          2. If a process uses its FULL quantum without finishing → demote to next queue.
          3. If a process finishes before quantum expires → stays at same level (reward).
          4. Higher queue levels always preempt lower ones.
             i.e. if a new process arrives in Q0 while Q1 is running → Q0 runs next.

        Why MLFQ?
          It automatically adapts: short CPU-burst processes (interactive) stay in Q0
          and get fast response. Long CPU-burst processes (batch jobs) sink to Q2
          and run with large quanta — less overhead, but lower priority.
        """
        # three queues — index = priority level (0 = highest)
        queues   = [deque(), deque(), deque()]
        quanta   = [base_quantum, base_quantum * 2, base_quantum * 4]

        t        = 0
        finished = 0
        n        = len(self.processes)

        # all processes start in Queue 0 as they arrive
        self._enqueue_arrivals_mlfq(queues[0], t)

        while finished < n:

            # find the highest-priority non-empty queue
            current_queue = None
            for level in range(3):
                if queues[level]:
                    current_queue = level
                    break

            # no process ready — advance time
            if current_queue is None:
                t += 1
                self._enqueue_arrivals_mlfq(queues[0], t)
                continue

            p       = queues[current_queue].popleft()
            quantum = quanta[current_queue]

            # first time on CPU → record response time
            if not p.started:
                p.response = t - p.arrival
                p.started  = True

            # run for quantum or remaining time, whichever is less
            run = min(p.remaining, quantum)

            self.gantt_log.append((p.pid, t, t + run))

            p.remaining -= run
            t           += run

            # check for new arrivals after this slice
            self._enqueue_arrivals_mlfq(queues[0], t)

            if p.remaining > 0:
                # process didn't finish — demote to next queue (max level 2)
                next_level       = min(current_queue + 1, 2)
                p.queue_level    = next_level
                queues[next_level].append(p)
            else:
                # process finished
                p.completion = t
                p.turnaround = t - p.arrival
                p.waiting    = p.turnaround - p.burst
                finished    += 1


    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _enqueue_arrivals(self, q: deque, t: int):
        """
        Add to queue any process that has arrived by time t and isn't queued yet.
        Mirrors enqueue_arrivals() in the C code exactly.
        """
        for p in self.processes:
            if not p.enqueued and p.arrival <= t:
                q.append(p)
                p.enqueued = True


    def _enqueue_arrivals_mlfq(self, q0: deque, t: int):
        """
        MLFQ version: new arrivals always go into Queue 0 (highest priority).
        """
        for p in self.processes:
            if not p.enqueued and p.arrival <= t:
                q0.append(p)
                p.enqueued   = True
                p.queue_level = 0


    def _build_results(self, algorithm: str, quantum: int) -> dict:
        """
        Collect per-process metrics and compute averages.
        Returns a structured dict used by sched_print_table().
        """
        proc_data = []
        for p in self.processes:
            proc_data.append({
                "pid"        : p.pid,
                "arrival"    : p.arrival,
                "burst"      : p.burst,
                "priority"   : p.priority,
                "completion" : p.completion,
                "turnaround" : p.turnaround,
                "waiting"    : p.waiting,
                "response"   : p.response
            })

        n           = len(self.processes)
        avg_tat     = sum(p["turnaround"] for p in proc_data) / n
        avg_wt      = sum(p["waiting"]    for p in proc_data) / n
        avg_rt      = sum(p["response"]   for p in proc_data) / n

        return {
            "algorithm"      : f"{algorithm}" + (f" (q={quantum})" if algorithm in ("RR","MLFQ") else ""),
            "processes"      : proc_data,
            "avg_turnaround" : round(avg_tat, 2),
            "avg_waiting"    : round(avg_wt,  2),
            "avg_response"   : round(avg_rt,  2)
        }
