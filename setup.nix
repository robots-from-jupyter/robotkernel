{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/0396345b79436f54920f7eb651ab42acf2eb7973.tar.gz";
    sha256 = "10wd0wsair6dlilgaviqw2p9spgcf8qg736bzs08jha0f4zfqjs4";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/9f8529e003ea4d2f433d2999dc50b8938548e7d0.tar.gz";
    sha256 = "15qzhz28jvgkna5zv7pj0gfnd0vcvafpckxcp850j64z7761apnm";
 })
, pythonPackages ? pkgs.python3Packages
}:

let overrides = self: super: {
  "flake8" = super."flake8".overrideDerivation(old: {
    patches = [];
  });
  "graphviz" = super."graphviz".overridePythonAttrs(old: {
    buildInputs = [ pkgs.unzip ];
  });
  "robotframework" = super."robotframework".overridePythonAttrs(old: {
    buildInputs = [ pkgs.unzip ];
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      pythonPackages.tkinter
    ];
  });
  "robotframework-appiumlibrary" =
  super."robotframework-appiumlibrary".overridePythonAttrs(old: {
    buildInputs = [ self."pytest-runner" ];
  });
  "simplegeneric" = super."simplegeneric".overridePythonAttrs(old: {
    buildInputs = [ pkgs.unzip ];
  });
  "testfixtures" = super."testfixtures".overrideDerivation(old: {
    patches = [];
  });
  # Patches to tweak around bad archive at Cachix
  "docutils" = super."docutils".overrideDerivation(old: {
    name = "${old.name}-2019-01-01";
  });
  "selenium" = super."selenium".overrideDerivation(old: {
    name = "${old.name}-2019-01-01";
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
