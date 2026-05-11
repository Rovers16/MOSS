#pragma once
#include "moss/sync/role.h"
#include "moss/sync/permission.h"
#include "moss/sync/mutex.h"
#include <string>
#include <unordered_map>

namespace moss::sync {

/**
 * AccessControl — role-based permission system.
 *
 * Permission matrix (what each role may do):
 *   ADMIN : READ, WRITE, EXECUTE
 *   USER  : READ, WRITE
 *   GUEST : READ only
 *
 * check_access() is thread-safe (protected by an internal mutex so that
 * log output is never interleaved).
 */
class AccessControl {
public:
    AccessControl();

    /**
     * Check whether 'user' with 'role' may perform 'perm' on 'resource'.
     * Prints a log line regardless of outcome and returns true if granted.
     */
    bool check_access(const std::string& user,
                      Role               role,
                      Permission         perm,
                      const std::string& resource);

private:
    // Returns true if role is allowed to perform perm
    bool is_allowed(Role role, Permission perm) const;

    Mutex log_mutex_;   // serializes console output
};

} // namespace moss::sync
