REF_NIXPKGS = branches nixos-19.03
REF_SETUPNIX = tags v2.1

PYTHON ?= python3
NIX_OPTIONS ?= --pure --argstr python $(PYTHON)

.PHONY: all
all: test

nix-%:
	nix-shell $(NIX_OPTIONS) setup.nix -A develop --run "$(MAKE) $*"

.PHONY: shell
shell: requirements-$(PYTHON).nix
	nix-shell $(NIX_OPTIONS) setup.nix -A develop

env: requirements-$(PYTHON).nix
	nix-build $(NIX_OPTIONS) setup.nix -A env -o env

.PHONY: test
test: check
	pytest --cov={{ cookiecutter.project_slug }} tests

.PHONY: check
check:
	black -t py37 --check src
	pylama src tests

build: result

result: requirements-$(PYTHON).nix
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

.PHONY: watch
watch:
	find src | entr -r $(CMD)

.PHONY: serve
serve:
	$(CMD) \
		--username=$(CMD) \
		--call-exchange=$(CMD) \
		--service-queue=$(CMD) \
		--prefetch-count=2 \
		--on-error=reject

###

.coverage: test

htmlcov: .coverage
	coverage html

requirements: requirements-$(PYTHON).nix

requirements-$(PYTHON).nix: requirements-$(PYTHON).txt
	nix-shell --pure -p cacert libffi nix \
		--run 'HOME="$(PWD)" NIX_CONF_DIR="$(PWD)" nix-shell --argstr python $(PYTHON) setup.nix -A pip2nix \
		--run "pip2nix generate -r requirements-$(PYTHON).txt \
		--output=requirements-$(PYTHON).nix"'

requirements-$(PYTHON).txt: requirements.txt
	nix-shell --pure -p cacert libffi nix \
		--run 'HOME="$(PWD)" NIX_CONF_DIR="$(PWD)" nix-shell --argstr python $(PYTHON) setup.nix -A pip2nix \
		--run "pip2nix generate -r requirements.txt \
		--output=requirements-$(PYTHON).nix"'
	@grep "name" requirements-$(PYTHON).nix |grep -Eo "\"(.*)\""|grep -Eo "[^\"]+"|sed -r "s|-([0-9\.]+)|==\1|g"|grep -v "setuptools=" > requirements-$(PYTHON).txt

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
	rev=$$(curl https://api.github.com/repos/datakurre/setup.nix/$(firstword $(REF_SETUPNIX)) \
		| jq -er '.[] | select(.name == "$(lastword $(REF_SETUPNIX))").commit.sha'); \
	echo "Latest commit sha: $$rev"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/datakurre/setup.nix/archive/$$rev.tar.gz); \
	sed -i \
		-e "7s|.*|    # $(REF_SETUPNIX)|" \
		-e "8s|.*|    url = \"https://github.com/datakurre/setup.nix/archive/$$rev.tar.gz\";|" \
		-e "9s|.*|    sha256 = \"$$sha\";|" \
		setup.nix
