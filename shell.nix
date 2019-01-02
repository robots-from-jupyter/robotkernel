{ pkgs ? import (fetchTarball {
    url = "https://github.com/NixOS/nixpkgs-channels/archive/0396345b79436f54920f7eb651ab42acf2eb7973.tar.gz";
    sha256 = "10wd0wsair6dlilgaviqw2p9spgcf8qg736bzs08jha0f4zfqjs4";
  }) {}
, sikuli ? false
, vim ? false
}:

let self = rec {

  # python packages

  pythonPackages = (import ./setup.nix {
    inherit pkgs;
    pythonPackages = pkgs.python3Packages;
  }).pythonPackages;

  sikulilibrary = (import ./pkgs/sikulixlibrary {
    inherit pkgs pythonPackages;
    jdk = pkgs.jdk;
    sikulix = with pkgs; import ./pkgs/sikulix {
      inherit stdenv fetchurl makeWrapper utillinux jre jdk opencv;
      inherit tesseract xdotool wmctrl;
    };
  });

  "robotkernel" = (import ./setup.nix {
    inherit pkgs;
    pythonPackages = pkgs.python3Packages;
  }).build;

  # other packages

  vim_binding = pkgs.fetchFromGitHub {
    owner = "lambdalisue";
    repo = "jupyter-vim-binding";
    rev = "c9822c753b6acad8b1084086d218eb4ce69950e9";
    sha256 = "1951wnf0k91h07nfsz8rr0c9nw68dbyflkjvw5pbx9dmmzsa065j";
  };

  # jupyter

  jupyter = pythonPackages.jupyter.overridePythonAttrs (old: {
    propagatedBuildInputs =
    with pythonPackages; old.propagatedBuildInputs ++ [
      graphviz
      ipywidgets
      jupyter-contrib-nbextensions
      jupyter-nbextensions-configurator
      jupyterlab
      lti
      nbimporter
      opencv3
      RESTinstance
      rise
      robotframework
      robotframework-appiumlibrary
      robotframework-debuglibrary
      robotframework-faker
      robotframework-seleniumlibrary
      robotframework-seleniumscreenshots
      robotkernel
      tkinter
    ] ++ pkgs.stdenv.lib.optionals sikuli [ sikulilibrary ];
  });

  jupyter_nbconfig = pkgs.stdenv.mkDerivation rec {
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
    builder = with pkgs; builtins.toFile "builder.sh" ''
      source $stdenv/setup
      mkdir -p $out
      cat > $out/notebook.json << EOF
      $json
      EOF
    '';
  };

  jupyter_config_dir = pkgs.stdenv.mkDerivation {
    name = "jupyter";
    builder = with pythonPackages; with pkgs; writeText "builder.sh" ''
      source $stdenv/setup
      mkdir -p $out/share/jupyter/nbextensions
      mkdir -p $out/share/jupyter/migrated

      ln -s ${jupyter_nbconfig} $out/share/jupyter/nbconfig
      ln -s ${jupyter-contrib-nbextensions}/${pythonPackages.python.sitePackages}/jupyter-contrib-nbextensions/nbextensions/* $out/share/jupyter/nbextensions
      ln -s ${rise}/${pythonPackages.python.sitePackages}/rise/static $out/share/jupyter/nbextensions/rise
      ln -s ${vim_binding} $out/share/jupyter/nbextensions/vim_binding

      ${pythonPackages.python.withPackages (ps: with ps; [ robotkernel ])}/bin/python -m robotkernel.install --prefix=$out

      cat > $out/share/jupyter/jupyter_notebook_config.py << EOF
      import rise
      EOF

      cat > $out/share/jupyter/jupyter_nbconvert_config.py << EOF
      c = get_config()
      c.Exporter.preprocessors = ['jupyter_contrib_nbextensions.nbconvert_support.pre_pymarkdown.PyMarkdownPreprocessor']
      EOF
    '';
  };
};

in with self;

pkgs.stdenv.mkDerivation rec {
  name = "jupyter";
  buildInputs = [
    pkgs.firefox
    pkgs.geckodriver
    jupyter
    jupyter_config_dir
  ] ++ (with pkgs; stdenv.lib.optionals stdenv.isLinux [ bash fontconfig tini ])
    ++ (with pkgs; stdenv.lib.optionals sikuli [ jre8 ]);
  shellHook = ''
    mkdir -p $(pwd)/.jupyter
    export JUPYTER_CONFIG_DIR=${jupyter_config_dir}/share/jupyter
    export JUPYTER_PATH=${jupyter_config_dir}/share/jupyter
    export JUPYTER_DATA_DIR=$(pwd)/.jupyter
    export JUPYTER_RUNTIME_DIR=$(pwd)/.jupyter
    export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
  '';
}
