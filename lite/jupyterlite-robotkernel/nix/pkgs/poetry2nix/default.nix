{ nixpkgs }:

import ((import ./nix/sources.nix).poetry2nix + "/default.nix") {
  pkgs = import nixpkgs { overlays = []; };
  poetry = (import nixpkgs {}).poetry;
}
