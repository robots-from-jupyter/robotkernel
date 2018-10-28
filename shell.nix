{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/09195057114a0a8d112c847a9a8f52957420857d.tar.gz";
    sha256 = "0hszcsvgcphjny8j0p5inhl45ja61vjiz0csb0kx0b9lzmrafr7b";
  }) {}
, vim ? false
, sikuli ? false
}:

with pkgs;

let self = rec {

  # kernels

  robotkernel =  import ./setup.nix {
    inherit pkgs;
    pythonPackages = pkgs.python3Packages;
  };

  pythonPackages = robotkernel.pythonPackages;

  sikulilibrary = (import ./pkgs/sikulixlibrary {
    inherit pkgs pythonPackages jdk;
    sikulix = import ./pkgs/sikulix {
      inherit stdenv fetchurl makeWrapper utillinux jre jdk opencv;
      inherit tesseract xdotool wmctrl;
    };
  });

  python_with_packages = pythonPackages.python.buildEnv.override {
    extraLibs = with pythonPackages; [
      ipykernel
      ipywidgets
    ];
  };

  robot_with_packages = buildEnv {
    name = "robotkernel";
    paths = [
      pkgs.geckodriver
      (pythonPackages.python.buildEnv.override {
        extraLibs = with pythonPackages; [
          tkinter
          ipykernel
          ipywidgets
          robotkernel.build
          RESTinstance
          robotframework-appiumlibrary
          robotframework-debuglibrary
          robotframework-faker
          robotframework-seleniumlibrary
          robotframework-selenium2library
          robotframework-selenium2screenshots
          opencv3
        ] ++ stdenv.lib.optionals sikuli [ sikulilibrary ];
      })
    ];
  };

  # extensions

  rise = pythonPackages.buildPythonPackage rec {
    pname = "rise";
    version = "5.1.0";
    name = "${pname}-${version}";
    src = pkgs.fetchurl {
      url = "mirror://pypi/${builtins.substring 0 1 pname}/${pname}/${name}.tar.gz";
      sha256 = "0b5rimnzd6zkgs7f286vr58a5rlzv275zd49xw48mn4dc06wfpz9";
    };
    buildInputs = [ pythonPackages.notebook ];
    postPatch = ''
      sed -i "s|README.md'|README.md', encoding='utf-8'|" setup.py
    '';
  };

  jupyter_nbextensions_configurator = pythonPackages.buildPythonPackage rec {
    pname = "jupyter_nbextensions_configurator";
    version = "0.3.0";
    name = "${pname}-${version}";
    src = pkgs.fetchurl {
      url = "mirror://pypi/${builtins.substring 0 1 pname}/${pname}/${name}.tar.gz";
      sha256 = "11qq1di2gas8r302xpa0h2xndd5qgrz4a77myd2bd43c0grffa6b";
    };
    doCheck = false;
    installFlags = [ "--no-dependencies" ];
    propagatedBuildInputs = with pythonPackages; [ pyyaml ];
  };

  jupyter_contrib_nbextensions = pythonPackages.buildPythonPackage rec {
    pname = "jupyter_contrib_nbextensions";
    version = "0.3.3";
    name = "${pname}-${version}";
    src = pkgs.fetchurl {
      url = "mirror://pypi/${builtins.substring 0 1 pname}/${pname}/${name}.tar.gz";
      sha256 = "0v730d5sqx6g106ii5r08mghbmbqi12pm6mpvjc0vsx703syd83f";
    };
    doCheck = false;
    installFlags = [ "--no-dependencies" ];
    propagatedBuildInputs = with pythonPackages; [ lxml ];
  };

  vim_binding = fetchFromGitHub {
    owner = "lambdalisue";
    repo = "jupyter-vim-binding";
    rev = "c9822c753b6acad8b1084086d218eb4ce69950e9";
    sha256 = "1951wnf0k91h07nfsz8rr0c9nw68dbyflkjvw5pbx9dmmzsa065j";
  };

  # notebook

  jupyter = pythonPackages.jupyter.overridePythonAttrs (old: {
    propagatedBuildInputs = old.propagatedBuildInputs ++ [
      jupyter_contrib_nbextensions
      jupyter_nbextensions_configurator
      rise
      pythonPackages.jupyterlab
    ];
  });

  jupyter_nbconfig = stdenv.mkDerivation rec {
    name = "jupyter";
    json = builtins.toJSON {
      load_extensions = {
        "rise/main" = true;
        "python-markdown/main" = true;
        "vim_binding/vim_binding" = if vim then true else false;
      };
      keys = {
        command = {
          bind = {
            "Ctrl-7" = "RISE:toggle-slide";
            "Ctrl-8" = "RISE:toggle-subslide";
            "Ctrl-9" = "RISE:toggle-fragment";
          };
        };
      };
    };
    builder = builtins.toFile "builder.sh" ''
      source $stdenv/setup
      mkdir -p $out
      cat > $out/notebook.json << EOF
      $json
      EOF
    '';
  };

  jupyter_config_dir = stdenv.mkDerivation {
    name = "jupyter";
    buildInputs = [
      python_with_packages
      robot_with_packages
      rise
      vim_binding
    ];
    builder = writeText "builder.sh" ''
      source $stdenv/setup
      mkdir -p $out/share/jupyter/nbextensions
      mkdir -p $out/share/jupyter/migrated
      ${robot_with_packages}/bin/python -m robotkernel.install --prefix=$out
      ln -s ${jupyter_nbconfig} $out/share/jupyter/nbconfig
      ln -s ${jupyter_contrib_nbextensions}/${pythonPackages.python.sitePackages}/jupyter_contrib_nbextensions/nbextensions/* $out/share/jupyter/nbextensions
      ln -s ${rise}/${pythonPackages.python.sitePackages}/rise/static $out/share/jupyter/nbextensions/rise
      ln -s ${vim_binding} $out/share/jupyter/nbextensions/vim_binding
      cat > $out/share/jupyter/jupyter_notebook_config.py << EOF
      import os
      import rise
      c.NotebookApp.ip = os.environ.get('JUPYTER_NOTEBOOK_IP', 'localhost')
      EOF

      cat > $out/share/jupyter/jupyter_nbconvert_config.py << EOF
      c = get_config()
      c.Exporter.preprocessors = ['jupyter_contrib_nbextensions.nbconvert_support.pre_pymarkdown.PyMarkdownPreprocessor']
      EOF
    '';
  };
};

in with self;

stdenv.mkDerivation rec {
  name = "jupyter";
  env = buildEnv { name = name; paths = buildInputs; };
  builder = builtins.toFile "builder.sh" ''
    source $stdenv/setup; ln -s $env $out
  '';
  buildInputs = [
    jupyter
    jupyter_config_dir
    geckodriver
  ] ++ stdenv.lib.optionals stdenv.isLinux [ bash fontconfig tini ]
    ++ stdenv.lib.optionals sikuli [ jre8 ];
  shellHook = ''
    mkdir -p $PWD/.jupyter
    export JUPYTER_CONFIG_DIR=${jupyter_config_dir}/share/jupyter
    export JUPYTER_PATH=${jupyter_config_dir}/share/jupyter
    export JUPYTER_DATA_DIR=$PWD/.jupyter
    export JUPYTER_RUNTIME_DIR=$PWD/.jupyter
    export PATH=$PATH:${robot_with_packages}/bin
  '';
}
