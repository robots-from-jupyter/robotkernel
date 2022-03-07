{ pkgs }:

(import ((import ./nix/sources.nix).pip2nix + "/release.nix") {
  inherit pkgs;
}).pip2nix
