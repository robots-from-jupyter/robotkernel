{ pkgs, pythonPackages, jdk, sikulix }:

pythonPackages.buildPythonPackage rec {
  name = "${pname}-${version}";
  pname = "robotframework-SikuliLibrary";
  version = "1.0.1";
  src = pkgs.fetchurl {
    url = "mirror://pypi/r/${pname}/${name}.tar.gz";
    sha256 = "16s6247rq2afjsr751iriadya9jzh3390a6yc8lnd98d5h2m9zaz";
  };
  buildInputs = [ jdk sikulix ];
  patches = [ ./stop_remote_server.patch ];
  postPatch = ''
    jar xf ${sikulix}/libexec/sikulix/sikulix.jar sikulixlibs
    jar uf target/src/SikuliLibrary/lib/SikuliLibrary.jar sikulixlibs
  '';
}
