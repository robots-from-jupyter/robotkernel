{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/09195057114a0a8d112c847a9a8f52957420857d.tar.gz";
    sha256 = "0hszcsvgcphjny8j0p5inhl45ja61vjiz0csb0kx0b9lzmrafr7b";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/d3025ac35cc348d7bb233ee171629630bb4d6864.tar.gz";
    sha256 = "09czivsv81y1qydl7jnqa634bili8z9zvzsj0h3snbr8pk5dzwkj";
 })
, pythonPackages ? pkgs.python3Packages
}:

let overrides = self: super: {
  "robotframework" = super."robotframework".overridePythonAttrs(old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      pythonPackages.tkinter
    ];
  });
  "robotframework-appiumlibrary" =
  super."robotframework-appiumlibrary".overridePythonAttrs(old: {
    buildInputs = [ self."pytest-runner" ];
  });
}; in

setup {
  inherit pkgs pythonPackages overrides;
  src = ./.;
  propagatedBuildInputs = with pkgs; [
    geckodriver
    firefox
  ];
  buildInputs = with pkgs; [
    pandoc  # requierd by nbsphinx
  ];
}
