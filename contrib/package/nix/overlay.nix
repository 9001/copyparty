final: prev: {
  copyparty = final.python3.pkgs.callPackage ./copyparty {
    ffmpeg = final.ffmpeg-full;
  };

  # Dependencies
  codemirror = final.callPackage ./deps/codemirror { };
  marked = final.callPackage ./deps/marked { };
  easy-mde = final.callPackage ./deps/easy-mde { };
  busy-mp3 = final.callPackage ./deps/busy-mp3 { };
  copyparty-fonts = final.callPackage ./deps/copyparty-fonts { };
  asmcrypto = final.callPackage ./deps/asmcrypto { };
  hash-wasm = final.callPackage ./deps/hash-wasm { };
  prism = final.callPackage ./deps/prism { };

  python3 = prev.python3.override {
    packageOverrides = pyFinal: pyPrev: {
      partftpy = pyFinal.callPackage ./partftpy { };
      fusepy-copyparty = pyPrev.fusepy.overridePythonAttrs (old: {
        pname = "${old.pname}-copyparty";
        patchPhase = old.patchPhase + ''
          python3 ${./../../../scripts/uncomment.py} fuse.py
          sed -ri '/self.__critical_exception = e/d' fuse.py
          awk '/^log =/{s=0} !s; /^from traceback im/{s=1;print"from functools import partial";print"basestring = str"}' < fuse.py > temp
          awk '/LoggingMixIn:/{exit} --s<0;/self.use_ns = getattr/{s=7}' < temp > fuse.py
          awk "/if _machine =/{s=0} /'(mips|ppc|ppc64)'/{s=1} !s" < fuse.py > temp
          mv temp fuse.py
        '';
      });
    };
  };
}
