# =============================================================================
# test_sync.py  —  pytest tests for Subsystem C: Synchronization & Protection
# COSC 514 | MOSS Project
# =============================================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync import (Mutex, Semaphore, ProducerConsumer, AccessControl,
                  SyncManager, SUCCESS, ERR_LOCKED, ERR_DENIED,
                  ERR_NOT_OWNER, ERR_INVALID)


# ── Test 1: Mutex — first acquire succeeds ────────────────────────────────────
def test_mutex_acquire_free():
    m = Mutex("lock")
    assert m.acquire(1) == SUCCESS
    assert m.locked
    assert m.owner == 1


# ── Test 2: Mutex — second acquire blocks ────────────────────────────────────
def test_mutex_acquire_blocks():
    m = Mutex("lock")
    m.acquire(1)
    result = m.acquire(2)
    assert result == ERR_LOCKED
    assert 2 in m.waitqueue


# ── Test 3: Mutex — release hands to waiter ──────────────────────────────────
def test_mutex_release_hands_to_waiter():
    m = Mutex("lock")
    m.acquire(1)
    m.acquire(2)   # P2 blocked
    m.release(1)   # should hand to P2
    assert m.owner == 2
    assert m.locked is True


# ── Test 4: Mutex — non-owner cannot release ─────────────────────────────────
def test_mutex_non_owner_release():
    m = Mutex("lock")
    m.acquire(1)
    result = m.release(2)   # P2 doesn't own it
    assert result == ERR_NOT_OWNER


# ── Test 5: Mutex — release when no waiters frees lock ───────────────────────
def test_mutex_release_no_waiters():
    m = Mutex("lock")
    m.acquire(1)
    m.release(1)
    assert m.locked is False
    assert m.owner is None


# ── Test 6: Semaphore — wait decrements count ────────────────────────────────
def test_semaphore_wait_decrements():
    s = Semaphore("sem", 2)
    s.wait(1)
    assert s.count == 1
    s.wait(2)
    assert s.count == 0


# ── Test 7: Semaphore — wait blocks at zero ───────────────────────────────────
def test_semaphore_blocks_at_zero():
    s = Semaphore("sem", 1)
    s.wait(1)
    result = s.wait(2)
    assert result == ERR_LOCKED
    assert 2 in s.waitqueue


# ── Test 8: Semaphore — signal wakes waiter ───────────────────────────────────
def test_semaphore_signal_wakes():
    s = Semaphore("sem", 0)
    s.wait(1)   # P1 blocks (count=-1)
    s.signal(2)
    assert 1 not in s.waitqueue


# ── Test 9: Producer-Consumer — produce and consume ─────────────────────────
def test_producer_consumer():
    pc = ProducerConsumer(3)
    assert pc.produce(1, 10) == SUCCESS
    assert pc.produce(2, 20) == SUCCESS
    assert pc.consume(3) == SUCCESS
    assert len(pc.buffer) == 1


# ── Test 10: Producer-Consumer — blocks when full ────────────────────────────
def test_producer_consumer_full():
    pc = ProducerConsumer(2)
    pc.produce(1, 1)
    pc.produce(1, 2)
    result = pc.produce(1, 3)   # buffer full
    assert result == ERR_LOCKED


# ── Test 11: Producer-Consumer — blocks when empty ───────────────────────────
def test_producer_consumer_empty():
    pc = ProducerConsumer(3)
    result = pc.consume(1)   # nothing to consume
    assert result == ERR_LOCKED


# ── Test 12: AccessControl — admin gets everything ───────────────────────────
def test_access_control_admin():
    ac = AccessControl()
    ac.add_user(1, "admin")
    ac.add_resource("kernel", "admin", "admin")
    assert ac.check_access(1, "kernel", "read")  == SUCCESS
    assert ac.check_access(1, "kernel", "write") == SUCCESS


# ── Test 13: AccessControl — user denied admin resource ──────────────────────
def test_access_control_user_denied_admin():
    ac = AccessControl()
    ac.add_user(2, "user")
    ac.add_resource("kernel", "admin", "admin")
    assert ac.check_access(2, "kernel", "read")  == ERR_DENIED
    assert ac.check_access(2, "kernel", "write") == ERR_DENIED


# ── Test 14: AccessControl — guest read-only ─────────────────────────────────
def test_access_control_guest():
    ac = AccessControl()
    ac.add_user(3, "guest")
    ac.add_resource("doc", "guest", "user")
    assert ac.check_access(3, "doc", "read")  == SUCCESS
    assert ac.check_access(3, "doc", "write") == ERR_DENIED


# ── Test 15: AccessControl — unknown user denied ──────────────────────────────
def test_access_control_unknown_user():
    ac = AccessControl()
    ac.add_resource("file", "user", "user")
    assert ac.check_access(99, "file", "read") == ERR_DENIED


# ── Test 16: SyncManager public API ──────────────────────────────────────────
def test_sync_manager_api():
    sm = SyncManager()
    assert sm.sync_create_mutex("m1") == SUCCESS
    assert sm.sync_mutex_acquire("m1", 1) == SUCCESS
    assert sm.sync_mutex_acquire("m1", 2) == ERR_LOCKED
    assert sm.sync_mutex_release("m1", 1) == SUCCESS

    assert sm.sync_create_semaphore("s1", 2) == SUCCESS
    assert sm.sync_semaphore_wait("s1", 1)   == SUCCESS
    assert sm.sync_semaphore_signal("s1", 1) == SUCCESS

    assert sm.sync_setup_producer_consumer(4) == SUCCESS
    assert sm.sync_produce(1, 42) == SUCCESS
    assert sm.sync_consume(2)     == SUCCESS

    assert sm.sync_add_user(1, "admin") == SUCCESS
    assert sm.sync_add_resource("res", "user", "admin") == SUCCESS
    assert sm.sync_check_access(1, "res", "read") == SUCCESS


if __name__ == "__main__":
    print("\n" + "#"*55)
    print("  MOSS — Subsystem C: Synchronization Demo")
    print("#"*55)
    sm = SyncManager()
    sm.sync_create_mutex("printer")
    sm.sync_mutex_acquire("printer", 1)
    sm.sync_mutex_acquire("printer", 2)
    sm.sync_mutex_release("printer", 1)
    sm.sync_setup_producer_consumer(3)
    for i in range(3): sm.sync_produce(1, i*10)
    sm.sync_consume(2)
    sm.sync_add_user(1, "admin"); sm.sync_add_user(2, "user")
    sm.sync_add_resource("kernel_log", "admin", "admin")
    sm.sync_check_access(1, "kernel_log", "write")
    sm.sync_check_access(2, "kernel_log", "write")
    sm.sync_print_all_logs()
