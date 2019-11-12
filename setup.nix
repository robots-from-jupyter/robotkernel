{ pkgs ? import (builtins.fetchTarball {
    # branches nixos-19.09
    url = "https://github.com/NixOS/nixpkgs-channels/archive/c75de8bc12cc7e713206199e5ca30b224e295041.tar.gz";
    sha256 = "1awipcjfvs354spzj2la1nzmi9rh2ci2mdapzf4kkabf58ilra6x";
  }) {}
, setup ? import (builtins.fetchTarball {
    # tags v3.3.0
    url = "https://github.com/nix-community/setup.nix/archive/322c73833bb54ee7e9c7f48582cdb9d8315c2456.tar.gz";
    sha256 = "1v1rgv1rl7za7ha3ngs6zap0b61z967aavh4p2ydngp44w5m2j5a";
  })
, python ? "python36"
, robotframework ? "rf32"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ? ./. + "/requirements-${python}-${robotframework}.nix"
}:

let overrides = self: super: {
# "pytest-mock" = super."pytest-mock".overridePythonAttrs(old: {
#   doCheck = false;
# });
# "json5" = super."json5".overridePythonAttrs(old: {
#   postPatch = "rm -r tests";
# });
# "RESTinstance" = super."RESTinstance".overridePythonAttrs(old: {
#   postInstall = "rm -f $out/bin/robot";
# });
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
