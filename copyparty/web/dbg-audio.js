var ofun = audio_eq.apply.bind(audio_eq);
audio_eq.apply = function () {
    var ac1 = mp.ac;
    ofun();
    var ac = mp.ac,
        w = 2048,
        h = 256;

    if (!audio_eq.filters.length) {
        audio_eq.ana = null;
        return;
    }

    var can = ebi('fft_can');
    if (!can) {
        can = mknod('canvas', 'fft_can');
        can.style.cssText = 'position:absolute;left:0;bottom:5em;width:' + w + 'px;height:' + h + 'px;z-index:9001';
        document.body.appendChild(can);
        can.width = w;
        can.height = h;
    }
    var cc = can.getContext('2d');
    if (!ac)
        return;

    var ana = ac.createAnalyser();
    ana.smoothingTimeConstant = 0;
    ana.fftSize = 8192;

    audio_eq.filters[0].connect(ana);
    audio_eq.ana = ana;

    var buf = new Uint8Array(ana.frequencyBinCount),
        colw = can.width / buf.length;

    cc.fillStyle = '#fc0';
    function draw() {
        if (ana == audio_eq.ana)
            requestAnimationFrame(draw);

        ana.getByteFrequencyData(buf);

        cc.clearRect(0, 0, can.width, can.height);

        /*var x = 0, w = 1;
        for (var a = 0; a < buf.length; a++) {
            cc.fillRect(x, h - buf[a], w, h);
            x += w;
        }*/
        var mul = Math.pow(w, 4) / buf.length;
        for (var x = 0; x < w; x++) {
            var a = Math.floor(Math.pow(x, 4) / mul),
                v = buf[a];

            cc.fillRect(x, h - v, 1, v);
        }
    }
    draw();
};
audio_eq.apply();
