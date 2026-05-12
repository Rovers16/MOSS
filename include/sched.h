# =============================================================================
# sched.h  —  Subsystem A Interface: CPU Scheduling
# =============================================================================
# Public API (from cpu_sched.py):
#
#   Scheduler()
#   .sched_add_process(pid, arrival, burst, priority=0) -> int
#   .sched_load_from_list(list_of_dicts)                -> None
#   .sched_run(algorithm, quantum=2)                    -> dict
#   .sched_print_table(results)                         -> None
#   .sched_print_gantt()                                -> None
#
# Algorithms: FCFS | RR | PRIORITY | MLFQ
# Return codes: SUCCESS=0  ERR_INVALID=-1
# =============================================================================
