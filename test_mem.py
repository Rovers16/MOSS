# =============================================================================
# test_mem.py  —  pytest tests for Subsystem B: Memory Management
# COSC 514 | MOSS Project
# =============================================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mem import MemoryManager, SUCCESS, ERR_FAULT, ERR_INVALID

REF = [1, 2, 3, 2, 4, 1, 3]   # Lab 6 reference string, 3 frames


def make_mm(algo="FIFO", frames=3):
    mm = MemoryManager(num_frames=frames, page_size=256)
    mm.mem_set_algorithm(algo)
    return mm


# ── Test 1: FIFO fault count matches expected ─────────────────────────────────
def test_fifo_fault_count():
    mm = make_mm("FIFO")
    mm.mem_run_reference_string(REF)
    stats = mm.mem_get_stats()
    # [1,2,3,2✓,4(evict1),1(evict2),3(evict3)] → 6 faults, 1 hit
    assert stats["page_faults"] == 5
    assert stats["page_hits"]   == 2


# ── Test 2: LRU fault count matches expected ──────────────────────────────────
def test_lru_fault_count():
    mm = make_mm("LRU")
    mm.mem_run_reference_string(REF)
    stats = mm.mem_get_stats()
    assert stats["page_faults"] == 6
    assert stats["page_hits"]   == 1


# ── Test 3: Optimal has fewest faults ────────────────────────────────────────
def test_optimal_fewest_faults():
    fifo = make_mm("FIFO"); fifo.mem_run_reference_string(REF)
    lru  = make_mm("LRU");  lru.mem_run_reference_string(REF)
    opt  = make_mm("OPTIMAL"); opt.mem_run_reference_string(REF)
    assert opt.mem_get_stats()["page_faults"] <= fifo.mem_get_stats()["page_faults"]
    assert opt.mem_get_stats()["page_faults"] <= lru.mem_get_stats()["page_faults"]


# ── Test 4: Page hit returns SUCCESS ─────────────────────────────────────────
def test_page_hit_returns_success():
    mm = make_mm("FIFO")
    mm.mem_run_reference_string([1, 2, 3])
    # access page 1 again — should be a hit
    result = mm.mem_access(1 * 256, reference_string=[1,2,3,1], future_index=3)
    assert result == SUCCESS


# ── Test 5: Page fault returns ERR_FAULT ────────────────────────────────────
def test_page_fault_returns_err_fault():
    mm = make_mm("FIFO")
    result = mm.mem_access(0)   # first access → always a fault
    assert result == ERR_FAULT


# ── Test 6: Invalid address returns ERR_INVALID ──────────────────────────────
def test_invalid_address():
    mm = make_mm("FIFO")
    result = mm.mem_access(-1)
    assert result == ERR_INVALID
    result2 = mm.mem_access(2**16)   # one beyond 16-bit max
    assert result2 == ERR_INVALID


# ── Test 7: mem_reset clears state ───────────────────────────────────────────
def test_mem_reset_clears_state():
    mm = make_mm("FIFO")
    mm.mem_run_reference_string([1, 2, 3])
    mm.mem_reset()
    assert mm.page_faults  == 0
    assert mm.page_hits    == 0
    assert mm.total_access == 0
    assert all(f is None for f in mm.frames)


# ── Test 8: More frames reduces faults (FIFO) ────────────────────────────────
def test_more_frames_generally_reduces_faults():
    ref = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    f2 = make_mm("LRU", 2); f2.mem_run_reference_string(ref)
    f5 = make_mm("LRU", 5); f5.mem_run_reference_string(ref)
    assert f5.mem_get_stats()["page_faults"] <= f2.mem_get_stats()["page_faults"]


# ── Test 9: Fault rate calculation correct ────────────────────────────────────
def test_fault_rate_calculation():
    mm = make_mm("FIFO")
    mm.mem_run_reference_string(REF)
    stats = mm.mem_get_stats()
    expected = round(5/7*100, 2)
    assert abs(stats["fault_rate"] - expected) < 0.01


# ── Test 10: Algorithm switch works between runs ──────────────────────────────
def test_algorithm_switch():
    mm = make_mm("FIFO")
    mm.mem_run_reference_string(REF)
    fifo_faults = mm.mem_get_stats()["page_faults"]
    mm.mem_set_algorithm("LRU")
    mm.mem_run_reference_string(REF)
    assert mm.mem_get_stats()["algorithm"] == "LRU"


# ── Manual experiment runner ──────────────────────────────────────────────────
def run_experiments():
    print("\n" + "="*65)
    print("  EXPERIMENT 1 — Lab 6 Reference String  [1,2,3,2,4,1,3]  3 frames")
    print("="*65)
    for algo in ["FIFO", "LRU", "OPTIMAL"]:
        mm = make_mm(algo); mm.mem_run_reference_string(REF); mm.mem_print_trace()

    print("\n" + "="*65)
    print("  EXPERIMENT 2 — Frame size vs fault rate (LRU)")
    print("="*65)
    ref2 = [1,2,3,4,1,2,5,1,2,3,4,5]
    print(f"  {'Frames':<8}{'Faults'}")
    for f in range(1,7):
        mm=make_mm("LRU",f); mm.mem_run_reference_string(ref2)
        print(f"  {f:<8}{mm.mem_get_stats()['page_faults']}")

    print("\n" + "="*65)
    print("  EXPERIMENT 3 — Belady's Anomaly")
    print("="*65)
    print(f"  {'Algo':<10}{'3F':<8}{'4F':<8}{'Anomaly?'}")
    for algo in ["FIFO","LRU","OPTIMAL"]:
        mm3=make_mm(algo,3); mm3.mem_run_reference_string(ref2)
        mm4=make_mm(algo,4); mm4.mem_run_reference_string(ref2)
        f3=mm3.mem_get_stats()["page_faults"]; f4=mm4.mem_get_stats()["page_faults"]
        print(f"  {algo:<10}{f3:<8}{f4:<8}{'YES ← Beladys!' if f4>f3 else 'No'}")


if __name__ == "__main__":
    print("\n" + "#"*65)
    print("  MOSS — Subsystem B: Memory Management Demo")
    print("#"*65)
    run_experiments()
