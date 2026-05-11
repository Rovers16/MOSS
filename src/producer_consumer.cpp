#include "moss/sync/bounded_buffer.h"
#include "moss/sync/mutex.h"
#include <pthread.h>
#include <cstdio>
#include <cstdlib>
#include <string>

// ── Configuration ────────────────────────────────────────────────────────────
static const int BUFFER_CAPACITY = 5;
static const int ITEMS_PER_PRODUCER = 6;
static const int N_PRODUCERS = 2;
static const int N_CONSUMERS = 2;

// Shared buffer and a mutex for clean console output
static moss::sync::BoundedBuffer* g_buffer  = nullptr;
static moss::sync::Mutex*         g_console  = nullptr;

// ── Producer thread ──────────────────────────────────────────────────────────
struct ProducerArgs { int id; };

void* producer_fn(void* arg) {
    auto* a = static_cast<ProducerArgs*>(arg);

    for (int i = 1; i <= ITEMS_PER_PRODUCER; ++i) {
        std::string item = "Item-P" + std::to_string(a->id) + "-" + std::to_string(i);
        g_buffer->produce(item);

        // Lock console so output lines from different threads don't interleave
        g_console->lock();
        printf("[Producer-%d] Produced: %-18s | Buffer: %s\n",
               a->id, item.c_str(), g_buffer->state_string().c_str());
        g_console->unlock();
    }
    return nullptr;
}

// ── Consumer thread ──────────────────────────────────────────────────────────
struct ConsumerArgs { int id; int items_to_consume; };

void* consumer_fn(void* arg) {
    auto* a = static_cast<ConsumerArgs*>(arg);

    for (int i = 0; i < a->items_to_consume; ++i) {
        std::string item = g_buffer->consume();

        g_console->lock();
        printf("[Consumer-%d] Consumed: %-18s | Buffer: %s\n",
               a->id, item.c_str(), g_buffer->state_string().c_str());
        g_console->unlock();
    }
    return nullptr;
}

// ── Entry point called from main.cpp ─────────────────────────────────────────
void run_producer_consumer() {
    printf("\n");
    printf("══════════════════════════════════════════════════════════════\n");
    printf("  DEMO 2 — Producer-Consumer (Bounded Buffer, capacity=%d)\n", BUFFER_CAPACITY);
    printf("  %d producers × %d items  |  %d consumers\n",
           N_PRODUCERS, ITEMS_PER_PRODUCER, N_CONSUMERS);
    printf("══════════════════════════════════════════════════════════════\n\n");

    moss::sync::BoundedBuffer buf(BUFFER_CAPACITY);
    moss::sync::Mutex         console("console");
    g_buffer  = &buf;
    g_console = &console;

    int total_items = N_PRODUCERS * ITEMS_PER_PRODUCER;   // must equal total consumed

    pthread_t prod_threads[N_PRODUCERS];
    pthread_t cons_threads[N_CONSUMERS];
    ProducerArgs prod_args[N_PRODUCERS];
    ConsumerArgs cons_args[N_CONSUMERS];

    // Distribute items evenly across consumers
    int items_each = total_items / N_CONSUMERS;

    for (int i = 0; i < N_PRODUCERS; ++i) {
        prod_args[i] = { i + 1 };
        pthread_create(&prod_threads[i], nullptr, producer_fn, &prod_args[i]);
    }
    for (int i = 0; i < N_CONSUMERS; ++i) {
        cons_args[i] = { i + 1, items_each };
        pthread_create(&cons_threads[i], nullptr, consumer_fn, &cons_args[i]);
    }

    for (int i = 0; i < N_PRODUCERS; ++i) pthread_join(prod_threads[i], nullptr);
    for (int i = 0; i < N_CONSUMERS; ++i) pthread_join(cons_threads[i], nullptr);

    printf("\n[Producer-Consumer] All items produced and consumed. Buffer empty: %s\n",
           buf.size() == 0 ? "YES ✓" : "NO ✗");

    g_buffer  = nullptr;
    g_console = nullptr;
}
