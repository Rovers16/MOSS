# MOSS Subsystem C — Synchronization & Protection

Part I of the Mini OS Services Simulator group project.  
Language: C++17 | Threading: POSIX pthreads

---

## What's Included

| Component | Files | Description |
|---|---|---|
| Mutex | `mutex.h / mutex.cpp` | pthread_mutex_t wrapper with lock/unlock + RAII guard |
| Semaphore | `semaphore.h / semaphore.cpp` | Counting semaphore via pthread_mutex + pthread_cond |
| Bounded Buffer | `bounded_buffer.h / bounded_buffer.cpp` | Circular buffer using 3-semaphore classic pattern |
| Producer-Consumer | `producer_consumer.cpp` | Multi-thread demo using BoundedBuffer |
| Access Control | `access_control.h / access_control.cpp` | RBAC: ADMIN/USER/GUEST × READ/WRITE/EXECUTE |
| Race Demo | `race_demo.cpp` | Reproduces Lab 4 behavior: unsync vs mutex |
| Main / API | `main.cpp` | Driver + Part II integration API |

---

## Build & Run

```bash
# Build
make

# Run all three demos
make demo

# Clean
make clean
```

Manual compile:
```bash
g++ -Wall -O2 -pthread -std=c++17 src/*.cpp -Iinclude -o moss_sync
./moss_sync
```

---

## Demo Output

**Demo 1 — Race Condition (Lab 4 reference)**
- Unsynchronized: 3 threads × 10,000,000 increments → lost updates (< 30,000,000)
- With Mutex: always exactly 30,000,000

**Demo 2 — Producer-Consumer**
- 2 producers × 6 items into a buffer of capacity 5
- 2 consumers drain the buffer
- Each event printed with thread ID, item name, and buffer state

**Demo 3 — Access Control**
- ADMIN root → READ/WRITE/EXECUTE all granted
- USER alice → READ/WRITE granted, EXECUTE denied
- GUEST guest1 → READ granted, WRITE/EXECUTE denied

---

## Part II Integration API

Include the headers and call via the `moss::sync` namespace:

```cpp
#include "moss/sync/mutex.h"
#include "moss/sync/semaphore.h"
#include "moss/sync/access_control.h"
#include "moss/sync/role.h"
#include "moss/sync/permission.h"

// Get or create a named mutex
moss::sync::Mutex* m = moss::sync::get_mutex("my_lock");

// Get or create a named semaphore with 3 permits
moss::sync::Semaphore* s = moss::sync::get_semaphore("my_sem", 3);

// Check access (also logs result)
bool ok = moss::sync::check_access("alice", moss::sync::Role::USER,
                                    moss::sync::Permission::WRITE, "FileX");
```

---

## Synchronization Decisions

- **Semaphore** uses `pthread_cond_wait` in a `while` loop (not `if`) to guard against spurious wakeups.
- **BoundedBuffer** uses three synchronization objects: `empty_slots` semaphore (producer blocks when full), `filled_slots` semaphore (consumer blocks when empty), and `buf_mutex` for exclusive access to head/tail/data.
- **AccessControl** serializes log output with an internal mutex so concurrent permission checks never produce interleaved console lines.
- **MutexGuard** (RAII) is used wherever possible to prevent unlock-on-exception bugs.
