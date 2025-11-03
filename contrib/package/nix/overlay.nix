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

  python3 = prev.python3.override {
    packageOverrides = pyFinal: pyPrev: {
      partftpy = pyFinal.callPackage ./partftpy { };
    };
  };
}
