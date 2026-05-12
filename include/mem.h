# =============================================================================
# mem.h  —  Subsystem B Interface: Memory Management
# =============================================================================
# Public API (from mem.py):
#
#   MemoryManager(num_frames, page_size)
#   .mem_set_algorithm(algo)                            -> int
#   .mem_access(address, reference_string=None,
#               future_index=None)                      -> int
#   .mem_run_reference_string(ref_list)                 -> None
#   .mem_reset()                                        -> None
#   .mem_get_stats()                                    -> dict
#   .mem_print_trace()                                  -> None
#
# Algorithms: FIFO | LRU | OPTIMAL
# Return codes: SUCCESS=0  ERR_FAULT=-1  ERR_INVALID=-2
# =============================================================================
