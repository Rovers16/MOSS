#include "moss/sync/bounded_buffer.h"
#include <sstream>
#include <stdexcept>

namespace moss::sync {

BoundedBuffer::BoundedBuffer(int capacity)
    : capacity_(capacity),
      head_(0), tail_(0), size_(0),
      buffer_(capacity),
      empty_slots_("empty_slots", capacity),   // all slots free initially
      filled_slots_("filled_slots", 0),         // no items initially
      buf_mutex_("buf_mutex")
{
    if (capacity <= 0)
        throw std::invalid_argument("BoundedBuffer: capacity must be > 0");
}

void BoundedBuffer::produce(const std::string& item) {
    // Wait for a free slot (blocks if buffer is full)
    empty_slots_.acquire();

    // Exclusive access to buffer data structures
    buf_mutex_.lock();
    buffer_[tail_] = item;
    tail_ = (tail_ + 1) % capacity_;   // circular advance
    ++size_;
    buf_mutex_.unlock();

    // Signal that one more item is now available for consumers
    filled_slots_.release();
}

std::string BoundedBuffer::consume() {
    // Wait for an available item (blocks if buffer is empty)
    filled_slots_.acquire();

    buf_mutex_.lock();
    std::string item = buffer_[head_];
    buffer_[head_].clear();
    head_ = (head_ + 1) % capacity_;   // circular advance
    --size_;
    buf_mutex_.unlock();

    // Signal that one more slot is now free for producers
    empty_slots_.release();

    return item;
}

std::string BoundedBuffer::state_string() const {
    // NOTE: caller must hold buf_mutex_ if calling from a concurrent context.
    // Here we take a snapshot under the mutex for safety.
    std::ostringstream oss;
    oss << "[";
    int idx  = head_;
    int seen = 0;
    while (seen < size_) {
        if (seen > 0) oss << ", ";
        oss << buffer_[idx];
        idx = (idx + 1) % capacity_;
        ++seen;
    }
    oss << "] (" << size_ << "/" << capacity_ << ")";
    return oss.str();
}

} // namespace moss::sync
