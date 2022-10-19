REF_NIXPKGS = branches nixos-20.03

PYTHON ?= python39
ROBOTFRAMEWORK ?= rf40
NIX_OPTIONS ?= --argstr python $(PYTHON) --argstr robotframework $(ROBOTFRAMEWORK)

.PHONY: all
all: test

cachix:
	nix-store --query --references $$(nix-instantiate shell.nix)|xargs nix-store --realise|xargs nix-store --query --requisites|cachix push robots-from-jupyter

nix-%:
	nix-shell $(NIX_OPTIONS) setup.nix -A develop --run "$(MAKE) $*"

.PHONY: shell
shell: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix
	nix-shell $(NIX_OPTIONS) setup.nix -A develop

env: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix
	nix-build $(NIX_OPTIONS) setup.nix -A env -o env

.PHONY: test
test: check
	PYTHONPATH=$(PYTHONPATH):$(PWD)/src pytest tests
	# pytest --cov=robotkernel tests

.PHONY: check
check:
	black -t py37 --check src
	pylama src tests

build: result

result: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix
	nix-build $(NIX_OPTIONS) setup.nix -A bdist_wheel

.PHONY: clean
clean:
	rm -rf .cache env result

.PHONY: coverage
coverage: htmlcov

.PHONY: format
format:
	black -t py37 src tests
	isort src tests

###

.coverage: test

htmlcov: .coverage
	coverage html

.PHONY: requirements-all
requirements-all:
	ROBOTFRAMEWORK=rf31 make requirements
	ROBOTFRAMEWORK=rf32 make requirements
	ROBOTFRAMEWORK=rf40 make requirements
	ROBOTFRAMEWORK=rf41 make requirements
	ROBOTFRAMEWORK=rf50 make requirements
	ROBOTFRAMEWORK=rf51 make requirements
	ROBOTFRAMEWORK=rf60 make requirements

requirements: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix

requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "pip2nix generate -r requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt --no-binary jupyter --output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"

requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt: requirements-$(ROBOTFRAMEWORK).txt
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "pip2nix generate -r requirements-$(ROBOTFRAMEWORK).txt --output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"
	@grep "pname =\|version =" requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix|awk "ORS=NR%2?FS:RS"|sed 's|.*"\(.*\)";.*version = "\(.*\)".*|\1==\2|' > requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt

examples/JupyterLab.html: examples/JupyterLab.ipynb
	jupyter nbconvert \
		--to html \
		--TemplateExporter.exclude_input=True \
		--TemplateExporter.exclude_input_prompt=True \
		--TemplateExporter.exclude_output_prompt=True \
		--TemplateExporter.template_file=docs/nbconvert.tpl \
		"examples/JupyterLab.ipynb"
