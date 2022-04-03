# https://github.com/nmattia/niv
{ sources ? import ./sources.nix
, nixpkgs ? sources."nixpkgs"
}:

let

  overlay = _: pkgs: rec {
    jupyterWith = pkgs.callPackage ./pkgs/jupyterWith {};
    poetry2nix = pkgs.callPackage ./pkgs/poetry2nix { inherit nixpkgs; };
    jupyterLiteEnv = pkgs.callPackage ./pkgs/jupyterLiteEnv{};
  };

  pkgs = import nixpkgs {
    overlays = [ overlay ];
  };

in pkgs
