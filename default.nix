{ python ? "python37" }:
(import ./setup.nix { inherit python; }).package
