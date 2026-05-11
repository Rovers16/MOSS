# =============================================================================
# mem.py  —  Subsystem B: Memory Management & Virtual Memory
# COSC 514 | MOSS Project
# =============================================================================
# This module simulates how an OS manages physical memory using paging.
# It translates logical (virtual) addresses to physical addresses, detects
# page faults, and replaces pages using FIFO, LRU, or Optimal algorithms.
# =============================================================================

from collections import deque   # deque = double-ended queue; used for FIFO
from typing import List, Tuple  # just for type hints in function signatures


# -----------------------------------------------------------------------------
# CONSTANTS
# -----------------------------------------------------------------------------

SUCCESS   =  0   # return code: operation succeeded
ERR_FAULT = -1   # return code: page fault occurred (page not in memory)
ERR_INVALID = -2 # return code: bad input (e.g. address out of range)


# -----------------------------------------------------------------------------
# MemoryManager class
# Owns all internal state for the memory subsystem.
# Other subsystems interact ONLY through the public API functions below.
# -----------------------------------------------------------------------------

class MemoryManager:

    def __init__(self, num_frames: int, page_size: int, logical_address_bits: int = 16):
        """
        Set up the memory manager.

        num_frames            : how many physical frames RAM has (e.g. 3)
        page_size             : size of each page/frame in bytes (e.g. 256)
        logical_address_bits  : how many bits wide a logical address is (e.g. 16)

        Example: 16-bit address space, 256-byte pages
          → 2^16 = 65536 total bytes of logical address space
          → 65536 / 256 = 256 possible pages
        """

        # --- store config ---
        self.num_frames           = num_frames
        self.page_size            = page_size
        self.logical_address_bits = logical_address_bits

        # total number of pages that can exist in logical address space
        # e.g. 2^16 / 256 = 256 pages
        self.num_pages = (2 ** logical_address_bits) // page_size

        # --- page table ---
        # Index = page number.  Value = frame number, or None if not loaded.
        # This is the OS's map of "which page is in which frame right now."
        self.page_table = [None] * self.num_pages

        # --- physical frames ---
        # A list of which page is currently occupying each frame.
        # Index = frame number.  Value = page number, or None if empty.
        self.frames = [None] * num_frames

        # --- FIFO state ---
        # A queue that tracks the ORDER pages arrived in memory.
        # When we need to evict, we pop from the front (oldest page).
        self.fifo_queue = deque()

        # --- LRU state ---
        # A list that tracks RECENCY OF USE.
        # Most-recently used page is at the END; least-recently used at FRONT.
        self.lru_order = []

        # --- statistics ---
        self.page_faults  = 0   # how many times a page wasn't in memory
        self.page_hits    = 0   # how many times a page WAS already in memory
        self.total_access = 0   # total number of memory accesses made

        # --- event log ---
        # Every access is recorded here so we can display a trace table.
        # Each entry is a dict with keys: address, page, offset, hit/fault, evicted, frames
        self.access_log: List[dict] = []

        # --- algorithm currently in use ---
        # Set by mem_set_algorithm(). Determines which replacement policy runs.
        self.algorithm = "FIFO"  # default


    # =========================================================================
    # PUBLIC API — these are the only functions other subsystems should call
    # =========================================================================

    def mem_set_algorithm(self, algo: str) -> int:
        """
        Choose the page replacement algorithm.
        algo must be one of: "FIFO", "LRU", "OPTIMAL"
        Returns SUCCESS or ERR_INVALID.
        """
        algo = algo.upper()
        if algo not in ("FIFO", "LRU", "OPTIMAL"):
            return ERR_INVALID
        self.algorithm = algo
        return SUCCESS


    def mem_reset(self) -> int:
        """
        Clear all state so a fresh simulation can run with the same config.
        Wipes the page table, frames, queues, stats, and log.
        Returns SUCCESS.
        """
        self.page_table   = [None] * self.num_pages
        self.frames       = [None] * self.num_frames
        self.fifo_queue   = deque()
        self.lru_order    = []
        self.page_faults  = 0
        self.page_hits    = 0
        self.total_access = 0
        self.access_log   = []
        return SUCCESS


    def mem_access(self, logical_address: int, reference_string: List[int] = None,
                   future_index: int = None) -> int:
        """
        Simulate one memory access at the given logical address.

        logical_address  : the virtual address the process wants to read/write
        reference_string : full page reference list (only needed for OPTIMAL)
        future_index     : current position in reference_string (for OPTIMAL)

        Steps:
          1. Validate the address
          2. Split address into page number + offset
          3. Check page table → hit or fault?
          4. On fault: load page, possibly evict an old one
          5. Log the event and update stats

        Returns SUCCESS (page was already there) or ERR_FAULT (page had to be loaded).
        """

        # --- step 1: validate ---
        max_address = (2 ** self.logical_address_bits) - 1
        if logical_address < 0 or logical_address > max_address:
            return ERR_INVALID

        # --- step 2: address translation ---
        # A logical address encodes TWO things:
        #   page number = which page (high bits)
        #   offset      = byte position WITHIN that page (low bits)
        #
        # Example: page_size=256 (2^8), address=0x1AF3 (6899 decimal)
        #   offset      = 6899 % 256 = 243  (low 8 bits)
        #   page_number = 6899 // 256 = 26  (high bits)
        #
        page_number = logical_address // self.page_size
        offset      = logical_address %  self.page_size

        self.total_access += 1

        # snapshot of frames BEFORE this access (for the log)
        frames_before = list(self.frames)

        # --- step 3: check page table ---
        if self.page_table[page_number] is not None:
            # PAGE HIT — page is already in a frame
            self.page_hits += 1
            self._update_lru(page_number)   # keep LRU order current

            self.access_log.append({
                "address"  : hex(logical_address),
                "page"     : page_number,
                "offset"   : offset,
                "result"   : "HIT",
                "evicted"  : None,
                "frames"   : list(self.frames)
            })
            return SUCCESS

        # --- step 4: PAGE FAULT — page is NOT in memory ---
        self.page_faults += 1
        evicted_page = None

        # is there a free frame? find it.
        free_frame = self._find_free_frame()

        if free_frame is not None:
            # there's an empty frame — just load the page there, no eviction needed
            frame_to_use = free_frame
        else:
            # all frames are full — must evict someone
            evicted_page, frame_to_use = self._evict(
                reference_string=reference_string,
                future_index=future_index
            )
            # remove the evicted page from the page table
            self.page_table[evicted_page] = None

        # load the new page into the chosen frame
        self.frames[frame_to_use]       = page_number
        self.page_table[page_number]    = frame_to_use

        # update FIFO queue and LRU order with the new page
        self.fifo_queue.append(page_number)
        self._update_lru(page_number)

        self.access_log.append({
            "address" : hex(logical_address),
            "page"    : page_number,
            "offset"  : offset,
            "result"  : "FAULT",
            "evicted" : evicted_page,
            "frames"  : list(self.frames)
        })
        return ERR_FAULT


    def mem_run_reference_string(self, reference_string: List[int]) -> dict:
        """
        Run an entire page reference string through the simulator.
        This is the main entry point for running a full experiment.

        reference_string : list of page numbers to access in order
                           e.g. [1, 2, 3, 2, 4, 1, 3]

        Returns a summary dict with hits, faults, fault rate, and the full log.
        """
        self.mem_reset()

        for i, page in enumerate(reference_string):
            # Convert page number to a logical address (just multiply by page_size).
            # This simulates accessing the first byte of each page.
            logical_addr = page * self.page_size

            self.mem_access(
                logical_address  = logical_addr,
                reference_string = reference_string,   # needed by OPTIMAL
                future_index     = i                   # our current position
            )

        return self.mem_get_stats()


    def mem_get_stats(self) -> dict:
        """
        Return current performance statistics.
        Called after a simulation run to get the summary.
        """
        fault_rate = (self.page_faults / self.total_access * 100) if self.total_access > 0 else 0
        return {
            "algorithm"   : self.algorithm,
            "num_frames"  : self.num_frames,
            "total_access": self.total_access,
            "page_hits"   : self.page_hits,
            "page_faults" : self.page_faults,
            "fault_rate"  : round(fault_rate, 2)
        }


    def mem_print_trace(self) -> int:
        """
        Print a step-by-step trace table of every memory access.
        Shows: page accessed, hit or fault, what was evicted, frame state.
        Returns SUCCESS.
        """
        print(f"\n{'='*60}")
        print(f"  Memory Trace  |  Algorithm: {self.algorithm}  |  Frames: {self.num_frames}")
        print(f"{'='*60}")
        print(f"{'Step':<6} {'Page':<6} {'Result':<8} {'Evicted':<9} {'Frames'}")
        print(f"{'-'*60}")

        for i, entry in enumerate(self.access_log):
            evicted = str(entry["evicted"]) if entry["evicted"] is not None else "-"
            frames  = str([f if f is not None else "_" for f in entry["frames"]])
            print(f"{i+1:<6} {entry['page']:<6} {entry['result']:<8} {evicted:<9} {frames}")

        stats = self.mem_get_stats()
        print(f"{'-'*60}")
        print(f"  Hits: {stats['page_hits']}  |  Faults: {stats['page_faults']}  |  Fault Rate: {stats['fault_rate']}%")
        print(f"{'='*60}\n")
        return SUCCESS


    # =========================================================================
    # PRIVATE HELPERS — internal logic, not part of the public API
    # =========================================================================

    def _find_free_frame(self):
        """Return the index of an empty frame, or None if all frames are full."""
        for i, page in enumerate(self.frames):
            if page is None:
                return i
        return None


    def _update_lru(self, page_number: int):
        """
        Move page_number to the END of lru_order (most recently used position).
        If it's already in the list, remove it first then re-append.
        """
        if page_number in self.lru_order:
            self.lru_order.remove(page_number)
        self.lru_order.append(page_number)


    def _evict(self, reference_string: List[int] = None, future_index: int = None) -> Tuple[int, int]:
        """
        Choose a victim page to evict based on the current algorithm.
        Returns (evicted_page_number, frame_index_that_is_now_free).
        """
        if self.algorithm == "FIFO":
            return self._evict_fifo()
        elif self.algorithm == "LRU":
            return self._evict_lru()
        elif self.algorithm == "OPTIMAL":
            return self._evict_optimal(reference_string, future_index)


    def _evict_fifo(self) -> Tuple[int, int]:
        """
        FIFO eviction: remove the page that arrived in memory FIRST.
        fifo_queue front = oldest page.
        """
        # pop the oldest page from the front of the queue
        victim_page = self.fifo_queue.popleft()
        # find which frame it's sitting in
        frame_index = self.page_table[victim_page]
        return victim_page, frame_index


    def _evict_lru(self) -> Tuple[int, int]:
        """
        LRU eviction: remove the page that was used LEAST RECENTLY.
        lru_order[0] = least recently used (it's at the front).
        """
        # the front of lru_order is the least recently used page
        victim_page = self.lru_order.pop(0)
        frame_index = self.page_table[victim_page]
        # also remove it from fifo_queue so queues stay consistent
        if victim_page in self.fifo_queue:
            self.fifo_queue.remove(victim_page)
        return victim_page, frame_index


    def _evict_optimal(self, reference_string: List[int], future_index: int) -> Tuple[int, int]:
        """
        OPTIMAL eviction: remove the page whose NEXT USE is furthest in the future.
        If a page will never be used again, evict it immediately.

        This requires knowing the full reference string in advance — which is
        why it's only usable as a benchmark, not in a real OS.

        reference_string : full list of page accesses
        future_index     : current position (we look AHEAD from here)
        """
        # collect pages currently in frames (ignore empty slots)
        pages_in_memory = [p for p in self.frames if p is not None]

        # future references = everything AFTER current position
        future = reference_string[future_index + 1:]

        farthest_page  = None
        farthest_dist  = -1

        for page in pages_in_memory:
            if page in future:
                # how far away is the next use of this page?
                dist = future.index(page)
            else:
                # page never used again → perfect candidate for eviction
                # use infinity so it always wins
                dist = float('inf')

            if dist > farthest_dist:
                farthest_dist = dist
                farthest_page = page

        frame_index = self.page_table[farthest_page]
        # clean up queues
        if farthest_page in self.fifo_queue:
            self.fifo_queue.remove(farthest_page)
        if farthest_page in self.lru_order:
            self.lru_order.remove(farthest_page)

        return farthest_page, frame_index
