{ pkgs ? import (builtins.fetchTarball {
    # branches nixos-19.09
    url = "https://github.com/NixOS/nixpkgs-channels/archive/c75de8bc12cc7e713206199e5ca30b224e295041.tar.gz";
    sha256 = "1awipcjfvs354spzj2la1nzmi9rh2ci2mdapzf4kkabf58ilra6x";
  }) {}
, setup ? import (builtins.fetchTarball {
    # tags v3.4.0
    url = "https://github.com/nix-community/setup.nix/archive/60ea39a442cbcb446dcc53be395c90764a7019bc.tar.gz";
    sha256 = "0rk5flzwfgw5wwp4hc9lmihc499shq82gbswsz8vb9fdsbnv12h1";
  })
, python ? "python36"
, robotframework ? "rf32"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, requirements ? { pkgs, fetchurl, fetchgit, fetchhg }:
  let generated = import (./. + "/requirements-${python}-${robotframework}.nix")
    { inherit pkgs fetchurl fetchgit fetchhg; };
  in self: super: generated self super // (with pythonPackages; {
    "matplotlib" = buildPythonPackage {
      inherit (matplotlib) pname version src;
    };
  })
}:

let overrides = self: super: {
  "fancycompleter" = super."fancycompleter".overridePythonAttrs(old: {
    nativeBuildInputs = [
      self."setuptools-scm"
    ];
  });
  "json5" = super."json5".overridePythonAttrs(old: {
    postInstall = "rm -r $out/${self.python.sitePackages}/tests";
  });
  "pdbpp" = super."pdbpp".overridePythonAttrs(old: {
    nativeBuildInputs = [
      self."setuptools-scm"
    ];
  });
  "robotframework-jupyterlibrary" = super."robotframework-jupyterlibrary".overridePythonAttrs(old: {
    src = builtins.fetchurl {  # master 2019-12-05
      url = "https://github.com/robots-from-jupyter/robotframework-jupyterlibrary/archive/6a9a8a2c844bf6f435ed806216afe501f0dd0ca2.tar.gz";
      sha256 = "b750286b3d13411002f10094884b1963b54f45901dfa2fcd40703bd23c85f455";
    };
    format = "setuptools";
  });
  "RESTinstance" = super."RESTinstance".overridePythonAttrs(old: {
    postInstall = "rm -f $out/bin/robot";
  });
}; in

let self = setup {
  inherit pkgs pythonPackages overrides;
  src = ./.;
  requirements = requirements;
  propagatedBuildInputs = with pkgs; [
    geckodriver
    firefox
  ];
  buildInputs = with pkgs; [
    pandoc  # required by nbsphinx
  ];
}; in self // {
  shell = self.shell.overridePythonAttrs(old: {
    postShellHook = ''
      export JUPYTER_PATH=${self.install}/share/jupyter
      export JUPYTERLAB_DIR=${self.pythonPackages.jupyterlab}/share/jupyter/lab
    '';
  });
}
