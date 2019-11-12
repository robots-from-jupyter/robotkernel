REF_NIXPKGS = branches nixos-19.09
REF_SETUPNIX = tags v3.3.0

PYTHON ?= python36
ROBOTFRAMEWORK ?= rf32
NIX_OPTIONS ?= \
  --pure \
  --argstr python $(PYTHON) \
  --argstr robotframework $(ROBOTFRAMEWORK)

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
	nix-shell -p cacert libffi nix \
		--run 'HOME="$(PWD)" NIX_CONF_DIR="$(PWD)" nix-shell --argstr python $(PYTHON) setup.nix -A pip2nix \
		--run "pip2nix generate -r requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt \
		--no-binary json5 --no-binary jupyter \
		--output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"'

requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt: requirements-$(ROBOTFRAMEWORK).txt
	nix-shell -p cacert libffi nix \
		--run 'HOME="$(PWD)" NIX_CONF_DIR="$(PWD)" nix-shell \
		--argstr python $(PYTHON) \
		--argstr robotframework $(ROBOTFRAMEWORK) setup.nix -A pip2nix \
		--run "pip2nix generate -r requirements-$(ROBOTFRAMEWORK).txt \
		--output=requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix"'
	@grep "pname =\|version =" requirements-$(PYTHON)-$(ROBOTFRAMEWORK).nix|awk "ORS=NR%2?FS:RS"|sed 's|.*"\(.*\)";.*version = "\(.*\)".*|\1==\2|' > requirements-$(PYTHON)-$(ROBOTFRAMEWORK).txt

.PHONY: upgrade
upgrade:
	nix-shell --pure -p curl gnumake jq nix --run "make setup.nix"

upgrade-nix: upgrade-nix-nixpkgs upgrade-nix-setupnix

upgrade-nix-nixpkgs:
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

upgrade-nix-setupnix:
	@echo "Updating setup @ setup.nix using $(REF_SETUPNIX)"; \
	rev=$$(curl https://api.github.com/repos/nix-community/setup.nix/$(firstword $(REF_SETUPNIX)) \
		| jq -er '.[] | select(.name == "$(lastword $(REF_SETUPNIX))").commit.sha'); \
	echo "Latest commit sha: $$rev"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/nix-community/setup.nix/archive/$$rev.tar.gz); \
	sed -i \
		-e "7s|.*|    # $(REF_SETUPNIX)|" \
		-e "8s|.*|    url = \"https://github.com/nix-community/setup.nix/archive/$$rev.tar.gz\";|" \
		-e "9s|.*|    sha256 = \"$$sha\";|" \
		setup.nix
