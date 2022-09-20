{ pkgs ? import ./nix {}
, python ? "python39"
, pythonPackages ? builtins.getAttr (python + "Packages") pkgs
, robotframework ? "rf40"
, requirements ?  ./. + "/requirements-${python}-${robotframework}.nix"
, src ? ./.
, buildInputs ? with pkgs; [ firefox geckodriver pandoc ]
, propagatedBuildInputs ? []
, postShellHook ? ""
}:

with builtins;
with pkgs;
with pkgs.lib;

let

  # Aliases map from generated requirements to available nixpkgs packages
  aliases = {
    "MarkupSafe" = "markupsafe";
    "Send2Trash" = "send2trash";
    "async-generator" = "async_generator";
    "ipython-genutils" = "ipython_genutils";
    "json5" = "pyjson5";
    "jupyter-console" = "jupyter_console";
    "jupyter-core" = "jupyter_core";
    "jupyter-server" = "jupyter_server";
    "jupyterlab-server" = "jupyterlab_server";
    "pyOpenSSL" = "pyopenssl";
  };

  # Packages that must override their respective nixpkgs versions
  override = [
    "docutils"
    "robotframework"
    "robotframework-seleniumlibrary"
    "selenium"
  ];

  # Target Python package overrides
  packageOverrides = lib.foldr lib.composeExtensions (self: super: { }) [

    # Import generated requirements not available in nixpkgs (or override them)
    (self: super:
      let
        generated = requirementsFunc self super;
      in

      # Import generated requirements not available
      (listToAttrs (map
        (name: { name = name;
                 value = getAttr name generated; })
        (filter (x: (! hasAttr x pythonPackages)) requirementsNames)
      ))
      //

      # Override nixpkgs version with version from generated requirements
      (listToAttrs (map
        (name: { name = name;
                 value = ((getAttr name super).overridePythonAttrs(old:
          let pkg = (getAttr name generated); in {
            inherit (pkg) pname version src;
          }
          //
          # Change format when package could be overriden with wheel distribution
          optionalAttrs (hasSuffix "whl" "${pkg.src}") { format = "wheel"; }));
        })
        (filter (x: (hasAttr x pythonPackages) && (elem x override)) requirementsNames)
      ))
    )

    # Map aliases required to align generated requirements with nixpkgs
    (self: super:
      (listToAttrs (map
        (name: { name = name; value = getAttr (getAttr name aliases) self; })
        (attrNames aliases)
      ))
    )

    # Disable tests for speed and changes in versions
    (self: super: lib.mapAttrs
      (name: value: (
        if lib.isDerivation value && lib.hasAttr "overridePythonAttrs" value
        then value.overridePythonAttrs (_: { doCheck = false; })
        else value
      ))
      super)

    # Whatever else is necessary to make your stuff work
    (self: super:
      {

        # Add requirements missing from nixpkgs version
        "robotframework-seleniumlibrary" = super."robotframework-seleniumlibrary".overridePythonAttrs(old: {
          propagatedBuildInputs = old.propagatedBuildInputs ++ [
            self."robotframework-pythonlibcore"
          ];
        });

        # Add requirements missing from nixpkgs version
        "selenium" = super."selenium".overridePythonAttrs(old: {
          patchPhase = "";
          propagatedBuildInputs = old.propagatedBuildInputs ++ [
            self."certifi"
            self."cryptography"
            self."pyopenssl"
            self."trio"
            self."trio-websocket"
          ];
        });

        # Fix hook after generic doCheck = false
        "flitBuildHook" = super."flitBuildHook".override { flit = self."flit"; };
      }
    )

  ];

  # Parsed setup.cfg in Nix via JSON (strings with \n are parsed into lists)
  setup_cfg = fromJSON(readFile(
    pkgs.runCommand "setup.json" { input=src + "/setup.cfg"; } ''
      ${pkgs.python3}/bin/python << EOF
      import configparser, json, re, os
      parser = configparser.ConfigParser()
      with open(os.environ.get("input"), errors="ignore",
                encoding="ascii") as fp:  # fromJSON supports ASCII only
         parser.read_file(fp)
      with open(os.environ.get("out"), "w") as fp:
        fp.write(json.dumps(dict(
          [(k, dict([(K, "\n" in V and [re.findall(r"[\w\.-]+", i)[0] for i in
                                        filter(bool, V.split("\n"))] or V)
                     for K, V in v.items()]))
           for k, v in parser._sections.items()]
        ), indent=4, sort_keys=True))
      fp.close()
      EOF
    ''
  ));

  # Helper to always return a list
  asList = name: attrs:
    if hasAttr name attrs then
      let candidate = getAttr name attrs; in
      if isList candidate then candidate else []
    else [];

  # Import all generated requirements
  requirementsFunc = import requirements {
    inherit pkgs;
    inherit (builtins) fetchurl;
    inherit (pkgs) fetchgit fetchhg;
  };

  # List package names in generated requirements requirements
  requirementsNames = attrNames (requirementsFunc {} {});

  # TargetPython with all requirements
  targetPython = (pythonPackages.python.override { inherit packageOverrides; });

in rec {

  # Shell with 'pip2nix' for resolving requirements.txt into requirements.nix
  pip2nix = mkShell {
    buildInputs = [ nix nix-prefetch-git cacert (getAttr python pkgs.pip2nix) ];
  };

  # TargetPython with all requirements
  inherit targetPython;

  # final env with packages in requirements.txt
  env = pkgs.buildEnv {
    name = "env";
    paths = [
      (targetPython.withPackages(ps: map (name: getAttr name ps) requirementsNames))
    ];
  };

  # Final package
  package = targetPython.pkgs.buildPythonPackage {
    pname = setup_cfg.metadata.name;
    version = setup_cfg.metadata.version;
    src = cleanSource src;
    doCheck = true;
    nativeBuildInputs = [ pkgs.gnumake pkgs.nix ] ++ buildInputs ++ map
      (name: getAttr name targetPython.pkgs) (asList "setup_requires" setup_cfg.options);
    checkInputs = buildInputs ++ map
      (name: getAttr name targetPython.pkgs) (asList "tests_require" setup_cfg.options);
    propagatedBuildInputs = propagatedBuildInputs ++ map
      (name: getAttr name targetPython.pkgs) (asList "install_requires" setup_cfg.options);
    postShellHook = ''
      export PYTHONPATH=$(pwd)/src:$PYTHONPATH
    '' + postShellHook;
  };

  install = targetPython.withPackages (ps: [ package ]);

  develop = package.overridePythonAttrs(old: {
    name = "${old.pname}-shell";
    nativeBuildInputs = with pkgs; [ cacert gnumake git entr nix env ]
      ++ buildInputs ++ propagatedBuildInputs;
    postShellHook = ''
      export PYTHONPATH=$(pwd)/src:$PYTHONPATH
      export JUPYTER_PATH=${install}/share/jupyter
      export JUPYTERLAB_DIR=${targetPython.pkgs.jupyterlab}/share/jupyter/lab
    '';
  });

  shell = develop;

}
