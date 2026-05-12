# =============================================================================
# sync.py  —  Subsystem C: Synchronization & Protection
# COSC 514 | MOSS Project
# =============================================================================
# This module simulates OS synchronization primitives and access control.
# It implements:
#   - Mutex locks        (binary semaphore, mutual exclusion)
#   - Counting semaphores
#   - Producer-Consumer  (classical sync problem)
#   - Readers-Writers    (classical sync problem)
#   - Access control     (user roles + permission checks)
#
# NOTE: This is a LOGICAL simulation — no real threads or OS calls.
# Concurrency is modeled by stepping through interleaved operations
# one at a time, exactly as a professor would trace on a whiteboard.
# =============================================================================

from collections import deque
from typing import List, Dict, Optional


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

SUCCESS        =  0
ERR_LOCKED     = -1   # resource is already locked
ERR_DENIED     = -2   # access control: permission denied
ERR_NOT_OWNER  = -3   # process trying to unlock a mutex it doesn't own
ERR_INVALID    = -4   # bad input


# -----------------------------------------------------------------------------
# Mutex
# A mutex (mutual exclusion lock) allows only ONE process to hold it at a time.
# Any other process that tries to lock it will BLOCK and join a waiting queue.
#
# Real OS analogy: pthread_mutex_lock / pthread_mutex_unlock
# -----------------------------------------------------------------------------

class Mutex:

    def __init__(self, name: str):
        """
        name     : human-readable label (e.g. "printer_lock")
        locked   : True if currently held by someone
        owner    : pid of the process holding the lock (None if free)
        waitqueue: processes blocked waiting for this mutex
        log      : every lock/unlock event recorded here
        """
        self.name      = name
        self.locked    = False
        self.owner     = None
        self.waitqueue = deque()
        self.log: List[str] = []


    def acquire(self, pid: int) -> int:
        """
        Process 'pid' tries to acquire (lock) this mutex.

        If FREE   → process gets the lock immediately. Returns SUCCESS.
        If LOCKED → process is added to the wait queue. Returns ERR_LOCKED.

        This models what happens when a thread calls pthread_mutex_lock()
        and the mutex is already held — the thread blocks in the kernel.
        """
        if not self.locked:
            # mutex is free — grant it
            self.locked = True
            self.owner  = pid
            self.log.append(f"  t+{len(self.log):02d}  P{pid} ACQUIRED '{self.name}'")
            return SUCCESS
        else:
            # mutex is held — block the caller
            self.waitqueue.append(pid)
            self.log.append(f"  t+{len(self.log):02d}  P{pid} BLOCKED  on '{self.name}' (owner: P{self.owner})")
            return ERR_LOCKED


    def release(self, pid: int) -> int:
        """
        Process 'pid' releases (unlocks) this mutex.

        Only the OWNER can release it — otherwise ERR_NOT_OWNER.
        If there are waiting processes, the first one in line gets the lock.

        This models pthread_mutex_unlock() — the kernel wakes the next waiter.
        """
        if self.owner != pid:
            self.log.append(f"  t+{len(self.log):02d}  P{pid} FAILED release '{self.name}' (not owner)")
            return ERR_NOT_OWNER

        if self.waitqueue:
            # hand the lock to the next waiting process
            next_pid    = self.waitqueue.popleft()
            self.owner  = next_pid
            self.locked = True
            self.log.append(f"  t+{len(self.log):02d}  P{pid} RELEASED '{self.name}' → handed to P{next_pid}")
        else:
            # no one waiting — just free the lock
            self.locked = False
            self.owner  = None
            self.log.append(f"  t+{len(self.log):02d}  P{pid} RELEASED '{self.name}' (now free)")

        return SUCCESS


    def print_log(self):
        print(f"\n  Mutex '{self.name}' event log:")
        for entry in self.log:
            print(entry)


# -----------------------------------------------------------------------------
# Semaphore
# A semaphore holds an INTEGER count, not just 0/1 like a mutex.
# Used to control access to a pool of N identical resources.
#
# wait()   (P operation): decrement count. If count < 0 → block.
# signal() (V operation): increment count. If there are waiters → wake one.
#
# Binary semaphore (N=1) behaves like a mutex.
# Counting semaphore (N>1) models a resource pool (e.g. 3 printers).
# -----------------------------------------------------------------------------

class Semaphore:

    def __init__(self, name: str, initial_value: int):
        """
        initial_value : number of resources available (e.g. 3 for 3 printers)
        count         : current value (can go negative — |negative| = # waiting)
        """
        self.name      = name
        self.count     = initial_value
        self.waitqueue = deque()
        self.log: List[str] = []


    def wait(self, pid: int) -> int:
        """
        P operation (proberen = "to test" in Dutch — Dijkstra's original term).
        Decrement count. If count goes negative → process blocks.

        count >= 0 after decrement → resource was available → SUCCESS
        count <  0 after decrement → no resource → ERR_LOCKED (blocked)
        """
        self.count -= 1
        if self.count >= 0:
            self.log.append(f"  t+{len(self.log):02d}  P{pid} WAIT '{self.name}' → count={self.count} (acquired)")
            return SUCCESS
        else:
            self.waitqueue.append(pid)
            self.log.append(f"  t+{len(self.log):02d}  P{pid} WAIT '{self.name}' → count={self.count} (BLOCKED)")
            return ERR_LOCKED


    def signal(self, pid: int) -> int:
        """
        V operation (verhogen = "to increment").
        Increment count. If there are blocked processes → wake the first one.
        """
        self.count += 1
        if self.waitqueue:
            woken = self.waitqueue.popleft()
            self.log.append(f"  t+{len(self.log):02d}  P{pid} SIGNAL '{self.name}' → count={self.count} (woke P{woken})")
        else:
            self.log.append(f"  t+{len(self.log):02d}  P{pid} SIGNAL '{self.name}' → count={self.count}")
        return SUCCESS


    def print_log(self):
        print(f"\n  Semaphore '{self.name}' event log:")
        for entry in self.log:
            print(entry)


# -----------------------------------------------------------------------------
# ProducerConsumer
# Classical synchronization problem.
#
# Setup:
#   - A shared BUFFER of fixed size N.
#   - PRODUCERS add items to the buffer.
#   - CONSUMERS remove items from the buffer.
#
# Problem without sync:
#   - Producer adds to a full buffer  → overflow (data lost or crash)
#   - Consumer removes from empty buffer → underflow (garbage data)
#   - Both access buffer simultaneously → race condition (corrupt data)
#
# Solution with semaphores:
#   - 'empty' semaphore: counts empty slots  (starts at N)
#   - 'full'  semaphore: counts filled slots (starts at 0)
#   - 'mutex' semaphore: protects buffer access (binary, starts at 1)
#
# Producer protocol:  wait(empty) → wait(mutex) → ADD → signal(mutex) → signal(full)
# Consumer protocol:  wait(full)  → wait(mutex) → REMOVE → signal(mutex) → signal(empty)
# -----------------------------------------------------------------------------

class ProducerConsumer:

    def __init__(self, buffer_size: int):
        self.buffer_size = buffer_size
        self.buffer      = []           # the shared buffer
        self.log: List[str] = []

        # three semaphores that coordinate access
        self.empty = Semaphore("empty", buffer_size)  # empty slots available
        self.full  = Semaphore("full",  0)             # filled slots available
        self.mutex = Semaphore("mutex", 1)             # mutual exclusion lock


    def produce(self, pid: int, item: int) -> int:
        """
        Producer tries to add 'item' to the buffer.

        Step 1: wait(empty)  — is there an empty slot?   block if buffer full
        Step 2: wait(mutex)  — get exclusive buffer access
        Step 3: add item     — critical section
        Step 4: signal(mutex)— release buffer access
        Step 5: signal(full) — notify a waiting consumer that an item is ready
        """
        self.log.append(f"\n  [PRODUCER P{pid}] wants to add item={item}")

        # step 1: wait for an empty slot
        r = self.empty.wait(pid)
        if r != SUCCESS:
            self.log.append(f"  [PRODUCER P{pid}] BLOCKED — buffer full ({len(self.buffer)}/{self.buffer_size})")
            return ERR_LOCKED

        # step 2: lock the buffer
        self.mutex.wait(pid)

        # step 3: critical section — add the item
        self.buffer.append(item)
        self.log.append(f"  [PRODUCER P{pid}] added item={item} | buffer={self.buffer}")

        # step 4: unlock the buffer
        self.mutex.signal(pid)

        # step 5: signal that one more slot is now full
        self.full.signal(pid)

        return SUCCESS


    def consume(self, pid: int) -> int:
        """
        Consumer tries to remove an item from the buffer.

        Step 1: wait(full)   — is there an item to consume?  block if buffer empty
        Step 2: wait(mutex)  — get exclusive buffer access
        Step 3: remove item  — critical section
        Step 4: signal(mutex)— release buffer access
        Step 5: signal(empty)— notify a waiting producer that a slot is free
        """
        self.log.append(f"\n  [CONSUMER P{pid}] wants to consume")

        # step 1: wait for a filled slot
        r = self.full.wait(pid)
        if r != SUCCESS:
            self.log.append(f"  [CONSUMER P{pid}] BLOCKED — buffer empty")
            return ERR_LOCKED

        # step 2: lock the buffer
        self.mutex.wait(pid)

        # step 3: critical section — remove the item
        item = self.buffer.pop(0)
        self.log.append(f"  [CONSUMER P{pid}] removed item={item} | buffer={self.buffer}")

        # step 4: unlock the buffer
        self.mutex.signal(pid)

        # step 5: signal that one more slot is now empty
        self.empty.signal(pid)

        return SUCCESS


    def print_log(self):
        print(f"\n  Producer-Consumer Log (buffer_size={self.buffer_size}):")
        for entry in self.log:
            print(entry)


# -----------------------------------------------------------------------------
# AccessControl
# Basic protection model: users have roles, resources have permissions.
#
# Roles:    admin > user > guest
# Resources can allow specific roles to READ or WRITE.
#
# This models OS protection rings / access control lists (ACLs).
# -----------------------------------------------------------------------------

ROLE_HIERARCHY = {"admin": 3, "user": 2, "guest": 1}   # higher = more privilege

class AccessControl:

    def __init__(self):
        """
        users     : maps pid → role  (e.g. {1: "admin", 2: "user"})
        resources : maps resource_name → {read: min_role, write: min_role}
        log       : every access attempt recorded
        """
        self.users: Dict[int, str]     = {}
        self.resources: Dict[str, dict] = {}
        self.log: List[str]            = []


    def add_user(self, pid: int, role: str) -> int:
        if role not in ROLE_HIERARCHY:
            return ERR_INVALID
        self.users[pid] = role
        return SUCCESS


    def add_resource(self, name: str, read_role: str, write_role: str) -> int:
        """
        Define a resource and the MINIMUM role needed to read/write it.
        e.g. add_resource("kernel_log", "admin", "admin")
             add_resource("user_file",  "user",  "user")
             add_resource("public_doc", "guest", "user")
        """
        if read_role not in ROLE_HIERARCHY or write_role not in ROLE_HIERARCHY:
            return ERR_INVALID
        self.resources[name] = {"read": read_role, "write": write_role}
        return SUCCESS


    def check_access(self, pid: int, resource: str, mode: str) -> int:
        """
        Check if process 'pid' can access 'resource' in 'mode' (read/write).

        Logic:
          1. Look up the user's role.
          2. Look up the resource's required minimum role for this mode.
          3. Compare privilege levels using ROLE_HIERARCHY.
          4. Grant if user's level >= required level, deny otherwise.
        """
        if pid not in self.users:
            self.log.append(f"  P{pid} → '{resource}' [{mode}]: DENIED (unknown user)")
            return ERR_DENIED

        if resource not in self.resources:
            self.log.append(f"  P{pid} → '{resource}' [{mode}]: DENIED (unknown resource)")
            return ERR_DENIED

        user_role     = self.users[pid]
        required_role = self.resources[resource][mode]

        user_level     = ROLE_HIERARCHY[user_role]
        required_level = ROLE_HIERARCHY[required_role]

        if user_level >= required_level:
            self.log.append(f"  P{pid} ({user_role}) → '{resource}' [{mode}]: GRANTED")
            return SUCCESS
        else:
            self.log.append(f"  P{pid} ({user_role}) → '{resource}' [{mode}]: DENIED (need '{required_role}')")
            return ERR_DENIED


    def print_log(self):
        print("\n  Access Control Log:")
        for entry in self.log:
            print(entry)


# -----------------------------------------------------------------------------
# SyncManager — public API wrapper
# Other subsystems call these functions, never the classes directly.
# -----------------------------------------------------------------------------

class SyncManager:

    def __init__(self):
        self.mutexes:    Dict[str, Mutex]         = {}
        self.semaphores: Dict[str, Semaphore]     = {}
        self.access_control                       = AccessControl()
        self.producer_consumer: Optional[ProducerConsumer] = None


    def sync_create_mutex(self, name: str) -> int:
        self.mutexes[name] = Mutex(name)
        return SUCCESS


    def sync_mutex_acquire(self, name: str, pid: int) -> int:
        if name not in self.mutexes:
            return ERR_INVALID
        return self.mutexes[name].acquire(pid)


    def sync_mutex_release(self, name: str, pid: int) -> int:
        if name not in self.mutexes:
            return ERR_INVALID
        return self.mutexes[name].release(pid)


    def sync_create_semaphore(self, name: str, value: int) -> int:
        self.semaphores[name] = Semaphore(name, value)
        return SUCCESS


    def sync_semaphore_wait(self, name: str, pid: int) -> int:
        if name not in self.semaphores:
            return ERR_INVALID
        return self.semaphores[name].wait(pid)


    def sync_semaphore_signal(self, name: str, pid: int) -> int:
        if name not in self.semaphores:
            return ERR_INVALID
        return self.semaphores[name].signal(pid)


    def sync_setup_producer_consumer(self, buffer_size: int) -> int:
        self.producer_consumer = ProducerConsumer(buffer_size)
        return SUCCESS


    def sync_produce(self, pid: int, item: int) -> int:
        if not self.producer_consumer:
            return ERR_INVALID
        return self.producer_consumer.produce(pid, item)


    def sync_consume(self, pid: int) -> int:
        if not self.producer_consumer:
            return ERR_INVALID
        return self.producer_consumer.consume(pid)


    def sync_add_user(self, pid: int, role: str) -> int:
        return self.access_control.add_user(pid, role)


    def sync_add_resource(self, name: str, read_role: str, write_role: str) -> int:
        return self.access_control.add_resource(name, read_role, write_role)


    def sync_check_access(self, pid: int, resource: str, mode: str) -> int:
        return self.access_control.check_access(pid, resource, mode)


    def sync_print_all_logs(self):
        for m in self.mutexes.values():
            m.print_log()
        for s in self.semaphores.values():
            s.print_log()
        if self.producer_consumer:
            self.producer_consumer.print_log()
        self.access_control.print_log()
