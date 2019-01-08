{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/eebd1a9263716a04689a37b6537e50801d376b5e.tar.gz";
    sha256 = "0s1fylhjqp2h4j044iwbwndgnips3nrynh2ip5ijh96kavizf2gb";
  }) {}
, setup ? import (fetchTarball {
    url = "https://github.com/datakurre/setup.nix/archive/9f8529e003ea4d2f433d2999dc50b8938548e7d0.tar.gz";
    sha256 = "15qzhz28jvgkna5zv7pj0gfnd0vcvafpckxcp850j64z7761apnm";
 })
, pythonPackages ? pkgs.python3Packages
}:

let overrides = self: super: {
  "click" = super."click".overrideDerivation(old: {
    patches = [];
  });
  "flake8" = super."flake8".overrideDerivation(old: {
    patches = [];
  });
  "graphviz" = super."graphviz".overridePythonAttrs(old: {
    buildInputs = [ pkgs.unzip ];
  });
  "iplantuml" = super."iplantuml".overridePythonAttrs(old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ [ pkgs.plantuml ];
    postPatch = ''
      sed -i "s|/usr/local/bin/plantuml.jar|${pkgs.plantuml}/lib/plantuml.jar|" iplantuml/__init__.py
    '';
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
  # building wheels require SOURCE_DATE_EPOCH
  "zest.releaser" = super."zest.releaser".overridePythonAttrs(old: {
    postInstall = ''
      for prog in $out/bin/*; do
        mv $prog $prog-python${pythonPackages.python.majorVersion}
        wrapProgram $prog-python${pythonPackages.python.majorVersion} \
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
