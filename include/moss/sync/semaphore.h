#pragma once
#include <pthread.h>
#include <string>

namespace moss::sync {

/**
 * Counting Semaphore — built on pthread_mutex_t + pthread_cond_t.
 *
 * acquire() (P / wait):  decrements the count; blocks if count == 0
 * release() (V / signal): increments the count; wakes one blocked thread
 *
 * This is intentionally implemented from scratch (no POSIX sem_t, no
 * std::counting_semaphore) to satisfy the "implement your own" requirement.
 */
class Semaphore {
public:
    explicit Semaphore(const std::string& name, int initial_permits);
    ~Semaphore();

    // Block until a permit is available, then consume one
    void acquire();

    // Return one permit, waking a waiting thread if any
    void release();

    int  count()       const { return count_; }
    const std::string& name() const { return name_; }

    Semaphore(const Semaphore&)            = delete;
    Semaphore& operator=(const Semaphore&) = delete;

private:
    std::string     name_;
    int             count_;       // current number of available permits
    pthread_mutex_t mtx_;         // protects count_
    pthread_cond_t  cond_;        // signaled when a permit becomes available
};

} // namespace moss::sync
