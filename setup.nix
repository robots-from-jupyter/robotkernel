{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/3a4ffdd38b56801ce616aa08791121d36769e884.tar.gz";
    sha256 = "1vfmmd88x4rmgrz95xzr67xpmp1cqbrk6cfdadxv8ifqk0gsbrm7";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/a05ef605ae476a07ba1f8b0c2e1ce95d0eca8355.tar.gz";
    sha256 = "0ih9ccy54hcij7z49mfxpyvl1wdsh00kr9714scza9b101s4gpap";
 })
, pythonPackages ? pkgs.python3Packages
}:

let overrides = self: super: {
  "click" = super."click".overrideDerivation(old: {
    patches = [];
  });
  "flake8" = super."flake8".overrideDerivation(old: {
    buildInputs = old.buildInputs ++ [ self."pytest-runner" ];
    patches = [];
  });
# "graphviz" = super."graphviz".overrideDerivation(old: {
#   nativeBuildInputs = [ pkgs.unzip ];
# });
  "graphviz" = pythonPackages.graphviz;
  "iplantuml" = super."iplantuml".overridePythonAttrs(old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ [ pkgs.plantuml ];
    postPatch = ''
      sed -i "s|/usr/local/bin/plantuml.jar|${pkgs.plantuml}/lib/plantuml.jar|" iplantuml/__init__.py
    '';
  });
  "robotframework" = super."robotframework".overridePythonAttrs(old: {
    nativeBuildInputs = [ pkgs.unzip ];
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      pythonPackages.tkinter
    ];
  });
  "robotframework-appiumlibrary" =
  super."robotframework-appiumlibrary".overridePythonAttrs(old: {
    buildInputs = [ self."pytest-runner" ];
  });
  "simplegeneric" = super."simplegeneric".overridePythonAttrs(old: {
    nativeBuildInputs = [ pkgs.unzip ];
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
  # building wheels require SOURCE_DATE_EPOCH
  "zest.releaser" = super."zest.releaser".overridePythonAttrs(old: {
    postInstall = ''
      for prog in $out/bin/*; do
        mv $prog $prog-python${pythonPackages.python.pythonVersion}
        wrapProgram $prog-python${pythonPackages.python.pythonVersion} \
          --set SOURCE_DATE_EPOCH 315532800
      done
    '';
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
