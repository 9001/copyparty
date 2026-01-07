final: prev:
let
  fullAttrs = {
    withHashedPasswords = true;
    withCertgen = true;
    withThumbnails = true;
    withFastThumbnails = true;
    withMediaProcessing = true;
    withBasicAudioMetadata = true;
    withZeroMQ = true;
    withSFTP = true;
    withFTP = true;
    withFTPS = true;
    withTFTP = true;
    withSMB = true;
    withMagic = true;
  };

  call = attrs: final.python3.pkgs.callPackage ./copyparty ({ ffmpeg = final.ffmpeg-full; } // attrs);
in
{
  copyparty = call { stable = true; };
  copyparty-unstable = call { stable = false; };
  copyparty-full = call (fullAttrs // { stable = true; });
  copyparty-unstable-full = call (fullAttrs // { stable = false; });

  python3 = prev.python3.override {
    packageOverrides = pyFinal: pyPrev: {
      partftpy = pyFinal.callPackage ./partftpy { };
    };
  };
}
