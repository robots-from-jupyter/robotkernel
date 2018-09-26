{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/29660a208552a1e32f872333d6eb52e13226effa.tar.gz";
    sha256 = "1rv87f7kqrnl16m64h4148c6nnnl3r3m860d0f08dwk1d5f6ffmd";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/d991abe23efde4a0bc5de2a0b4672cca0126c151.tar.gz";
    sha256 = "0zglrif1hncs84ia28m03ca324y8aqnjqygzsji7x0bnfn77hpqm";
 })
, pythonPackages ? pkgs.python3Packages
}:

setup {
  inherit pkgs pythonPackages;
  src = ./.;
  propagatedBuildInputs = with pkgs; [
    geckodriver
  ];
}
