# Thin convenience wrapper around tasks.py (the cross-platform runner).
# Windows users without `make` can call `python tasks.py <task>` directly.

PY ?= python
SEASONS ?= 1950:

.PHONY: backfill refresh build test docs export preview all

backfill: ; $(PY) tasks.py backfill $(SEASONS)
refresh:  ; $(PY) tasks.py refresh
build:    ; $(PY) tasks.py build
test:     ; $(PY) tasks.py test
docs:     ; $(PY) tasks.py docs
export:   ; $(PY) tasks.py export
preview:  ; $(PY) tasks.py preview
all:      ; $(PY) tasks.py all $(SEASONS)
