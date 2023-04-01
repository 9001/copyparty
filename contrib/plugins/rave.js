/* untz untz untz untz */

(function () {

    var can, ctx, W, H, fft, buf, bars, barw, pv,
        hue = 0,
        ibeat = 0,
        beats = [9001],
        beats_url = '',
        uofs = 0,
        ops = ebi('ops'),
        raving = false,
        recalc = 0,
        cdown = 0,
        FC = 0.9,
        css = `<style>

#fft {
    position: fixed;
    top: 0;
    left: 0;
    z-index: -1;
}
body {
    box-shadow: inset 0 0 0 white;
}
#ops>a,
#path>a {
    display: inline-block;
}
/*
body.untz {
    animation: untz-body 200ms ease-out;
}
@keyframes untz-body {
	0% {inset 0 0 20em white}
	100% {inset 0 0 0 white}
}
*/
:root, html.a, html.b, html.c, html.d, html.e {
    --row-alt: rgba(48,52,78,0.2);
}
#files td {
    background: none;
}

</style>`;

    QS('body').appendChild(mknod('div', null, css));

    function rave_load() {
        console.log('rave_load');
        can = mknod('canvas', 'fft');
        QS('body').appendChild(can);
        ctx = can.getContext('2d');

        fft = new AnalyserNode(actx, {
            "fftSize": 2048,
            "maxDecibels": 0,
            "smoothingTimeConstant": 0.7,
        });
        ibeat = 0;
        beats = [9001];
        buf = new Uint8Array(fft.frequencyBinCount);
        bars = buf.length * FC;
        afilt.filters.push(fft);
        if (!raving) {
            raving = true;
            raver();
        }
        beats_url = mp.au.src.split('?')[0].replace(/(.*\/)(.*)/, '$1.beats/$2.txt');
        console.log("reading beats from", beats_url);
        var xhr = new XHR();
        xhr.open('GET', beats_url, true);
        xhr.onload = readbeats;
        xhr.url = beats_url;
        xhr.send();
    }

    function rave_unload() {
        qsr('#fft');
        can = null;
    }

    function readbeats() {
        if (this.url != beats_url)
            return console.log('old beats??', this.url, beats_url);

        var sbeats = this.responseText.replace(/\r/g, '').split(/\n/g);
        if (sbeats.length < 3)
            return;

        beats = [];
        for (var a = 0; a < sbeats.length; a++)
            beats.push(parseFloat(sbeats[a]));

        var end = beats.slice(-2),
            t = end[1],
            d = t - end[0];

        while (d > 0.1 && t < 1200)
            beats.push(t += d);
    }

    function hrand() {
        return Math.random() - 0.5;
    }

    function raver() {
        if (!can) {
            raving = false;
            return;
        }

        requestAnimationFrame(raver);
        if (!mp || !mp.au || mp.au.paused)
            return;

        if (--uofs >= 0) {
            document.body.style.marginLeft = hrand() * uofs + 'px';
            ebi('tree').style.marginLeft = hrand() * uofs + 'px';
            for (var a of QSA('#ops>a, #path>a, #pctl>a'))
                a.style.transform = 'translate(' + hrand() * uofs * 1 + 'px, ' + hrand() * uofs * 0.7 + 'px) rotate(' + Math.random() * uofs * 0.7 + 'deg)'
        }

        if (--recalc < 0) {
            recalc = 60;
            var tree = ebi('tree'),
                x = tree.style.display == 'none' ? 0 : tree.offsetWidth;

            //W = can.width = window.innerWidth - x;
            //H = can.height = window.innerHeight;
            //H = ebi('widget').offsetTop;
            W = can.width = bars;
            H = can.height = 512;
            barw = 1; //parseInt(0.8 + W / bars);
            can.style.left = x + 'px';
            can.style.width = (window.innerWidth - x) + 'px';
            can.style.height = ebi('widget').offsetTop + 'px';
        }

        //if (--cdown == 1)
        //    clmod(ops, 'untz');

        fft.getByteFrequencyData(buf);

        var imax = 0, vmax = 0;
        for (var a = 10; a < 50; a++)
            if (vmax < buf[a]) {
                vmax = buf[a];
                imax = a;
            }

        hue = hue * 0.93 + imax * 0.07;

        ctx.fillStyle = 'rgba(0,0,0,0)';
        ctx.fillRect(0, 0, W, H);
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = 'hsla(' + (hue * 2.5) + ',100%,50%,0.7)';

        var x = 0, mul = (H / 256) * 0.5;
        for (var a = 0; a < buf.length * FC; a++) {
            var v = buf[a] * mul * (1 + 0.69 * a / buf.length);
            ctx.fillRect(x, H - v, barw, v);
            x += barw;
        }

        var t = mp.au.currentTime + 0.05;

        if (ibeat >= beats.length || beats[ibeat] > t)
            return;

        while (ibeat < beats.length && beats[ibeat++] < t)
            continue;

        return untz();

        var cv = 0;
        for (var a = 0; a < 128; a++)
            cv += buf[a];

        if (cv - pv > 1000) {
            console.log(pv, cv, cv - pv);
            if (cdown < 0) {
                clmod(ops, 'untz', 1);
                cdown = 20;
            }
        }
        pv = cv;
    }

    function untz() {
        console.log('untz');
        uofs = 14;
        document.body.animate([
            { boxShadow: 'inset 0 0 1em #f0c' },
            { boxShadow: 'inset 0 0 20em #f0c', offset: 0.2 },
            { boxShadow: 'inset 0 0 0 #f0c' },
        ], { duration: 200, iterations: 1 });
    }

    afilt.plugs.push({
        "en": true,
        "load": rave_load,
        "unload": rave_unload
    });

})();
