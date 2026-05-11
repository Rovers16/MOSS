#pragma once
#include <string>

namespace moss::sync {

enum class Role { ADMIN, USER, GUEST };

inline std::string role_to_string(Role r) {
    switch (r) {
        case Role::ADMIN: return "ADMIN";
        case Role::USER:  return "USER";
        case Role::GUEST: return "GUEST";
        default:          return "UNKNOWN";
    }
}

} // namespace moss::sync
