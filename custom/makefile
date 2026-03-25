compile:
	yq eval capslock.yml -o=json > capslock.json

install: compile
	mkdir -p $$HOME/.config/karabiner/assets/complex_modifications/
	cp capslock.json $$HOME/.config/karabiner/assets/complex_modifications/

sync: compile
	mkdir -p $$HOME/.local/bin
	cp toggle_app.sh $$HOME/.local/bin/toggle_app
	cp toggle_espanso_search.sh $$HOME/.local/bin/toggle_espanso_search
	chmod +x $$HOME/.local/bin/toggle_app $$HOME/.local/bin/toggle_espanso_search
	python3 sync_karabiner.py

all:
	mkdir -p $$HOME/.config/karabiner/
	cp karabiner.json $$HOME/.config/karabiner/

.PHONY: compile install sync all