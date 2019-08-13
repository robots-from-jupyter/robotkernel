{ pkgs ? import (builtins.fetchTarball {
    # branches nixos-19.03
    url = "https://github.com/NixOS/nixpkgs-channels/archive/96151a48dd6662fb3f84bd16bbfe8a34f59d717a.tar.gz";
    sha256 = "06cqc37yj23g3jbwvlf9704bl5dg8vrzqvs5y2q18ayg9sw61i6z";
  }) {}
, setup ? import (builtins.fetchTarball {
    # tags v2.1
    url = "https://github.com/datakurre/setup.nix/archive/e835238aed6a0058cf3fd0f3d6ae603532db5cb4.tar.gz";
    sha256 = "0gak3pg5nrrhxj2cws313jz80pmdys047ypnyhagvrfry5a9wa48";
  })
, python ? "python3"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ? ./. + "/requirements-${python}.nix"
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
