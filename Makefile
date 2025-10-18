# system python interpreter. used only to create virtual environment
PY = python3
VENV = venv
BIN=$(VENV)/bin

# make it work on windows too
ifeq ($(OS), Windows_NT)
    BIN=$(VENV)\Scripts
    PY=python
endif

$(VENV):
	$(PY) -m venv $(VENV)
ifeq ($(OS), Windows_NT)
	$(VENV)\Scripts\pip.exe install -r requirements.txt
else
	$(VENV)/bin/pip install -r requirements.txt
endif

.PHONY: run clean
run: $(VENV)
ifeq ($(OS), Windows_NT)
	$(VENV)\Scripts\streamlit.exe run analyze.py
else
	$(VENV)/bin/streamlit run analyze.py
endif

clean:
ifeq ($(OS), Windows_NT)
	rmdir /s /q $(VENV)
else
	rm -rf $(VENV)
endif
