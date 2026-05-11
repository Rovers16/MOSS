#include "moss/sync/mutex.h"
#include <pthread.h>
#include <cstdio>
#include <cstdint>
#include <ctime>

// ── Shared state ─────────────────────────────────────────────────────────────
static const int    N_THREADS    = 3;
static const long   N_INCREMENTS = 10'000'000L;

static int64_t             g_counter   = 0;
static bool                g_use_mutex = false;
static moss::sync::Mutex*  g_mutex     = nullptr;

// ── Worker thread ─────────────────────────────────────────────────────────────
void* race_worker(void* arg) {
    long tid = reinterpret_cast<long>(arg);
    (void)tid;   // suppress unused-variable warning in non-verbose builds

    for (long i = 0; i < N_INCREMENTS; ++i) {
        if (g_use_mutex) {
            // ── CRITICAL SECTION ─────────────────────────────────────────
            // Only one thread may increment at a time.
            // Without this guard, load/add/store can interleave and produce
            // lost updates (the classic race condition from Lab 4).
            g_mutex->lock();
            g_counter++;
            g_mutex->unlock();
            // ── END CRITICAL SECTION ─────────────────────────────────────
        } else {
            // Unsynchronized: counter++ is NOT atomic — it expands to:
            //   1. load  counter → register
            //   2. add   1
            //   3. store register → counter
            // Two threads can both load the same value and both store the
            // same incremented value, causing a "lost update".
            g_counter++;
        }
    }
    return nullptr;
}

// ── Run one experiment ────────────────────────────────────────────────────────
static void run_experiment(bool use_mutex, moss::sync::Mutex& mtx) {
    g_counter   = 0;
    g_use_mutex = use_mutex;
    g_mutex     = &mtx;

    pthread_t threads[N_THREADS];

    struct timespec t_start, t_end;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    for (long t = 0; t < N_THREADS; ++t)
        pthread_create(&threads[t], nullptr, race_worker, reinterpret_cast<void*>(t + 1));

    for (int t = 0; t < N_THREADS; ++t)
        pthread_join(threads[t], nullptr);

    clock_gettime(CLOCK_MONOTONIC, &t_end);
    double elapsed_ms = (t_end.tv_sec  - t_start.tv_sec)  * 1000.0
                      + (t_end.tv_nsec - t_start.tv_nsec) / 1'000'000.0;

    long expected = (long)N_THREADS * N_INCREMENTS;
    printf("  Mode     : %s\n",    use_mutex ? "MUTEX (synchronized)" : "NO LOCK (unsynchronized)");
    printf("  Threads  : %d\n",    N_THREADS);
    printf("  Increments/thread: %ld\n", N_INCREMENTS);
    printf("  Expected : %ld\n",   expected);
    printf("  Actual   : %ld\n",   g_counter);
    printf("  Lost     : %ld\n",   expected - g_counter);
    printf("  Time     : %.2f ms\n", elapsed_ms);
    printf("  Result   : %s\n",
           (g_counter == expected) ? "Correct (no lost updates) ✓"
                                   : "DATA RACE OBSERVED (lost updates) ✗");
}

// ── Entry point called from main.cpp ─────────────────────────────────────────
void run_race_demo() {
    printf("\n");
    printf("══════════════════════════════════════════════════════════════\n");
    printf("  DEMO 1 — Race Condition Demo  (Lab 4 reference behavior)\n");
    printf("══════════════════════════════════════════════════════════════\n");

    moss::sync::Mutex mtx("race_mutex");

    printf("\n── Experiment A: No synchronization ──────────────────────────\n");
    run_experiment(false, mtx);

    printf("\n── Experiment B: With Mutex ──────────────────────────────────\n");
    run_experiment(true, mtx);

    printf("\n[Race Demo] Observation: mutex serializes the critical section,\n");
    printf("  trading some parallelism for guaranteed correctness.\n");
}
