final: prev: {
  copyparty = final.python3.pkgs.callPackage ./copyparty {
    ffmpeg = final.ffmpeg-full;
  };

  # Dependencies
  codemirror = final.callPackage ./deps/codemirror { };
  marked = final.callPackage ./deps/marked { };
  easy-mde = final.callPackage ./deps/easy-mde { };

  python3 = prev.python3.override {
    packageOverrides = pyFinal: pyPrev: {
      partftpy = pyFinal.callPackage ./partftpy { };
    };
  };
}
