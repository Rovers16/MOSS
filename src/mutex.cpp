#include "moss/sync/mutex.h"
#include <stdexcept>

namespace moss::sync {

Mutex::Mutex(const std::string& name) : name_(name) {
    // Initialize with default attributes (non-recursive, fast mutex)
    if (pthread_mutex_init(&mtx_, nullptr) != 0)
        throw std::runtime_error("Mutex::Mutex — pthread_mutex_init failed for: " + name_);
}

Mutex::~Mutex() {
    pthread_mutex_destroy(&mtx_);
}

void Mutex::lock() {
    // pthread_mutex_lock blocks the calling thread until the mutex is free.
    // This is the "enter critical section" operation.
    pthread_mutex_lock(&mtx_);
}

void Mutex::unlock() {
    // pthread_mutex_unlock releases the mutex so another blocked thread
    // (if any) can proceed. This is the "exit critical section" operation.
    pthread_mutex_unlock(&mtx_);
}

} // namespace moss::sync
