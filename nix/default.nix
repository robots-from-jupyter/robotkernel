# https://github.com/nmattia/niv
{ sources ? import ./sources.nix
, nixpkgs ? sources."nixpkgs-22.05"
}:

let

  nixpkgs_20_09 = import sources."nixpkgs-20.09" {};
  nixpkgs_unstable = import sources."nixpkgs-unstable" {};

  overlay = _: pkgs: {
    pip2nix = nixpkgs_20_09.callPackage ./pkgs/pip2nix {};
    inherit (nixpkgs_unstable) geckodriver;
  };

  pkgs = import nixpkgs {
    overlays = [ overlay ];
  };

in pkgs
