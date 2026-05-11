# =============================================================================
# main.py  —  MOSS: Mini Operating System Services Simulator
# COSC 514 | Unified Command-Line Interface
# =============================================================================
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cpu_sched import Scheduler
from mem       import MemoryManager
from sync      import SyncManager


class MOSS:

    def __init__(self):
        self.scheduler  = Scheduler()
        self.memory     = MemoryManager(num_frames=3, page_size=256)
        self.sync       = SyncManager()
        self.system_log = []
        self.vs_process_created  = False
        self.vs_scheduled        = False
        self.vs_memory_accessed  = False
        self.vs_sync_checked     = False
        self._log("MOSS simulator initialized.")

    def _log(self, message):
        self.system_log.append(message)
        print(f"  [MOSS] {message}")

    def dispatch(self, line):
        line = line.strip()
        if not line:
            return True
        tokens  = line.split()
        command = tokens[0].lower()
        args    = tokens[1:]

        if   command == "help":             self._cmd_help()
        elif command == "exit":             print("\n  Goodbye.\n"); return False
        elif command == "create_process":   self._cmd_create_process(args)
        elif command == "list_processes":   self._cmd_list_processes()
        elif command == "schedule":         self._cmd_schedule(args)
        elif command == "mem_config":       self._cmd_mem_config(args)
        elif command == "mem_algo":         self._cmd_mem_algo(args)
        elif command == "access_memory":    self._cmd_access_memory(args)
        elif command == "mem_run":          self._cmd_mem_run(args)
        elif command == "mem_stats":        self._cmd_mem_stats()
        elif command == "create_mutex":     self._cmd_create_mutex(args)
        elif command == "lock":             self._cmd_lock(args)
        elif command == "unlock":           self._cmd_unlock(args)
        elif command == "create_semaphore": self._cmd_create_semaphore(args)
        elif command == "sem_wait":         self._cmd_sem_wait(args)
        elif command == "sem_signal":       self._cmd_sem_signal(args)
        elif command == "setup_pc":         self._cmd_setup_pc(args)
        elif command == "produce":          self._cmd_produce(args)
        elif command == "consume":          self._cmd_consume(args)
        elif command == "add_user":         self._cmd_add_user(args)
        elif command == "add_resource":     self._cmd_add_resource(args)
        elif command == "check_access":     self._cmd_check_access(args)
        elif command == "show_sync_logs":   self.sync.sync_print_all_logs()
        elif command == "vertical_slice":   self._cmd_vertical_slice()
        elif command == "show_log":         self._cmd_show_log()
        elif command == "reset":            self._cmd_reset()
        else:
            print(f"  Unknown command: '{command}'. Type 'help' for a list.")
        return True

    def _cmd_help(self):
        print("""
  ╔══════════════════════════════════════════════════════════╗
  ║         MOSS — Mini OS Services Simulator                ║
  ║         COSC 514 | Command Reference                     ║
  ╚══════════════════════════════════════════════════════════╝

  PROCESS & SCHEDULING
    create_process <pid> <arrival> <burst> [priority]
    list_processes
    schedule <FCFS|RR|PRIORITY|MLFQ> [quantum]

  MEMORY
    mem_config <frames> <page_size>
    mem_algo <FIFO|LRU|OPTIMAL>
    access_memory <hex_address>        e.g. access_memory 0x1AF3
    mem_run <page> [page] ...          e.g. mem_run 1 2 3 2 4 1 3
    mem_stats

  SYNCHRONIZATION
    create_mutex <name>
    lock <name> <pid>
    unlock <name> <pid>
    create_semaphore <name> <value>
    sem_wait <name> <pid>
    sem_signal <name> <pid>
    setup_pc <buffer_size>
    produce <pid> <item>
    consume <pid>
    add_user <pid> <admin|user|guest>
    add_resource <name> <read_role> <write_role>
    check_access <pid> <resource> <read|write>
    show_sync_logs

  SYSTEM
    vertical_slice    end-to-end demo through all three subsystems
    show_log          full system event log
    reset             reset all subsystems
    exit
        """)

    # ── SCHEDULING ────────────────────────────────────────────────────────────

    def _cmd_create_process(self, args):
        if len(args) < 3:
            print("  Usage: create_process <pid> <arrival> <burst> [priority]"); return
        try:
            pid=int(args[0]); arrival=int(args[1]); burst=int(args[2])
            priority=int(args[3]) if len(args)>3 else 0
        except ValueError:
            print("  Error: all fields must be integers."); return
        if self.scheduler.sched_add_process(pid,arrival,burst,priority)==0:
            self._log(f"Process created: PID={pid} arrival={arrival} burst={burst} priority={priority}")
            self.vs_process_created = True
        else:
            print("  Error: burst must be > 0.")

    def _cmd_list_processes(self):
        if not self.scheduler.processes:
            print("  No processes loaded."); return
        print(f"\n  {'PID':<6}{'Arrival':<9}{'Burst':<7}{'Priority'}")
        print(f"  {'-'*32}")
        for p in self.scheduler.processes:
            print(f"  {p.pid:<6}{p.arrival:<9}{p.burst:<7}{p.priority}")
        print()

    def _cmd_schedule(self, args):
        if not args:
            print("  Usage: schedule <FCFS|RR|PRIORITY|MLFQ> [quantum]"); return
        algo=args[0].upper(); quantum=int(args[1]) if len(args)>1 else 2
        if not self.scheduler.processes:
            print("  No processes. Use create_process first."); return
        results = self.scheduler.sched_run(algo, quantum)
        if "error" in results:
            print(f"  Error: {results['error']}"); return
        self.scheduler.sched_print_table(results)
        self.scheduler.sched_print_gantt()
        self._log(f"Scheduled {len(self.scheduler.processes)} processes using {results['algorithm']}")
        self.vs_scheduled = True

    # ── MEMORY ────────────────────────────────────────────────────────────────

    def _cmd_mem_config(self, args):
        if len(args)<2:
            print("  Usage: mem_config <frames> <page_size>"); return
        try: frames=int(args[0]); page_size=int(args[1])
        except ValueError:
            print("  Error: must be integers."); return
        algo = self.memory.algorithm          # FIX: preserve algorithm
        self.memory = MemoryManager(num_frames=frames, page_size=page_size)
        self.memory.mem_set_algorithm(algo)
        self._log(f"Memory reconfigured: {frames} frames, page_size={page_size}, algo={algo}")

    def _cmd_mem_algo(self, args):
        if not args:
            print("  Usage: mem_algo <FIFO|LRU|OPTIMAL>"); return
        if self.memory.mem_set_algorithm(args[0])==0:
            self._log(f"Memory algorithm set to {args[0].upper()}")
        else:
            print(f"  Error: unknown algorithm '{args[0]}'.")

    def _cmd_access_memory(self, args):
        if not args:
            print("  Usage: access_memory <hex_address>"); return
        try: address = int(args[0], 0)
        except ValueError:
            print(f"  Error: invalid address '{args[0]}'"); return
        # FIX: build reference_string so OPTIMAL works on single accesses
        current_pages = [e["page"] for e in self.memory.access_log]
        new_page      = address // self.memory.page_size
        ref_string    = current_pages + [new_page]
        future_index  = len(current_pages)
        result = self.memory.mem_access(address, reference_string=ref_string,
                                        future_index=future_index)
        self._log(f"Memory access {hex(address)}: {'HIT' if result==0 else 'PAGE FAULT'}")
        self.memory.mem_print_trace()
        self.vs_memory_accessed = True

    def _cmd_mem_run(self, args):
        if not args:
            print("  Usage: mem_run <page> [page] ..."); return
        try: ref_string=[int(x) for x in args]
        except ValueError:
            print("  Error: pages must be integers."); return
        self.memory.mem_run_reference_string(ref_string)
        self.memory.mem_print_trace()
        self._log(f"Memory simulation complete: ref_string={ref_string}")
        self.vs_memory_accessed = True

    def _cmd_mem_stats(self):
        stats = self.memory.mem_get_stats()
        print("\n  Memory Statistics:")
        for k,v in stats.items(): print(f"    {k:<15}: {v}")
        print()

    # ── SYNC ──────────────────────────────────────────────────────────────────

    def _cmd_create_mutex(self, args):
        if not args: print("  Usage: create_mutex <name>"); return
        self.sync.sync_create_mutex(args[0])
        self._log(f"Mutex created: '{args[0]}'")

    def _cmd_lock(self, args):
        if len(args)<2: print("  Usage: lock <name> <pid>"); return
        name=args[0]; pid=int(args[1])
        outcome="ACQUIRED" if self.sync.sync_mutex_acquire(name,pid)==0 else "BLOCKED"
        self._log(f"P{pid} {outcome} mutex '{name}'")
        self.vs_sync_checked=True

    def _cmd_unlock(self, args):
        if len(args)<2: print("  Usage: unlock <name> <pid>"); return
        name=args[0]; pid=int(args[1])
        if self.sync.sync_mutex_release(name,pid)==0:
            self._log(f"P{pid} released mutex '{name}'")
        else:
            print(f"  Error: P{pid} does not own mutex '{name}'")

    def _cmd_create_semaphore(self, args):
        if len(args)<2: print("  Usage: create_semaphore <name> <value>"); return
        self.sync.sync_create_semaphore(args[0],int(args[1]))
        self._log(f"Semaphore created: '{args[0]}' value={args[1]}")

    def _cmd_sem_wait(self, args):
        if len(args)<2: print("  Usage: sem_wait <name> <pid>"); return
        outcome="acquired" if self.sync.sync_semaphore_wait(args[0],int(args[1]))==0 else "BLOCKED"
        self._log(f"P{args[1]} sem_wait '{args[0]}': {outcome}")

    def _cmd_sem_signal(self, args):
        if len(args)<2: print("  Usage: sem_signal <name> <pid>"); return
        self.sync.sync_semaphore_signal(args[0],int(args[1]))
        self._log(f"P{args[1]} sem_signal '{args[0]}'")

    def _cmd_setup_pc(self, args):
        if not args: print("  Usage: setup_pc <buffer_size>"); return
        self.sync.sync_setup_producer_consumer(int(args[0]))
        self._log(f"Producer-Consumer initialized: buffer_size={args[0]}")

    def _cmd_produce(self, args):
        if len(args)<2: print("  Usage: produce <pid> <item>"); return
        pid=int(args[0]); item=int(args[1])
        outcome="added" if self.sync.sync_produce(pid,item)==0 else "BLOCKED (buffer full)"
        self._log(f"P{pid} produce item={item}: {outcome}")

    def _cmd_consume(self, args):
        if not args: print("  Usage: consume <pid>"); return
        pid=int(args[0])
        outcome="consumed" if self.sync.sync_consume(pid)==0 else "BLOCKED (buffer empty)"
        self._log(f"P{pid} consume: {outcome}")

    def _cmd_add_user(self, args):
        if len(args)<2: print("  Usage: add_user <pid> <admin|user|guest>"); return
        pid=int(args[0])
        if self.sync.sync_add_user(pid,args[1])==0:
            self._log(f"User registered: P{pid} role={args[1]}")
        else:
            print(f"  Error: invalid role '{args[1]}'.")

    def _cmd_add_resource(self, args):
        if len(args)<3: print("  Usage: add_resource <name> <read_role> <write_role>"); return
        if self.sync.sync_add_resource(args[0],args[1],args[2])==0:
            self._log(f"Resource registered: '{args[0]}' read={args[1]} write={args[2]}")
        else:
            print("  Error: invalid roles.")

    def _cmd_check_access(self, args):
        if len(args)<3: print("  Usage: check_access <pid> <resource> <read|write>"); return
        pid=int(args[0])
        outcome="GRANTED" if self.sync.sync_check_access(pid,args[1],args[2])==0 else "DENIED"
        self._log(f"Access check P{pid} → '{args[1]}' [{args[2]}]: {outcome}")
        self.vs_sync_checked=True

    # ── SYSTEM ────────────────────────────────────────────────────────────────

    def _cmd_vertical_slice(self):
        print("\n" + "="*60)
        print("  VERTICAL SLICE — End-to-End System Demo")
        print("="*60)
        print("\n  One process flows through all three subsystems in sequence.\n")

        # step 1
        print("  ── Step 1: Process Creation (Subsystem A) ──")
        self.scheduler.processes=[]; self.vs_process_created=False
        self.dispatch("create_process 1 0 4 1")
        self.dispatch("create_process 2 1 2 0")
        self.dispatch("create_process 3 2 6 2")

        # step 2
        print("\n  ── Step 2: CPU Scheduling — Priority (Subsystem A) ──")
        self.dispatch("schedule PRIORITY")

        # step 3
        print("\n  ── Step 3: Memory Management — LRU (Subsystem B) ──")
        self.memory=MemoryManager(num_frames=3,page_size=256)
        self.memory.mem_set_algorithm("LRU")
        self.vs_memory_accessed=False
        self.dispatch("mem_run 1 2 3 2 4 1 3")

        # step 4
        print("\n  ── Step 4: Synchronization & Protection (Subsystem C) ──")
        self.sync=SyncManager(); self.vs_sync_checked=False
        self.dispatch("add_user 1 admin")
        self.dispatch("add_user 2 user")
        self.dispatch("add_user 3 guest")
        self.dispatch("add_resource kernel_log admin admin")
        self.dispatch("add_resource user_file user user")
        self.dispatch("add_resource public_doc guest user")
        self.dispatch("create_mutex cpu_lock")
        self.dispatch("lock cpu_lock 1")
        self.dispatch("lock cpu_lock 2")
        self.dispatch("unlock cpu_lock 1")
        self.dispatch("check_access 1 kernel_log read")
        self.dispatch("check_access 2 kernel_log read")
        self.dispatch("check_access 2 user_file write")
        self.dispatch("check_access 3 public_doc read")
        self.dispatch("show_sync_logs")

        # summary
        print("\n  ── Vertical Slice Complete ──")
        print(f"  {'✓' if self.vs_process_created else '✗'} Process created       : {self.vs_process_created}")
        print(f"  {'✓' if self.vs_scheduled        else '✗'} Process scheduled     : {self.vs_scheduled}")
        print(f"  {'✓' if self.vs_memory_accessed  else '✗'} Memory access handled : {self.vs_memory_accessed}")
        print(f"  {'✓' if self.vs_sync_checked      else '✗'} Sync check applied    : {self.vs_sync_checked}")
        print("="*60 + "\n")

    def _cmd_show_log(self):
        print("\n  System Event Log:")
        print("  " + "-"*40)
        for i,entry in enumerate(self.system_log):
            print(f"  {i+1:>3}. {entry}")
        print()

    def _cmd_reset(self):
        self.__init__()
        print("  All subsystems reset to initial state.")

    def run(self):
        print("""
  ╔══════════════════════════════════════════════════════════╗
  ║     MOSS — Mini Operating System Services Simulator      ║
  ║     COSC 514 | Type 'help' for commands | 'exit' to quit ║
  ╚══════════════════════════════════════════════════════════╝
        """)
        while True:
            try:
                line = input("  moss> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  Goodbye.\n"); break
            if not self.dispatch(line):
                break


if __name__ == "__main__":
    moss = MOSS()
    moss.run()
