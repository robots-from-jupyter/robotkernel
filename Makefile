requirements.nix: requirements.txt
	@nix-shell -p libffi \
	--run 'nix-shell setup.nix -A pip2nix \
	--run "pip2nix generate -r requirements.txt --output=requirements.nix"'

.PHONY: freeze
freeze:
	@grep "name" requirements.nix |grep -Eo "\"(.*)\""|grep -Eo "[^\"]+"|sed -r "s|-([0-9\.]+)|==\1|g"

.PHONY: upgrade
upgrade:
	@echo "Updating nixpkgs unstable revision"; \
	rev=$$(curl https://api.github.com/repos/NixOS/nixpkgs-channels/branches/nixos-unstable|jq -r .commit.sha); \
	echo "Updating nixpkgs $$rev hash"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz); \
	sed -i "2s|.*|    url = \"https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz\";|" setup.nix; \
	sed -i "3s|.*|    sha256 = \"$$sha\";|" setup.nix; \
	sed -i "2s|.*|    url = \"https://github.com/NixOS/nixpkgs-channels/archive/$$rev.tar.gz\";|" shell.nix; \
	sed -i "3s|.*|    sha256 = \"$$sha\";|" shell.nix
	@echo "Updating setup.nix version"; \
	rev=$$(curl https://api.github.com/repos/datakurre/setup.nix/branches/master|jq -r ".commit.sha"); \
	echo "Updating setup.nix $$rev hash"; \
	sha=$$(nix-prefetch-url --unpack https://github.com/datakurre/setup.nix/archive/$$rev.tar.gz); \
	sed -i "6s|.*|    url = \"https://github.com/datakurre/setup.nix/archive/$$rev.tar.gz\";|" setup.nix; \
	sed -i "7s|.*|    sha256 = \"$$sha\";|" setup.nix
