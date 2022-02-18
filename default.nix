{ python ? "python39" }:
(import ./setup.nix { inherit python; }).package
