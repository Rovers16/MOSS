#pragma once
#include "moss/sync/semaphore.h"
#include "moss/sync/mutex.h"
#include <string>
#include <vector>

namespace moss::sync {

/**
 * BoundedBuffer — a fixed-capacity circular buffer safe for concurrent
 * producer and consumer threads.
 *
 * Synchronization strategy (classic three-semaphore approach):
 *   empty_slots_  — counts free slots; producers acquire before writing
 *   filled_slots_ — counts filled slots; consumers acquire before reading
 *   buf_mutex_    — mutual exclusion on the buffer index/data themselves
 */
class BoundedBuffer {
public:
    explicit BoundedBuffer(int capacity);

    // Producer: blocks until a slot is free, then inserts item
    void produce(const std::string& item);

    // Consumer: blocks until an item is available, then removes and returns it
    std::string consume();

    int capacity()    const { return capacity_; }
    int size()        const { return size_; }      // current number of items

    // Returns a snapshot string like "[Item-1, Item-2] (2/5)"
    std::string state_string() const;

private:
    int                      capacity_;
    int                      head_;      // next read position
    int                      tail_;      // next write position
    int                      size_;      // current occupancy
    std::vector<std::string> buffer_;

    Semaphore empty_slots_;   // starts at capacity  (free slots)
    Semaphore filled_slots_;  // starts at 0         (filled slots)
    Mutex     buf_mutex_;     // protects head/tail/size/buffer
};

} // namespace moss::sync
