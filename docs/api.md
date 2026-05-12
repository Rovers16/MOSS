# MOSS API Reference

## Subsystem A — CPU Scheduling (`src/sched/cpu_sched.py`)

### `Scheduler`
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `sched_add_process` | pid, arrival, burst, priority=0 | 0 or -1 | Add one process |
| `sched_load_from_list` | list of dicts | None | Bulk load processes |
| `sched_run` | algorithm, quantum=2 | dict | Run scheduling algorithm |
| `sched_print_table` | results dict | None | Print results table |
| `sched_print_gantt` | — | None | Print Gantt chart |

**Algorithms:** `FCFS` `RR` `PRIORITY` `MLFQ`

---

## Subsystem B — Memory Management (`src/mem/mem.py`)

### `MemoryManager(num_frames, page_size)`
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `mem_set_algorithm` | algo string | 0 or -1 | Set replacement algorithm |
| `mem_access` | address, reference_string, future_index | 0 or -1 | Single page access |
| `mem_run_reference_string` | list of page numbers | None | Run full reference string |
| `mem_reset` | — | None | Clear all state |
| `mem_get_stats` | — | dict | Get hit/fault statistics |
| `mem_print_trace` | — | None | Print step-by-step trace |

**Algorithms:** `FIFO` `LRU` `OPTIMAL`

---

## Subsystem C — Synchronization & Protection (`src/sync/sync.py`)

### `SyncManager`
| Method | Parameters | Returns | Description |
|---|---|---|---|
| `sync_create_mutex` | name | 0 | Create named mutex |
| `sync_mutex_acquire` | name, pid | 0 or -1 | Acquire mutex |
| `sync_mutex_release` | name, pid | 0 or -3 | Release mutex |
| `sync_create_semaphore` | name, value | 0 | Create semaphore |
| `sync_semaphore_wait` | name, pid | 0 or -1 | P operation |
| `sync_semaphore_signal` | name, pid | 0 | V operation |
| `sync_setup_producer_consumer` | buffer_size | 0 | Init bounded buffer |
| `sync_produce` | pid, item | 0 or -1 | Add item to buffer |
| `sync_consume` | pid | 0 or -1 | Remove item from buffer |
| `sync_add_user` | pid, role | 0 or -4 | Register user with role |
| `sync_add_resource` | name, read_role, write_role | 0 or -4 | Register resource |
| `sync_check_access` | pid, resource, mode | 0 or -2 | Check permission |
| `sync_print_all_logs` | — | None | Print all event logs |

**Roles:** `admin` `user` `guest`

**Return codes:** `SUCCESS=0` `ERR_LOCKED=-1` `ERR_DENIED=-2` `ERR_NOT_OWNER=-3` `ERR_INVALID=-4`
