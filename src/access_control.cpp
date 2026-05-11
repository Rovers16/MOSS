#include "moss/sync/access_control.h"
#include <cstdio>

namespace moss::sync {

// ── Permission matrix ────────────────────────────────────────────────────────
// ADMIN : READ, WRITE, EXECUTE
// USER  : READ, WRITE
// GUEST : READ only

AccessControl::AccessControl() : log_mutex_("ac_log") {}

bool AccessControl::is_allowed(Role role, Permission perm) const {
    switch (role) {
        case Role::ADMIN:
            // Admin may do everything
            return true;
        case Role::USER:
            // User may read or write, but not execute
            return (perm == Permission::READ || perm == Permission::WRITE);
        case Role::GUEST:
            // Guest may only read
            return (perm == Permission::READ);
        default:
            return false;
    }
}

bool AccessControl::check_access(const std::string& user,
                                  Role               role,
                                  Permission         perm,
                                  const std::string& resource) {
    bool granted = is_allowed(role, perm);

    // Serialize log output so concurrent checks don't produce garbled lines
    MutexGuard guard(log_mutex_);
    printf("[ACCESS] %-6s %-10s → %-8s on %-12s : %s\n",
           role_to_string(role).c_str(),
           user.c_str(),
           perm_to_string(perm).c_str(),
           resource.c_str(),
           granted ? "GRANTED ✓" : "DENIED  ✗");

    return granted;
}

} // namespace moss::sync
