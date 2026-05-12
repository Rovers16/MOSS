# =============================================================================
# sync.h  —  Subsystem C Interface: Synchronization & Protection
# =============================================================================
# Public API (from sync.py via SyncManager):
#
#   SyncManager()
#   .sync_create_mutex(name)                            -> int
#   .sync_mutex_acquire(name, pid)                      -> int
#   .sync_mutex_release(name, pid)                      -> int
#   .sync_create_semaphore(name, value)                 -> int
#   .sync_semaphore_wait(name, pid)                     -> int
#   .sync_semaphore_signal(name, pid)                   -> int
#   .sync_setup_producer_consumer(buffer_size)          -> int
#   .sync_produce(pid, item)                            -> int
#   .sync_consume(pid)                                  -> int
#   .sync_add_user(pid, role)                           -> int
#   .sync_add_resource(name, read_role, write_role)     -> int
#   .sync_check_access(pid, resource, mode)             -> int
#   .sync_print_all_logs()                              -> None
#
# Roles: admin | user | guest
# Return codes: SUCCESS=0  ERR_LOCKED=-1  ERR_DENIED=-2
#               ERR_NOT_OWNER=-3  ERR_INVALID=-4
# =============================================================================
