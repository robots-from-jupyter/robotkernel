{ pkgs ? import (builtins.fetchTarball {
    # branches nixos-19.03
    url = "https://github.com/NixOS/nixpkgs-channels/archive/96151a48dd6662fb3f84bd16bbfe8a34f59d717a.tar.gz";
    sha256 = "06cqc37yj23g3jbwvlf9704bl5dg8vrzqvs5y2q18ayg9sw61i6z";
  }) {}
, setup ? import (builtins.fetchTarball {
    # tags v3.0.3
    url = "https://github.com/nix-community/setup.nix/archive/b13b7ee5f95ba4dc050c82ed1225f40225823ec1.tar.gz";
    sha256 = "1k2d8fdlf9m0drmhg5jr0dvzw8i4ylhr7nhryfifwim5y8amhc2b";
  })
, python ? "python3"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ? ./. + "/requirements-${python}.nix"
}:

let overrides = self: super: {
  "pytest-mock" = super."pytest-mock".overridePythonAttrs(old: {
     doCheck = false;
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
