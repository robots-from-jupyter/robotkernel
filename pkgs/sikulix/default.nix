{ stdenv, fetchurl, makeWrapper, utillinux, jre, jdk, opencv,
  tesseract, xdotool, wmctrl }:

stdenv.mkDerivation rec {
  name = "sikulix-${version}";
  version = "1.1.1";

  ide = fetchurl {
    url = "https://oss.sonatype.org/content/groups/public/com/sikulix/sikulixsetupIDE/${version}-SNAPSHOT/sikulixsetupIDE-${version}-20170329.090402-140-forsetup.jar";
    sha256 = "04hf7awhz7ndxbnif07v3n1sgq03qpk52s298mkdnw86803spbz8";
  };

  api = fetchurl {
    url = "https://oss.sonatype.org/content/groups/public/com/sikulix/sikulixsetupAPI/${version}-SNAPSHOT/sikulixsetupAPI-${version}-20170329.090133-142-forsetup.jar";
    sha256 = "0779ryv0qaqpcpl5ana36q98zika9dnx2j29sdabvy2ap01pwb66";
  };

  jython = fetchurl {
    url = "http://repo1.maven.org/maven2/org/python/jython-standalone/2.7.1/jython-standalone-2.7.1.jar";
    sha256 = "0jwc4ly75cna78blnisv4q8nfcn5s0g4wk7jf4d16j0rfcd0shf4";
  };

  jruby = fetchurl {
    url = "http://repo1.maven.org/maven2/org/jruby/jruby-complete/1.7.22/jruby-complete-1.7.22.jar";
    sha256 = "1pvmn10lb873i0fsxn4mwxca2r476qrxwhdiz4n5qlfrnxy809id";
  };

  native = fetchurl {
    url = "https://oss.sonatype.org/content/groups/public/com/sikulix/sikulixlibslux/${version}-SNAPSHOT/sikulixlibslux-${version}-20170329.085133-153.jar";
    sha256 = "0ssdcp43wsigx9x5gigy266a2ls4wxqh3m90i55jpi59a3axqzmq";
  };

  setup = fetchurl {
    url = "https://launchpad.net/sikuli/sikulix/${version}/+download/sikulixsetup-${version}.jar";
    sha256 = "0rwll7rl51ry8nirl91znsvjh6s5agal0wxzqpisr907g1l1vp12";
  };

  buildInputs = [ makeWrapper jre jdk opencv tesseract xdotool wmctrl ];

  unpackPhase = "true";

  NIX_CFLAGS_COMPILE = "-ltesseract -lopencv_core -lopencv_highgui -lopencv_imgproc -I${jdk}/include";
  buildPhase = ''
    cp $ide sikulixsetupIDE-${version}.jar
    cp $api sikulixsetupAPI-${version}.jar
    cp $jython jython-standalone-2.7.1.jar
    cp $jruby jruby-complete-1.7.22.jar
    cp $native sikulixlibslux-${version}.jar
    cp $setup sikulixsetup-${version}.jar

    jar xf $native srcnativelibs
    mods=
    for mod in cvgui.cpp finder.cpp pyramid-template-matcher.cpp \
      sikuli-debug.cpp tessocr.cpp vision.cpp visionJAVA_wrap.cxx
    do
      echo ----- $mod
      g++ -c -O3 -fPIC -MMD -MP \
        -MF $mod.o.d \
        -o $mod.o \
        ./srcnativelibs/Vision/$mod
      mods="$mods $mod.o"
    done
    mkdir -p sikulixlibs/linux/libs64
    g++ -shared -s -fPIC -dynamic $mods \
    -o sikulixlibs/linux/libs64/libVisionProxy.so
    jar uf sikulixlibslux-${version}.jar \
      sikulixlibs/linux/libs64/libVisionProxy.so
    rm -r *.o *.o.d srcnativelibs sikulixlibs

    mkdir tmp
    java -Djava.io.tmpdir=$(pwd)/tmp -Duser.home=$(pwd) -jar sikulixsetup-${version}.jar options 1.1
  '';

  installPhase = ''
    cat *.txt
    mkdir -p $out/libexec/sikulix
    cp -R sikulix.jar runsikulix $out/libexec/sikulix
    makeWrapper $out/libexec/sikulix/runsikulix $out/bin/sikulix \
      --prefix PATH : "${jre}/bin:${xdotool}/bin:${wmctrl}/bin"
  '';

  meta = with stdenv.lib; {
    description = "Sikuli automates anything you see on the screen.";
    homepage = http://www.sikulix.com/;
    license = with licenses; [ mit ];
    maintainers = with maintainers; [];
    platforms = with platforms; linux;
  };
}
