{ poetry2nix }:

poetry2nix.mkPoetryEnv {
  projectDir = ./.;
  overrides = poetry2nix.overrides.withDefaults (self: super: {
    jupyterlite = super.jupyterlite.overridePythonAttrs(old: {
      nativeBuildInputs = [ self.flit-core ];
    });
  });
}
