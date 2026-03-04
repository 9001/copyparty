due to legal reasons, the copyparty [docker image](https://github.com/9001/copyparty/blob/hovudstraum/scripts/docker) and [bootable flashdrive](https://a.ocv.me/pub/stuff/edcd001/enterprise-edition/) are not able to decode and display images and videos which were made using certain codecs

* specifically, photos and videos taken with iphones will not work, and perhaps some samsung phones, idk
* this also includes thumbnails thereof

I suggest you stop reading at this point, unless you want to share my frustration, in which case please do continue


## why hevc is not included

the following is my understanding, which is probably wrong because [I anal](https://en.wikipedia.org/wiki/IANAL)

* the h265 codec, also known as h.265 and hevc, is patent-encumbered and legally problematic to distribute;
  * there are several patent-pools of patent-holders with conflicting and unclear requirements
  * even FOSS is not exempt from demands of payment; https://en.wikipedia.org/wiki/High_Efficiency_Video_Coding#Provision_for_costless_software
  * I have no idea how "number of sales" maps to FOSS, but copyparty doesn't have telemetry so it would be impossible to satisfy the requirements either way
* due to this, both chrome and firefox refuse to add a built-in decoder for hevc; https://caniuse.com/hevc
  * and while I haven't discussed this with a lawyer, I presume the reason is they did
* most heif/heic images are hevc, meaning they are equally troublesome
* safari is the only webbrowser willing to decode and display heif/heic photos, for self-inflicted reasons https://caniuse.com/heif

and anyways there's no reason to use hevc in the first place because [av1](https://en.wikipedia.org/wiki/AV1) gives higher quality at a smaller filesize, is entirely free, and avif (its heif counterpart) is widely supported across all browsers: https://caniuse.com/avif


## why only the docker and flashdrive images are affected

supposedly, royalties is like a jigsaw puzzle, where whoever lays down the last piece wins the responsibility of dealing with that mess -- and because the docker-image has everything bundled as one big ball of software, that might(?) be a problem...idk, i anal

so because ffmpeg is the component that handles everything regarding hevc, only the packages which include ffmpeg are affected, which means the docker-image and bootable-flashdrive-image

if you use or install copyparty in any other way, then you are in charge of obtaining and providing an ffmpeg for copyparty to use, and thus nothing has changed


## how hevc support was removed

the regular ffmpeg package from the alpinelinux repos was replaced with a [custom ffmpeg build](https://github.com/9001/copyparty/tree/hovudstraum/scripts/docker/base) where the hevc decoder was physically stripped out, meaning hevc is not just "disabled", but entirely removed from all official copyparty distributions

oh and the aac support has also been tampered with; now only AAC-LC can be decoded, which is fine because that's like 99% of all aac files (nobody uses HE-AAC or AAC-LD), and LC-AAC has become royalty-free in all relevant parts of the world at this point

and any traces of vvc was also stripped out because that codec was dead on arrival, unable to compete with av1 (and soon av2)

the silver lining is that this has made the docker images *much* smaller; the `ac` image is now half the size -- it went from 67 to 35 MiB gzipped, from 195 to 99 MiB installed, which is nice


## how to enable hevc support

all I can say is good luck; I legally cannot help you with that

see, here's the fun part -- apparently I'm not allowed to assist with a technical explanation on how it could be done, because that would "facilitate access" as they call it?? but all copyparty does is call `ffmpeg` to generate the thumbnail; copyparty doesn't even know or care what "hevc" is; this is all purely on the ffmpeg side of things -- so technically none of this is even related to copyparty itself in the first place... ah whatever

man I just wanna write software, I hate this

pain peko
