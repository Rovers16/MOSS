#pragma once
#include <string>

namespace moss::sync {

enum class Permission { READ, WRITE, EXECUTE };

inline std::string perm_to_string(Permission p) {
    switch (p) {
        case Permission::READ:    return "READ";
        case Permission::WRITE:   return "WRITE";
        case Permission::EXECUTE: return "EXECUTE";
        default:                  return "UNKNOWN";
    }
}

} // namespace moss::sync
