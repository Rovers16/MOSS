#include "moss/sync/semaphore.h"
#include <stdexcept>

namespace moss::sync {

Semaphore::Semaphore(const std::string& name, int initial_permits)
    : name_(name), count_(initial_permits) {

    if (initial_permits < 0)
        throw std::invalid_argument("Semaphore: initial_permits must be >= 0");

    if (pthread_mutex_init(&mtx_, nullptr) != 0)
        throw std::runtime_error("Semaphore: pthread_mutex_init failed");

    if (pthread_cond_init(&cond_, nullptr) != 0) {
        pthread_mutex_destroy(&mtx_);
        throw std::runtime_error("Semaphore: pthread_cond_init failed");
    }
}

Semaphore::~Semaphore() {
    pthread_cond_destroy(&cond_);
    pthread_mutex_destroy(&mtx_);
}

void Semaphore::acquire() {
    // Lock the internal mutex so we can safely inspect count_
    pthread_mutex_lock(&mtx_);

    // While no permits are available, block on the condition variable.
    // pthread_cond_wait atomically releases mtx_ and suspends the thread.
    // When signaled, it reacquires mtx_ before returning — so we must
    // re-check count_ in a loop (guards against spurious wakeups).
    while (count_ == 0)
        pthread_cond_wait(&cond_, &mtx_);

    // A permit is now available — consume it
    --count_;

    pthread_mutex_unlock(&mtx_);
}

void Semaphore::release() {
    pthread_mutex_lock(&mtx_);

    // Return one permit
    ++count_;

    // Wake exactly one thread waiting in acquire() (if any).
    // We use signal (not broadcast) because only one permit was added.
    pthread_cond_signal(&cond_);

    pthread_mutex_unlock(&mtx_);
}

} // namespace moss::sync
