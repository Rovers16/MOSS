# =============================================================================
# Makefile  —  MOSS: Mini OS Services Simulator
# =============================================================================

PYTHON = python3
SRC    = src/main.py
TESTS  = tests/test_sched.py tests/test_mem.py tests/test_sync.py

.PHONY: run test clean help

# Run the interactive simulator
run:
	$(PYTHON) $(SRC)

# Run all tests
test:
	$(PYTHON) -m pytest $(TESTS) -v

# Run individual subsystem tests
test-sched:
	$(PYTHON) -m pytest tests/test_sched.py -v

test-mem:
	$(PYTHON) -m pytest tests/test_mem.py -v

test-sync:
	$(PYTHON) -m pytest tests/test_sync.py -v

# Run the vertical slice demo non-interactively
demo:
	$(PYTHON) -c "from src.main import MOSS; m=MOSS(); m.dispatch('vertical_slice')"

# Remove cache files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

help:
	@echo "make run        — start the interactive MOSS simulator"
	@echo "make test       — run all 36 pytest tests"
	@echo "make test-sched — Subsystem A tests only"
	@echo "make test-mem   — Subsystem B tests only"
	@echo "make test-sync  — Subsystem C tests only"
	@echo "make demo       — run vertical slice demo"
	@echo "make clean      — remove cache files"
