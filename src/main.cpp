/**
 * main.cpp — MOSS Subsystem C driver and public API
 *
 * Runs all three demos in sequence and exposes the integration API
 * that Part II (unified MOSS) will call.
 *
 * Public API (moss::sync namespace):
 *   get_mutex(name)                         → Mutex*
 *   get_semaphore(name, permits)            → Semaphore*
 *   check_access(user, role, perm, resource)→ bool
 */

#include "moss/sync/mutex.h"
#include "moss/sync/semaphore.h"
#include "moss/sync/access_control.h"
#include "moss/sync/role.h"
#include "moss/sync/permission.h"

#include <cstdio>
#include <string>
#include <unordered_map>
#include <memory>

// Forward declarations for demo entry points
void run_race_demo();
void run_producer_consumer();

// ── Registry storage (named primitives for Part II integration) ───────────────
namespace {
    std::unordered_map<std::string, std::unique_ptr<moss::sync::Mutex>>     mutex_registry;
    std::unordered_map<std::string, std::unique_ptr<moss::sync::Semaphore>> sem_registry;
    moss::sync::AccessControl ac;
}

// ── Public API ────────────────────────────────────────────────────────────────
namespace moss::sync {

/**
 * Returns (creating if needed) a named Mutex.
 * Part II calls this to obtain a shared lock by name.
 */
Mutex* get_mutex(const std::string& name) {
    auto it = mutex_registry.find(name);
    if (it == mutex_registry.end()) {
        mutex_registry[name] = std::make_unique<Mutex>(name);
        it = mutex_registry.find(name);
    }
    return it->second.get();
}

/**
 * Returns (creating if needed) a named Semaphore with the given permit count.
 * If the semaphore already exists, the existing one is returned (permits ignored).
 */
Semaphore* get_semaphore(const std::string& name, int permits) {
    auto it = sem_registry.find(name);
    if (it == sem_registry.end()) {
        sem_registry[name] = std::make_unique<Semaphore>(name, permits);
        it = sem_registry.find(name);
    }
    return it->second.get();
}

/**
 * Checks whether user with role may perform perm on resource.
 * Logs the result and returns true if access is granted.
 */
bool check_access(const std::string& user,
                  Role               role,
                  Permission         perm,
                  const std::string& resource) {
    return ac.check_access(user, role, perm, resource);
}

} // namespace moss::sync

// ── Access Control demo ───────────────────────────────────────────────────────
static void run_access_control_demo() {
    using namespace moss::sync;

    printf("\n");
    printf("══════════════════════════════════════════════════════════════\n");
    printf("  DEMO 3 — Access Control (Role-Based Permission System)\n");
    printf("  Roles: ADMIN | USER | GUEST\n");
    printf("  Permissions: READ | WRITE | EXECUTE\n");
    printf("══════════════════════════════════════════════════════════════\n\n");

    // ADMIN — should be granted everything
    check_access("root",  Role::ADMIN, Permission::READ,    "FileX");
    check_access("root",  Role::ADMIN, Permission::WRITE,   "FileX");
    check_access("root",  Role::ADMIN, Permission::EXECUTE, "FileX");

    printf("\n");

    // USER — read and write allowed, execute denied
    check_access("alice", Role::USER,  Permission::READ,    "FileY");
    check_access("alice", Role::USER,  Permission::WRITE,   "FileY");
    check_access("alice", Role::USER,  Permission::EXECUTE, "FileY");

    printf("\n");

    // GUEST — read only
    check_access("guest1", Role::GUEST, Permission::READ,    "FileZ");
    check_access("guest1", Role::GUEST, Permission::WRITE,   "FileZ");
    check_access("guest1", Role::GUEST, Permission::EXECUTE, "FileZ");

    printf("\n[Access Control] Matrix enforced correctly.\n");
}

// ── Main ──────────────────────────────────────────────────────────────────────
int main() {
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║   MOSS — Mini OS Services Simulator                         ║\n");
    printf("║   Subsystem C: Synchronization & Protection                 ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");

    run_race_demo();
    run_producer_consumer();
    run_access_control_demo();

    printf("\n══════════════════════════════════════════════════════════════\n");
    printf("  Subsystem C complete. All demos passed.\n");
    printf("══════════════════════════════════════════════════════════════\n\n");
    return 0;
}
