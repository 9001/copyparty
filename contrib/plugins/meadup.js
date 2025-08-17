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

// keyboard,
//   onscreen keyboard by @steinuil
function initKeyboard(BASE_URL, HAMBAGA, consoleLog, consoleError) {
    document.querySelector('.keyboard-container').innerHTML = `
      <div class="keyboard-body">
        <div class="keyboard-row keyboard-row-1">
          <div class="keyboard-key" data-keyboard-key="Escape">
            esc
          </div>
          <div class="keyboard-key" data-keyboard-key="F1">
            F1
          </div>
          <div class="keyboard-key" data-keyboard-key="F2">
            F2
          </div>
          <div class="keyboard-key" data-keyboard-key="F3">
            F3
          </div>
          <div class="keyboard-key" data-keyboard-key="F4">
            F4
          </div>
          <div class="keyboard-key" data-keyboard-key="F5">
            F5
          </div>
          <div class="keyboard-key" data-keyboard-key="F6">
            F6
          </div>
          <div class="keyboard-key" data-keyboard-key="F7">
            F7
          </div>
          <div class="keyboard-key" data-keyboard-key="F8">
            F8
          </div>
          <div class="keyboard-key" data-keyboard-key="F9">
            F9
          </div>
          <div class="keyboard-key" data-keyboard-key="F10">
            F10
          </div>
          <div class="keyboard-key" data-keyboard-key="F11">
            F11
          </div>
          <div class="keyboard-key" data-keyboard-key="F12">
            F12
          </div>
          <div class="keyboard-key" data-keyboard-key="Insert">
            ins
          </div>
          <div class="keyboard-key" data-keyboard-key="Delete">
            del
          </div>
        </div>
        <div class="keyboard-row keyboard-row-2">
          <div class="keyboard-key" data-keyboard-key="\`">
            \`
          </div>
          <div class="keyboard-key" data-keyboard-key="1">
            1
          </div>
          <div class="keyboard-key" data-keyboard-key="2">
            2
          </div>
          <div class="keyboard-key" data-keyboard-key="3">
            3
          </div>
          <div class="keyboard-key" data-keyboard-key="4">
            4
          </div>
          <div class="keyboard-key" data-keyboard-key="5">
            5
          </div>
          <div class="keyboard-key" data-keyboard-key="6">
            6
          </div>
          <div class="keyboard-key" data-keyboard-key="7">
            7
          </div>
          <div class="keyboard-key" data-keyboard-key="8">
            8
          </div>
          <div class="keyboard-key" data-keyboard-key="9">
            9
          </div>
          <div class="keyboard-key" data-keyboard-key="0">
            0
          </div>
          <div class="keyboard-key" data-keyboard-key="-">
            -
          </div>
          <div class="keyboard-key" data-keyboard-key="=">
            =
          </div>
          <div class="keyboard-key keyboard-backspace" data-keyboard-key="BackSpace">
            backspace
          </div>
        </div>
        <div class="keyboard-row keyboard-row-3">
          <div class="keyboard-key keyboard-tab" data-keyboard-key="Tab">
            tab
          </div>
          <div class="keyboard-key" data-keyboard-key="q">
            q
          </div>
          <div class="keyboard-key" data-keyboard-key="w">
            w
          </div>
          <div class="keyboard-key" data-keyboard-key="e">
            e
          </div>
          <div class="keyboard-key" data-keyboard-key="r">
            r
          </div>
          <div class="keyboard-key" data-keyboard-key="t">
            t
          </div>
          <div class="keyboard-key" data-keyboard-key="y">
            y
          </div>
          <div class="keyboard-key" data-keyboard-key="u">
            u
          </div>
          <div class="keyboard-key" data-keyboard-key="i">
            i
          </div>
          <div class="keyboard-key" data-keyboard-key="o">
            o
          </div>
          <div class="keyboard-key" data-keyboard-key="p">
            p
          </div>
          <div class="keyboard-key" data-keyboard-key="[">
            [
          </div>
          <div class="keyboard-key" data-keyboard-key="]">
            ]
          </div>
          <div class="keyboard-key keyboard-enter" data-keyboard-key="Return">
            enter
          </div>
        </div>
        <div class="keyboard-row keyboard-row-4">
          <div class="keyboard-key keyboard-capslock" data-keyboard-key="HAMBAGA">
            🍔
          </div>
          <div class="keyboard-key" data-keyboard-key="a">
            a
          </div>
          <div class="keyboard-key" data-keyboard-key="s">
            s
          </div>
          <div class="keyboard-key" data-keyboard-key="d">
            d
          </div>
          <div class="keyboard-key" data-keyboard-key="f">
            f
          </div>
          <div class="keyboard-key" data-keyboard-key="g">
            g
          </div>
          <div class="keyboard-key" data-keyboard-key="h">
            h
          </div>
          <div class="keyboard-key" data-keyboard-key="j">
            j
          </div>
          <div class="keyboard-key" data-keyboard-key="k">
            k
          </div>
          <div class="keyboard-key" data-keyboard-key="l">
            l
          </div>
          <div class="keyboard-key" data-keyboard-key=";">
            ;
          </div>
          <div class="keyboard-key" data-keyboard-key="'">
            '
          </div>
          <div class="keyboard-key keyboard-backslash" data-keyboard-key="\\">
            \\
          </div>
        </div>
        <div class="keyboard-row keyboard-row-5">
          <div class="keyboard-key keyboard-lshift" data-keyboard-key="Shift_L">
            shift
          </div>
          <div class="keyboard-key" data-keyboard-key="\\">
            \\
          </div>
          <div class="keyboard-key" data-keyboard-key="z">
            z
          </div>
          <div class="keyboard-key" data-keyboard-key="x">
            x
          </div>
          <div class="keyboard-key" data-keyboard-key="c">
            c
          </div>
          <div class="keyboard-key" data-keyboard-key="v">
            v
          </div>
          <div class="keyboard-key" data-keyboard-key="b">
            b
          </div>
          <div class="keyboard-key" data-keyboard-key="n">
            n
          </div>
          <div class="keyboard-key" data-keyboard-key="m">
            m
          </div>
          <div class="keyboard-key" data-keyboard-key=",">
            ,
          </div>
          <div class="keyboard-key" data-keyboard-key=".">
            .
          </div>
          <div class="keyboard-key" data-keyboard-key="/">
            /
          </div>
          <div class="keyboard-key keyboard-rshift" data-keyboard-key="Shift_R">
            shift
          </div>
        </div>
        <div class="keyboard-row keyboard-row-6">
          <div class="keyboard-key keyboard-lctrl" data-keyboard-key="Control_L">
            ctrl
          </div>
          <div class="keyboard-key keyboard-super" data-keyboard-key="Meta_L">
            win
          </div>
          <div class="keyboard-key keyboard-alt" data-keyboard-key="Alt_L">
            alt
          </div>
          <div class="keyboard-key keyboard-spacebar" data-keyboard-key="space">
            space
          </div>
          <div class="keyboard-key keyboard-altgr" data-keyboard-key="Alt_R">
            altgr
          </div>
          <div class="keyboard-key keyboard-what" data-keyboard-key="Menu">
            menu
          </div>
          <div class="keyboard-key keyboard-rctrl" data-keyboard-key="Control_R">
            ctrl
          </div>
        </div>
        <div class="keyboard-row">
          <div class="keyboard-key" data-keyboard-key="XF86AudioLowerVolume">
            🔉
          </div>
          <div class="keyboard-key" data-keyboard-key="XF86AudioRaiseVolume">
            🔊
          </div>
          <div class="keyboard-key" data-keyboard-key="Left">
            ⬅️
          </div>
          <div class="keyboard-key" data-keyboard-key="Down">
            ⬇️
          </div>
          <div class="keyboard-key" data-keyboard-key="Up">
            ⬆️
          </div>
          <div class="keyboard-key" data-keyboard-key="Right">
            ➡️
          </div>
          <div class="keyboard-key" data-keyboard-key="Page_Up">
            PgUp
          </div>
          <div class="keyboard-key" data-keyboard-key="Page_Down">
            PgDn
          </div>
          <div class="keyboard-key" data-keyboard-key="Home">
            🏠
          </div>
          <div class="keyboard-key" data-keyboard-key="End">
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
    const MODIFIER_ON_CLASS = "keyboard-modifier-on";
    const KEY_DATASET = "data-keyboard-key";
    const KEY_CLASS = "keyboard-key";

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
        const key = button.dataset.keyboardKey;

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


// keyboard integration
(function () {
    var o = mknod('div');
    clmod(o, 'keyboard-container', 1);
    ebi('op_msg').appendChild(o);

    o = mknod('style');
    o.innerHTML = `
.keyboard-body {
	display: flex;
	flex-flow: column nowrap;
    margin: .6em 0;
}

.keyboard-row {
	display: flex;
}

.keyboard-key {
	border: 1px solid rgba(128,128,128,0.2);
	width: 41px;
	height: 40px;

	display: flex;
	justify-content: center;
	align-items: center;
}

.keyboard-key:active {
	background-color: lightgrey;
}

.keyboard-key.keyboard-modifier-on {
	background-color: lightblue;
}

.keyboard-key.keyboard-backspace {
	width: 82px;
}

.keyboard-key.keyboard-tab {
	width: 55px;
}

.keyboard-key.keyboard-enter {
	width: 69px;
}

.keyboard-key.keyboard-capslock {
	width: 80px;
}

.keyboard-key.keyboard-backslash {
	width: 88px;
}

.keyboard-key.keyboard-lshift {
	width: 65px;
}

.keyboard-key.keyboard-rshift {
	width: 103px;
}

.keyboard-key.keyboard-lctrl {
	width: 55px;
}

.keyboard-key.keyboard-super {
	width: 55px;
}

.keyboard-key.keyboard-alt {
	width: 55px;
}

.keyboard-key.keyboard-altgr {
	width: 55px;
}

.keyboard-key.keyboard-what {
	width: 55px;
}

.keyboard-key.keyboard-rctrl {
	width: 55px;
}

.keyboard-key.keyboard-spacebar {
	width: 302px;
}
`;
    document.head.appendChild(o);

    initKeyboard('/', hambagas,
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
