{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/ef450efb9df5260e54503509d2fd638444668713.tar.gz";
    sha256 = "1k9f3n2pmdh7sap79c8nqpz7cjx9930fcpk27pvp6lwmr4qigmxg";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/53dee902050e2f3d57619ea78dcc19578640b055.tar.gz";
    sha256 = "0w4zh0xf05kd5i5pqx2ki78x5n2mhxrwi20wpv3zhlfgydxqwrrn";
  })
, pythonPackages ? pkgs.python3Packages
}:

setup {
  inherit pkgs pythonPackages;
  src = ./.;
  propagatedBuildInputs = with pkgs; [
    geckodriver
    pythonPackages.opencv3
  ];
}
