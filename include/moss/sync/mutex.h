#pragma once
#include <pthread.h>
#include <string>

namespace moss::sync {

/**
 * Mutex — wraps pthread_mutex_t to provide mutual exclusion.
 * Only one thread may hold the lock at a time; others block on lock().
 */
class Mutex {
public:
    explicit Mutex(const std::string& name = "unnamed");
    ~Mutex();

    // Acquire the lock — blocks if already held by another thread
    void lock();

    // Release the lock — must be called by the thread that called lock()
    void unlock();

    const std::string& name() const { return name_; }

    // Non-copyable
    Mutex(const Mutex&)            = delete;
    Mutex& operator=(const Mutex&) = delete;

private:
    std::string      name_;
    pthread_mutex_t  mtx_;
};

/**
 * RAII guard — locks on construction, unlocks on destruction.
 * Use instead of manual lock()/unlock() to avoid forgetting to unlock.
 */
class MutexGuard {
public:
    explicit MutexGuard(Mutex& m) : mutex_(m) { mutex_.lock(); }
    ~MutexGuard()                              { mutex_.unlock(); }
    MutexGuard(const MutexGuard&)            = delete;
    MutexGuard& operator=(const MutexGuard&) = delete;
private:
    Mutex& mutex_;
};

} // namespace moss::sync
