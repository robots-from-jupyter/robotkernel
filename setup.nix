{ pkgs ? import (builtins.fetchTarball {
    # branches nixos-19.03
    url = "https://github.com/NixOS/nixpkgs-channels/archive/96151a48dd6662fb3f84bd16bbfe8a34f59d717a.tar.gz";
    sha256 = "06cqc37yj23g3jbwvlf9704bl5dg8vrzqvs5y2q18ayg9sw61i6z";
  }) {}
, setup ? import (builtins.fetchTarball {
    # tags v3.1.0
    url = "https://github.com/nix-community/setup.nix/archive/129a384786f2d5985e1067e9b505f8cfc907e9fa.tar.gz";
    sha256 = "1dp9bzivqaqqc2d9bnfy6jh37rfz6mvqaqbxy34l998y0khv5fpv";
  })
, python ? "python3"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ? ./. + "/requirements-${python}.nix"
}:

let overrides = self: super: {
  "pytest-mock" = super."pytest-mock".overridePythonAttrs(old: {
    doCheck = false;
  });
  "json5" = super."json5".overridePythonAttrs(old: {
    postPatch = "rm -r tests";
  });
  "RESTinstance" = super."RESTinstance".overridePythonAttrs(old: {
    postInstall = "rm -f $out/bin/robot";
  });
}; in

setup {
  inherit pkgs pythonPackages overrides;
  src = ./.;
  requirements = requirements;
  propagatedBuildInputs = with pkgs; [
    geckodriver
    firefox
  ];
  buildInputs = with pkgs; [
    pandoc  # requierd by nbsphinx
  ];
}
