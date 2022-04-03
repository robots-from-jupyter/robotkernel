{ pkgs ? import ./nix {}
, sources ? import ./nix/sources.nix
}:

pkgs.mkShell {
  buildInputs = with pkgs; [
    gnumake
    niv
    nodejs
    nodePackages.lerna
    yarn
    poetry
    poetry2nix.cli
    jupyterLiteEnv
    twine
    (jupyterWith.jupyterlabWith {})
  ];
  shellHook = ''
    export SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt
  '';
}
