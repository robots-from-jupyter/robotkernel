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

  # Parse setup.cfg into Nix via JSON (strings with \n are parsed into lists)
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

  # Load generated requirements
  requirementsFunc = import requirements {
    inherit pkgs;
    inherit (builtins) fetchurl;
    inherit (pkgs) fetchgit fetchhg;
  };

  # List package names in requirements
  requirementsNames = attrNames (requirementsFunc {} {});

  # Return base name from drv name
  nameFromDrvName = name:
    let parts = tail (split "([0-9]-)" (parseDrvName name).name);
    in if length parts > 0 then elemAt parts 1 else name;

  # Merge named input list from nixpkgs drv with input list from requirements drv
  mergedInputs = old: new: inputsName: self: super:
    (attrByPath [ inputsName ] [] new) ++ map
    (x: attrByPath [ (nameFromDrvName x.name) ] x self)
    (filter (x: !isNull x) (attrByPath [ inputsName ] [] old));

  # Merge package drv from nixpkgs drv with requirements drv
  mergedPackage = old: new: self: super:
    if isString new.src
       && !isNull (match ".*\.whl" new.src)  # do not merge build inputs for wheels
       && new.pname != "wheel"               # ...
    then new.overridePythonAttrs(old: rec {
      propagatedBuildInputs =
        mergedInputs old new "propagatedBuildInputs" self super;
    })
    else old.overridePythonAttrs(old: rec {
      inherit (new) pname version src;
      name = "${pname}-${version}";
      checkInputs =
        mergedInputs old new "checkInputs" self super;
      buildInputs =
        mergedInputs old new "buildInputs" self super;
      nativeBuildInputs =
        mergedInputs old new "nativeBuildInputs" self super;
      propagatedBuildInputs =
        mergedInputs old new "propagatedBuildInputs" self super;
      propagatedNativeBuildInputs =
        mergedInputs old new "propagatedNativeBuildInputs" self super;
      doCheck = false;
    });

  # Build python with manual aliases for naming differences between world and nix
  buildPython = (pythonPackages.python.override {
    packageOverrides = self: super:
      listToAttrs (map (name: {
        name = name; value = getAttr (getAttr name aliases) super;
      }) (filter (x: hasAttr (getAttr x aliases) super) (attrNames aliases)));
  });

  # Build target python with all generated & customized requirements
  targetPython = (buildPython.override {
    packageOverrides = self: super:
      # 1) Merge packages already in pythonPackages
      let super_ = (requirementsFunc self buildPython.pkgs);  # from requirements
          results = (listToAttrs (map (name: let new = getAttr name super_; in {
        inherit name;
        value = mergedPackage (getAttr name buildPython.pkgs) new self super_;
      })
      (filter (name: hasAttr "overridePythonAttrs"
                     (if (tryEval (attrByPath [ name ] {} buildPython.pkgs)).success
                      then (attrByPath [ name ] {} buildPython.pkgs) else {}))
       requirementsNames)))
      // # 2) with packages only in requirements or disabled in nixpkgs
      (listToAttrs (map (name: { inherit name; value = (getAttr name super_); })
      (filter (name: (! ((hasAttr name buildPython.pkgs) &&
                         (tryEval (getAttr name buildPython.pkgs)).success)))
       requirementsNames)));
      in # 3) finally, apply overrides (with aliased drvs mapped back)
      (let final = (super // (results //
        (listToAttrs (map (name: {
          name = getAttr name aliases; value = getAttr name results;
        }) (filter (x: hasAttr x results) (attrNames aliases))))
      )); in (final // (overrides self final)));
    self = buildPython;
  });

  # Alias packages with different names in requirements and in nixpkgs
  aliases = {
    "jupyter-console" = "jupyter_console";
  };

  # Final overrides to fix issues all the magic above cannot fix automatically
  overrides = self: super: {
    "notebook" = let kernel_js = ./src/robotkernel/resources/kernel/kernel.js; in super."notebook".overridePythonAttrs(old: {
      postInstall = ''
        mkdir -p $out/${pythonPackages.python.sitePackages}/notebook/static/components/codemirror/mode/robotframework
        cp ${kernel_js} $out/${pythonPackages.python.sitePackages}/notebook/static/components/codemirror/mode/robotframework/robotframework.js
      '';
    });

    "aiohttp" = super."aiohttp".overridePythonAttrs(old: { doCheck = false; });

    "argon2-cffi-bindings" = super."argon2-cffi-bindings".overridePythonAttrs(old: {
      nativeBuildInputs = old.nativeBuildInputs
        ++ [ self."setuptools_scm" ];
    });

    "pillow" = super."pillow".overridePythonAttrs(old: { patches = []; });

    "pytest-xdist" = super."pytest-xdist".overridePythonAttrs(old: { doCheck = false; });

    "pytestCheckHook" = super."pytestCheckHook".override { pytest = self."pytest"; };

    "debugpy" = super."debugpy".overridePythonAttrs(old: { patches = []; });

    "pdbpp" = super."pdbpp".overridePythonAttrs(old: {
      nativeBuildInputs = old.nativeBuildInputs
        ++ [ self."setuptools_scm" ];
    });

    "selenium" = super."selenium".overridePythonAttrs(old: {
      propagatedBuildInputs = old.propagatedBuildInputs
        ++ [ self."certifi" self."cryptography" self."pyopenssl" ];
    });

  };

in rec {

  # shell with 'pip2nix' for resolving requirements.txt into requirements.nix
  pip2nix = mkShell {
    buildInputs = [ nix nix-prefetch-git cacert (getAttr python pkgs.pip2nix) ];
  };

  inherit buildPython targetPython;

  # final env with packages in requirements.txt
  env = pkgs.buildEnv {
    name = "env";
    paths = [
      (targetPython.withPackages(ps: map (name: getAttr name ps) requirementsNames))
    ];
  };

  # final package
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

  install = targetPython.withPackages (ps: [ package]);

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
