REF_NIXPKGS = branches nixos-20.03

PYTHON ?= python37
ROBOTFRAMEWORK ?= rf32
NIX_OPTIONS ?= --argstr python $(PYTHON) --argstr robotframework $(ROBOTFRAMEWORK)

.PHONY: all
all: test

nix-%:
	nix-shell $(NIX_OPTIONS) setup.nix -A develop --run "$(MAKE) $*"

.PHONY: shell
shell: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix
	nix-shell $(NIX_OPTIONS) setup.nix -A develop

env: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix
	nix-build $(NIX_OPTIONS) setup.nix -A env -o env

.PHONY: test
test: check
	pytest tests
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
	isort -rc -y src tests

###

.coverage: test

htmlcov: .coverage
	coverage html

requirements: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix

requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix: requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "pip2nix generate -r requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt --no-binary jupyter --output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"

requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt: requirements-$(ROBOTFRAMEWORK).txt
	nix-shell setup.nix $(NIX_OPTIONS) -A pip2nix --run "pip2nix generate -r requirements-$(ROBOTFRAMEWORK).txt --output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"
	@grep "pname =\|version =" requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix|awk "ORS=NR%2?FS:RS"|sed 's|.*"\(.*\)";.*version = "\(.*\)".*|\1==\2|' > requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt

.PHONY: upgrade
upgrade:
	nix-shell --pure -p cacert curl gnumake jq nix --run "make setup.nix"

.PHONY: setup.nix
setup.nix:
	@set -e pipefail; \
	echo "Updating nixpkgs @ setup.nix using $(REF_NIXPKGS)"; \
	rev=$$(curl https://api.github.com/repos/NixOS/nixpkgs-channels/$(firstword $(REF_NIXPKGS)) \
		| jq -er '.[]|select(.name == "$(lastword $(REF_NIXPKGS))").commit.sha'); \
	echo "Latest commit sha: $$rev"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz); \
	sed -i \
		-e "2s|.*|    # $(REF_NIXPKGS)|" \
		-e "3s|.*|    url = \"https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz\";|" \
		-e "4s|.*|    sha256 = \"$$sha\";|" \
		setup.nix


examples/JupyterLab.html: examples/JupyterLab.ipynb
	jupyter nbconvert \
		--to html \
		--TemplateExporter.exclude_input=True \
		--TemplateExporter.exclude_input_prompt=True \
		--TemplateExporter.exclude_output_prompt=True \
		--TemplateExporter.template_file=docs/nbconvert.tpl \
		"examples/JupyterLab.ipynb"
