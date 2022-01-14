// USAGE:
//   place this file somewhere in the webroot and then
//   python3 -m copyparty --js-browser /memes/meadup.js
//
// FEATURES:
// * adds an onscreen keyboard for operating a media center remotely,
//    relies on https://github.com/9001/copyparty/blob/hovudstraum/bin/mtag/very-bad-idea.py
// * adds an interactive anime girl (if you can find the dependencies)

var hambagas = [
    "https://www.youtube.com/watch?v=pFA3KGp4GuU"
];

// keybaord,
//   onscreen keyboard by @steinuil
function initKeybaord(BASE_URL, HAMBAGA, consoleLog, consoleError) {
    document.querySelector('.keybaord-container').innerHTML = `
      <div class="keybaord-body">
        <div class="keybaord-row keybaord-row-1">
          <div class="keybaord-key" data-keybaord-key="Escape">
            esc
          </div>
          <div class="keybaord-key" data-keybaord-key="F1">
            F1
          </div>
          <div class="keybaord-key" data-keybaord-key="F2">
            F2
          </div>
          <div class="keybaord-key" data-keybaord-key="F3">
            F3
          </div>
          <div class="keybaord-key" data-keybaord-key="F4">
            F4
          </div>
          <div class="keybaord-key" data-keybaord-key="F5">
            F5
          </div>
          <div class="keybaord-key" data-keybaord-key="F6">
            F6
          </div>
          <div class="keybaord-key" data-keybaord-key="F7">
            F7
          </div>
          <div class="keybaord-key" data-keybaord-key="F8">
            F8
          </div>
          <div class="keybaord-key" data-keybaord-key="F9">
            F9
          </div>
          <div class="keybaord-key" data-keybaord-key="F10">
            F10
          </div>
          <div class="keybaord-key" data-keybaord-key="F11">
            F11
          </div>
          <div class="keybaord-key" data-keybaord-key="F12">
            F12
          </div>
          <div class="keybaord-key" data-keybaord-key="Insert">
            ins
          </div>
          <div class="keybaord-key" data-keybaord-key="Delete">
            del
          </div>
        </div>
        <div class="keybaord-row keybaord-row-2">
          <div class="keybaord-key" data-keybaord-key="\`">
            \`
          </div>
          <div class="keybaord-key" data-keybaord-key="1">
            1
          </div>
          <div class="keybaord-key" data-keybaord-key="2">
            2
          </div>
          <div class="keybaord-key" data-keybaord-key="3">
            3
          </div>
          <div class="keybaord-key" data-keybaord-key="4">
            4
          </div>
          <div class="keybaord-key" data-keybaord-key="5">
            5
          </div>
          <div class="keybaord-key" data-keybaord-key="6">
            6
          </div>
          <div class="keybaord-key" data-keybaord-key="7">
            7
          </div>
          <div class="keybaord-key" data-keybaord-key="8">
            8
          </div>
          <div class="keybaord-key" data-keybaord-key="9">
            9
          </div>
          <div class="keybaord-key" data-keybaord-key="0">
            0
          </div>
          <div class="keybaord-key" data-keybaord-key="-">
            -
          </div>
          <div class="keybaord-key" data-keybaord-key="=">
            =
          </div>
          <div class="keybaord-key keybaord-backspace" data-keybaord-key="BackSpace">
            backspace
          </div>
        </div>
        <div class="keybaord-row keybaord-row-3">
          <div class="keybaord-key keybaord-tab" data-keybaord-key="Tab">
            tab
          </div>
          <div class="keybaord-key" data-keybaord-key="q">
            q
          </div>
          <div class="keybaord-key" data-keybaord-key="w">
            w
          </div>
          <div class="keybaord-key" data-keybaord-key="e">
            e
          </div>
          <div class="keybaord-key" data-keybaord-key="r">
            r
          </div>
          <div class="keybaord-key" data-keybaord-key="t">
            t
          </div>
          <div class="keybaord-key" data-keybaord-key="y">
            y
          </div>
          <div class="keybaord-key" data-keybaord-key="u">
            u
          </div>
          <div class="keybaord-key" data-keybaord-key="i">
            i
          </div>
          <div class="keybaord-key" data-keybaord-key="o">
            o
          </div>
          <div class="keybaord-key" data-keybaord-key="p">
            p
          </div>
          <div class="keybaord-key" data-keybaord-key="[">
            [
          </div>
          <div class="keybaord-key" data-keybaord-key="]">
            ]
          </div>
          <div class="keybaord-key keybaord-enter" data-keybaord-key="Return">
            enter
          </div>
        </div>
        <div class="keybaord-row keybaord-row-4">
          <div class="keybaord-key keybaord-capslock" data-keybaord-key="HAMBAGA">
            🍔
          </div>
          <div class="keybaord-key" data-keybaord-key="a">
            a
          </div>
          <div class="keybaord-key" data-keybaord-key="s">
            s
          </div>
          <div class="keybaord-key" data-keybaord-key="d">
            d
          </div>
          <div class="keybaord-key" data-keybaord-key="f">
            f
          </div>
          <div class="keybaord-key" data-keybaord-key="g">
            g
          </div>
          <div class="keybaord-key" data-keybaord-key="h">
            h
          </div>
          <div class="keybaord-key" data-keybaord-key="j">
            j
          </div>
          <div class="keybaord-key" data-keybaord-key="k">
            k
          </div>
          <div class="keybaord-key" data-keybaord-key="l">
            l
          </div>
          <div class="keybaord-key" data-keybaord-key=";">
            ;
          </div>
          <div class="keybaord-key" data-keybaord-key="'">
            '
          </div>
          <div class="keybaord-key keybaord-backslash" data-keybaord-key="\\">
            \\
          </div>
        </div>
        <div class="keybaord-row keybaord-row-5">
          <div class="keybaord-key keybaord-lshift" data-keybaord-key="Shift_L">
            shift
          </div>
          <div class="keybaord-key" data-keybaord-key="\\">
            \\
          </div>
          <div class="keybaord-key" data-keybaord-key="z">
            z
          </div>
          <div class="keybaord-key" data-keybaord-key="x">
            x
          </div>
          <div class="keybaord-key" data-keybaord-key="c">
            c
          </div>
          <div class="keybaord-key" data-keybaord-key="v">
            v
          </div>
          <div class="keybaord-key" data-keybaord-key="b">
            b
          </div>
          <div class="keybaord-key" data-keybaord-key="n">
            n
          </div>
          <div class="keybaord-key" data-keybaord-key="m">
            m
          </div>
          <div class="keybaord-key" data-keybaord-key=",">
            ,
          </div>
          <div class="keybaord-key" data-keybaord-key=".">
            .
          </div>
          <div class="keybaord-key" data-keybaord-key="/">
            /
          </div>
          <div class="keybaord-key keybaord-rshift" data-keybaord-key="Shift_R">
            shift
          </div>
        </div>
        <div class="keybaord-row keybaord-row-6">
          <div class="keybaord-key keybaord-lctrl" data-keybaord-key="Control_L">
            ctrl
          </div>
          <div class="keybaord-key keybaord-super" data-keybaord-key="Meta_L">
            win
          </div>
          <div class="keybaord-key keybaord-alt" data-keybaord-key="Alt_L">
            alt
          </div>
          <div class="keybaord-key keybaord-spacebar" data-keybaord-key="space">
            space
          </div>
          <div class="keybaord-key keybaord-altgr" data-keybaord-key="Alt_R">
            altgr
          </div>
          <div class="keybaord-key keybaord-what" data-keybaord-key="Menu">
            menu
          </div>
          <div class="keybaord-key keybaord-rctrl" data-keybaord-key="Control_R">
            ctrl
          </div>
        </div>
        <div class="keybaord-row">
          <div class="keybaord-key" data-keybaord-key="XF86AudioLowerVolume">
            🔉
          </div>
          <div class="keybaord-key" data-keybaord-key="XF86AudioRaiseVolume">
            🔊
          </div>
          <div class="keybaord-key" data-keybaord-key="Left">
            ⬅️
          </div>
          <div class="keybaord-key" data-keybaord-key="Down">
            ⬇️
          </div>
          <div class="keybaord-key" data-keybaord-key="Up">
            ⬆️
          </div>
          <div class="keybaord-key" data-keybaord-key="Right">
            ➡️
          </div>
          <div class="keybaord-key" data-keybaord-key="Page_Up">
            PgUp
          </div>
          <div class="keybaord-key" data-keybaord-key="Page_Down">
            PgDn
          </div>
          <div class="keybaord-key" data-keybaord-key="Home">
            🏠
          </div>
          <div class="keybaord-key" data-keybaord-key="End">
            End
          </div>
        </div>
      <div>
    `;

    function arraySample(array) {
        return array[Math.floor(Math.random() * array.length)];
    }

    function sendMessage(msg) {
        return fetch(BASE_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            },
            body: "msg=" + encodeURIComponent(msg),
        }).then(
            (r) => r.text(), // so the response body shows up in network tab
            (err) => consoleError(err)
        );
    }
    const MODIFIER_ON_CLASS = "keybaord-modifier-on";
    const KEY_DATASET = "data-keybaord-key";
    const KEY_CLASS = "keybaord-key";

    const modifiers = new Set()

    function toggleModifier(button, key) {
        button.classList.toggle(MODIFIER_ON_CLASS);
        if (modifiers.has(key)) {
            modifiers.delete(key);
        } else {
            modifiers.add(key);
        }
    }

    function popModifiers() {
        let modifierString = "";

        modifiers.forEach((mod) => {
            document.querySelector("[" + KEY_DATASET + "='" + mod + "']")
                .classList.remove(MODIFIER_ON_CLASS);

            modifierString += mod + "+";
        });

        modifiers.clear();

        return modifierString;
    }

    Array.from(document.querySelectorAll("." + KEY_CLASS)).forEach((button) => {
        const key = button.dataset.keybaordKey;

        button.addEventListener("click", (ev) => {
            switch (key) {
                case "HAMBAGA":
                    sendMessage(arraySample(HAMBAGA));
                    break;

                case "Shift_L":
                case "Shift_R":

                case "Control_L":
                case "Control_R":

                case "Meta_L":

                case "Alt_L":
                case "Alt_R":
                    toggleModifier(button, key);
                    break;

                default: {
                    const keyWithModifiers = popModifiers() + key;

                    consoleLog(keyWithModifiers);

                    sendMessage("key " + keyWithModifiers)
                        .then(() => consoleLog(keyWithModifiers + " OK"));
                }
            }
        });
    });
}


// keybaord integration
(function () {
    var o = mknod('div');
    clmod(o, 'keybaord-container', 1);
    ebi('op_msg').appendChild(o);

    o = mknod('style');
    o.innerHTML = `
.keybaord-body {
	display: flex;
	flex-flow: column nowrap;
    margin: .6em 0;
}

.keybaord-row {
	display: flex;
}

.keybaord-key {
	border: 1px solid rgba(128,128,128,0.2);
	width: 41px;
	height: 40px;

	display: flex;
	justify-content: center;
	align-items: center;
}

.keybaord-key:active {
	background-color: lightgrey;
}

.keybaord-key.keybaord-modifier-on {
	background-color: lightblue;
}

.keybaord-key.keybaord-backspace {
	width: 82px;
}

.keybaord-key.keybaord-tab {
	width: 55px;
}

.keybaord-key.keybaord-enter {
	width: 69px;
}

.keybaord-key.keybaord-capslock {
	width: 80px;
}

.keybaord-key.keybaord-backslash {
	width: 88px;
}

.keybaord-key.keybaord-lshift {
	width: 65px;
}

.keybaord-key.keybaord-rshift {
	width: 103px;
}

.keybaord-key.keybaord-lctrl {
	width: 55px;
}

.keybaord-key.keybaord-super {
	width: 55px;
}

.keybaord-key.keybaord-alt {
	width: 55px;
}

.keybaord-key.keybaord-altgr {
	width: 55px;
}

.keybaord-key.keybaord-what {
	width: 55px;
}

.keybaord-key.keybaord-rctrl {
	width: 55px;
}

.keybaord-key.keybaord-spacebar {
	width: 302px;
}
`;
    document.head.appendChild(o);

    initKeybaord('/', hambagas,
        (msg) => { toast.inf(2, msg.toString()) },
        (msg) => { toast.err(30, msg.toString()) });
})();


// live2d (dumb pointless meme)
//   dependencies for this part are not tracked in git
//   so delete this section if you wanna use this file
//   (or supply your own l2d model and js)
(function () {
    var o = mknod('link');
    o.setAttribute('rel', 'stylesheet');
    o.setAttribute('href', "/bad-memes/pio.css");
    document.head.appendChild(o);

    o = mknod('style');
    o.innerHTML = '.pio-container{text-shadow:none;z-index:1}';
    document.head.appendChild(o);

    o = mknod('div');
    clmod(o, 'pio-container', 1);
    o.innerHTML = '<div class="pio-action"></div><canvas id="pio" width="280" height="500"></canvas>';
    document.body.appendChild(o);

    var remaining = 3;
    for (var a of ['pio', 'l2d', 'fireworks']) {
        import_js(`/bad-memes/${a}.js`, function () {
            if (remaining --> 1)
                return;

            o = mknod('script');
            o.innerHTML = 'var pio = new Paul_Pio({"selector":[],"mode":"fixed","hidden":false,"content":{"close":"ok bye"},"model":["/bad-memes/sagiri/model.json"]});';
            document.body.appendChild(o);
        });
    }
})();
