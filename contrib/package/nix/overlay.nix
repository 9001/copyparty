final: prev: {
  copyparty = final.python3.pkgs.callPackage ./copyparty {
    ffmpeg = final.ffmpeg-full;
  };

  python3 = prev.python3.override {
    packageOverrides = pyFinal: pyPrev: {
      partftpy = pyFinal.callPackage ./partftpy { };
    };
  };
}
