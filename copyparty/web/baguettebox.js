/*!
 * baguetteBox.js
 * @author  feimosi
 * @version 1.11.1-mod
 * @url https://github.com/feimosi/baguetteBox.js
 */

window.baguetteBox = (function () {
    'use strict';

    var options = {},
        defaults = {
            captions: true,
            buttons: 'auto',
            noScrollbars: false,
            bodyClass: 'bbox-open',
            titleTag: false,
            async: false,
            preload: 2,
            animation: 'slideIn',
            afterShow: null,
            afterHide: null,
            onChange: null,
        },
        overlay, slider, btnPrev, btnNext, btnHelp, btnVmode, btnClose,
        currentGallery = [],
        currentIndex = 0,
        isOverlayVisible = false,
        touch = {},  // start-pos
        touchFlag = false,  // busy
        re_i = /.+\.(gif|jpe?g|png|webp)(\?|$)/i,
        re_v = /.+\.(webm|mp4)(\?|$)/i,
        data = {},  // all galleries
        imagesElements = [],
        documentLastFocus = null,
        isFullscreen = false,
        vmute = false,
        vloop = false,
        vnext = false,
        resume_mp = false;

    var onFSC = function (e) {
        isFullscreen = !!document.fullscreenElement;
    };

    var overlayClickHandler = function (e) {
        if (e.target.id.indexOf('baguette-img') !== -1)
            hideOverlay();
    };

    var touchstartHandler = function (e) {
        touch.count++;
        if (touch.count > 1)
            touch.multitouch = true;

        touch.startX = e.changedTouches[0].pageX;
        touch.startY = e.changedTouches[0].pageY;
    };
    var touchmoveHandler = function (e) {
        if (touchFlag || touch.multitouch)
            return;

        e.preventDefault ? e.preventDefault() : e.returnValue = false;
        var touchEvent = e.touches[0] || e.changedTouches[0];
        if (touchEvent.pageX - touch.startX > 40) {
            touchFlag = true;
            showPreviousImage();
        } else if (touchEvent.pageX - touch.startX < -40) {
            touchFlag = true;
            showNextImage();
        } else if (touch.startY - touchEvent.pageY > 100) {
            hideOverlay();
        }
    };
    var touchendHandler = function () {
        touch.count--;
        if (touch.count <= 0)
            touch.multitouch = false;

        touchFlag = false;
    };
    var contextmenuHandler = function () {
        touchendHandler();
    };

    var trapFocusInsideOverlay = function (e) {
        if (overlay.style.display === 'block' && (overlay.contains && !overlay.contains(e.target))) {
            e.stopPropagation();
            btnClose.focus();
        }
    };

    function run(selector, userOptions) {
        buildOverlay();
        removeFromCache(selector);
        return bindImageClickListeners(selector, userOptions);
    }

    function bindImageClickListeners(selector, userOptions) {
        var galleryNodeList = QSA(selector);
        var selectorData = {
            galleries: [],
            nodeList: galleryNodeList
        };
        data[selector] = selectorData;

        [].forEach.call(galleryNodeList, function (galleryElement) {
            var tagsNodeList = [];
            if (galleryElement.tagName === 'A')
                tagsNodeList = [galleryElement];
            else
                tagsNodeList = galleryElement.getElementsByTagName('a');

            tagsNodeList = [].filter.call(tagsNodeList, function (element) {
                if (element.className.indexOf(userOptions && userOptions.ignoreClass) === -1)
                    return re_i.test(element.href) || re_v.test(element.href);
            });
            if (!tagsNodeList.length)
                return;

            var gallery = [];
            [].forEach.call(tagsNodeList, function (imageElement, imageIndex) {
                var imageElementClickHandler = function (e) {
                    if (ctrl(e))
                        return true;

                    e.preventDefault ? e.preventDefault() : e.returnValue = false;
                    prepareOverlay(gallery, userOptions);
                    showOverlay(imageIndex);
                };
                var imageItem = {
                    eventHandler: imageElementClickHandler,
                    imageElement: imageElement
                };
                bind(imageElement, 'click', imageElementClickHandler);
                gallery.push(imageItem);
            });
            selectorData.galleries.push(gallery);
        });

        return selectorData.galleries;
    }

    function clearCachedData() {
        for (var selector in data)
            if (data.hasOwnProperty(selector))
                removeFromCache(selector);
    }

    function removeFromCache(selector) {
        if (!data.hasOwnProperty(selector))
            return;

        var galleries = data[selector].galleries;
        [].forEach.call(galleries, function (gallery) {
            [].forEach.call(gallery, function (imageItem) {
                unbind(imageItem.imageElement, 'click', imageItem.eventHandler);
            });

            if (currentGallery === gallery)
                currentGallery = [];
        });

        delete data[selector];
    }

    function buildOverlay() {
        overlay = ebi('bbox-overlay');
        if (!overlay) {
            var ctr = mknod('div');
            ctr.innerHTML = (
                '<div id="bbox-overlay" role="dialog">' +
                '<div id="bbox-slider"></div>' +
                '<button id="bbox-prev" class="bbox-btn" type="button" aria-label="Previous">&lt;</button>' +
                '<button id="bbox-next" class="bbox-btn" type="button" aria-label="Next">&gt;</button>' +
                '<div id="bbox-btns">' +
                '<button id="bbox-help" type="button">?</button>' +
                '<button id="bbox-vmode" type="button" tt="a"></button>' +
                '<button id="bbox-close" type="button" aria-label="Close">X</button>' +
                '</div></div>'
            );
            overlay = ctr.firstChild;
            QS('body').appendChild(overlay);
            tt.att(overlay);
        }
        slider = ebi('bbox-slider');
        btnPrev = ebi('bbox-prev');
        btnNext = ebi('bbox-next');
        btnHelp = ebi('bbox-help');
        btnVmode = ebi('bbox-vmode');
        btnClose = ebi('bbox-close');
        bindEvents();
    }

    function halp() {
        if (ebi('bbox-halp'))
            return;

        var list = [
            ['<b># hotkey</b>', '<b># operation</b>'],
            ['escape', 'close'],
            ['left, J', 'previous file'],
            ['right, L', 'next file'],
            ['home', 'first file'],
            ['end', 'last file'],
            ['space, P, K', 'video: play / pause'],
            ['U', 'video: seek 10sec back'],
            ['P', 'video: seek 10sec ahead'],
            ['M', 'video: toggle mute'],
            ['R', 'video: toggle loop'],
            ['C', 'video: toggle auto-next'],
            ['F', 'video: toggle fullscreen'],
        ],
            d = mknod('table'),
            html = ['<tbody>'];

        for (var a = 0; a < list.length; a++)
            html.push('<tr><td>' + list[a][0] + '</td><td>' + list[a][1] + '</td></tr>');

        d.innerHTML = html.join('\n') + '</tbody>';
        d.setAttribute('id', 'bbox-halp');
        d.onclick = function () {
            overlay.removeChild(d);
        };
        overlay.appendChild(d);
    }

    function keyDownHandler(e) {
        if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing)
            return;

        var k = e.code + '', v = vid();

        if (k == "ArrowLeft" || k == "KeyJ")
            showPreviousImage();
        else if (k == "ArrowRight" || k == "KeyL")
            showNextImage();
        else if (k == "Escape")
            hideOverlay();
        else if (k == "Home")
            showFirstImage(e);
        else if (k == "End")
            showLastImage(e);
        else if (k == "Space" || k == "KeyP" || k == "KeyK")
            playpause();
        else if (k == "KeyU" || k == "KeyO")
            relseek(k == "KeyU" ? -10 : 10);
        else if (k == "KeyM" && v) {
            v.muted = vmute = !vmute;
            mp_ctl();
        }
        else if (k == "KeyR" && v) {
            vloop = !vloop;
            vnext = vnext && !vloop;
            setVmode();
        }
        else if (k == "KeyC" && v) {
            vnext = !vnext;
            vloop = vloop && !vnext;
            setVmode();
        }
        else if (k == "KeyF")
            try {
                if (isFullscreen)
                    document.exitFullscreen();
                else
                    v.requestFullscreen();
            }
            catch (ex) { }
    }

    function setVmode() {
        var v = vid();
        ebi('bbox-vmode').style.display = v ? '' : 'none';
        if (!v)
            return;

        var msg = 'When video ends, ', tts = '', lbl;
        if (vloop) {
            lbl = 'Loop';
            msg += 'repeat it';
            tts = '$NHotkey: R';
        }
        else if (vnext) {
            lbl = 'Cont';
            msg += 'continue to next';
            tts = '$NHotkey: C';
        }
        else {
            lbl = 'Stop';
            msg += 'just stop'
        }
        btnVmode.setAttribute('aria-label', msg);
        btnVmode.setAttribute('tt', msg + tts);
        btnVmode.textContent = lbl;

        v.loop = vloop
        if (vloop && v.paused)
            v.play();
    }

    function tglVmode() {
        if (vloop) {
            vnext = true;
            vloop = false;
        }
        else if (vnext)
            vnext = false;
        else
            vloop = true;

        setVmode();
        if (tt.en)
            tt.show.bind(this)();
    }

    function keyUpHandler(e) {
        if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing)
            return;

        var k = e.code + '';

        if (k == "Space")
            ev(e);
    }

    var passiveSupp = false;
    try {
        var opts = {
            get passive() {
                passiveSupp = true;
                return false;
            }
        };
        window.addEventListener('test', null, opts);
        window.removeEventListener('test', null, opts);
    }
    catch (ex) {
        passiveSupp = false;
    }
    var passiveEvent = passiveSupp ? { passive: false } : null;
    var nonPassiveEvent = passiveSupp ? { passive: true } : null;

    function bindEvents() {
        bind(overlay, 'click', overlayClickHandler);
        bind(btnPrev, 'click', showPreviousImage);
        bind(btnNext, 'click', showNextImage);
        bind(btnClose, 'click', hideOverlay);
        bind(btnVmode, 'click', tglVmode);
        bind(btnHelp, 'click', halp);
        bind(slider, 'contextmenu', contextmenuHandler);
        bind(overlay, 'touchstart', touchstartHandler, nonPassiveEvent);
        bind(overlay, 'touchmove', touchmoveHandler, passiveEvent);
        bind(overlay, 'touchend', touchendHandler);
        bind(document, 'focus', trapFocusInsideOverlay, true);
    }

    function unbindEvents() {
        unbind(overlay, 'click', overlayClickHandler);
        unbind(btnPrev, 'click', showPreviousImage);
        unbind(btnNext, 'click', showNextImage);
        unbind(btnClose, 'click', hideOverlay);
        unbind(btnVmode, 'click', tglVmode);
        unbind(btnHelp, 'click', halp);
        unbind(slider, 'contextmenu', contextmenuHandler);
        unbind(overlay, 'touchstart', touchstartHandler, nonPassiveEvent);
        unbind(overlay, 'touchmove', touchmoveHandler, passiveEvent);
        unbind(overlay, 'touchend', touchendHandler);
        unbind(document, 'focus', trapFocusInsideOverlay, true);
    }

    function prepareOverlay(gallery, userOptions) {
        if (currentGallery === gallery)
            return;

        currentGallery = gallery;
        setOptions(userOptions);
        slider.innerHTML = '';
        imagesElements.length = 0;

        var imagesFiguresIds = [];
        var imagesCaptionsIds = [];
        for (var i = 0, fullImage; i < gallery.length; i++) {
            fullImage = mknod('div');
            fullImage.className = 'full-image';
            fullImage.id = 'baguette-img-' + i;
            imagesElements.push(fullImage);

            imagesFiguresIds.push('bbox-figure-' + i);
            imagesCaptionsIds.push('bbox-figcaption-' + i);
            slider.appendChild(imagesElements[i]);
        }
        overlay.setAttribute('aria-labelledby', imagesFiguresIds.join(' '));
        overlay.setAttribute('aria-describedby', imagesCaptionsIds.join(' '));
    }

    function setOptions(newOptions) {
        if (!newOptions)
            newOptions = {};

        for (var item in defaults) {
            options[item] = defaults[item];
            if (typeof newOptions[item] !== 'undefined')
                options[item] = newOptions[item];
        }
        slider.style.transition = (options.animation === 'fadeIn' ? 'opacity .4s ease' :
            options.animation === 'slideIn' ? '' : 'none');

        if (options.buttons === 'auto' && ('ontouchstart' in window || currentGallery.length === 1))
            options.buttons = false;

        btnPrev.style.display = btnNext.style.display = (options.buttons ? '' : 'none');
    }

    function showOverlay(chosenImageIndex) {
        if (options.noScrollbars) {
            document.documentElement.style.overflowY = 'hidden';
            document.body.style.overflowY = 'scroll';
        }
        if (overlay.style.display === 'block')
            return;

        bind(document, 'keydown', keyDownHandler);
        bind(document, 'keyup', keyUpHandler);
        bind(document, 'fullscreenchange', onFSC);
        currentIndex = chosenImageIndex;
        touch = {
            count: 0,
            startX: null,
            startY: null
        };
        loadImage(currentIndex, function () {
            preloadNext(currentIndex);
            preloadPrev(currentIndex);
        });

        updateOffset();
        overlay.style.display = 'block';
        // Fade in overlay
        setTimeout(function () {
            overlay.className = 'visible';
            if (options.bodyClass && document.body.classList)
                document.body.classList.add(options.bodyClass);

            if (options.afterShow)
                options.afterShow();
        }, 50);

        if (options.onChange)
            options.onChange(currentIndex, imagesElements.length);

        documentLastFocus = document.activeElement;
        btnClose.focus();
        isOverlayVisible = true;
    }

    function hideOverlay(e) {
        ev(e);
        playvid(false);
        if (options.noScrollbars) {
            document.documentElement.style.overflowY = 'auto';
            document.body.style.overflowY = 'auto';
        }
        if (overlay.style.display === 'none')
            return;

        unbind(document, 'keydown', keyDownHandler);
        unbind(document, 'keyup', keyUpHandler);
        unbind(document, 'fullscreenchange', onFSC);
        // Fade out and hide the overlay
        overlay.className = '';
        setTimeout(function () {
            overlay.style.display = 'none';
            if (options.bodyClass && document.body.classList)
                document.body.classList.remove(options.bodyClass);

            var h = ebi('bbox-halp');
            if (h)
                h.parentNode.removeChild(h);

            if (options.afterHide)
                options.afterHide();

            documentLastFocus && documentLastFocus.focus();
            isOverlayVisible = false;
        }, 500);
    }

    function loadImage(index, callback) {
        var imageContainer = imagesElements[index];
        var galleryItem = currentGallery[index];

        if (typeof imageContainer === 'undefined' || typeof galleryItem === 'undefined')
            return;  // out-of-bounds or gallery dirty

        if (imageContainer.querySelector('img, video'))
            // was loaded, cb and bail
            return callback ? callback() : null;

        // maybe unloaded video
        while (imageContainer.firstChild)
            imageContainer.removeChild(imageContainer.firstChild);

        var imageElement = galleryItem.imageElement,
            imageSrc = imageElement.href,
            is_vid = re_v.test(imageSrc),
            thumbnailElement = imageElement.querySelector('img, video'),
            imageCaption = typeof options.captions === 'function' ?
                options.captions.call(currentGallery, imageElement) :
                imageElement.getAttribute('data-caption') || imageElement.title;

        imageSrc += imageSrc.indexOf('?') < 0 ? '?cache' : '&cache';

        if (is_vid && index != currentIndex)
            return;  // no preload

        var figure = mknod('figure');
        figure.id = 'bbox-figure-' + index;
        figure.innerHTML = '<div class="bbox-spinner">' +
            '<div class="bbox-double-bounce1"></div>' +
            '<div class="bbox-double-bounce2"></div>' +
            '</div>';

        if (options.captions && imageCaption) {
            var figcaption = mknod('figcaption');
            figcaption.id = 'bbox-figcaption-' + index;
            figcaption.innerHTML = imageCaption;
            figure.appendChild(figcaption);
        }
        imageContainer.appendChild(figure);

        var image = mknod(is_vid ? 'video' : 'img');
        clmod(imageContainer, 'vid', is_vid);

        image.addEventListener(is_vid ? 'loadedmetadata' : 'load', function () {
            // Remove loader element
            var spinner = QS('#baguette-img-' + index + ' .bbox-spinner');
            figure.removeChild(spinner);
            if (!options.async && callback)
                callback();
        });
        image.setAttribute('src', imageSrc);
        if (is_vid) {
            image.setAttribute('controls', 'controls');
            image.onended = vidEnd;
        }
        image.alt = thumbnailElement ? thumbnailElement.alt || '' : '';
        if (options.titleTag && imageCaption)
            image.title = imageCaption;

        figure.appendChild(image);

        if (options.async && callback)
            callback();
    }

    function showNextImage(e) {
        ev(e);
        return show(currentIndex + 1);
    }

    function showPreviousImage(e) {
        ev(e);
        return show(currentIndex - 1);
    }

    function showFirstImage(e) {
        if (e)
            e.preventDefault();

        return show(0);
    }

    function showLastImage(e) {
        if (e)
            e.preventDefault();

        return show(currentGallery.length - 1);
    }

    function show(index, gallery) {
        if (!isOverlayVisible && index >= 0 && index < gallery.length) {
            prepareOverlay(gallery, options);
            showOverlay(index);
            return true;
        }
        if (index < 0) {
            if (options.animation)
                bounceAnimation('left');

            return false;
        }
        if (index >= imagesElements.length) {
            if (options.animation)
                bounceAnimation('right');

            return false;
        }

        var v = vid();
        if (v) {
            v.src = '';
            v.load();
            v.parentNode.removeChild(v);
        }

        currentIndex = index;
        loadImage(currentIndex, function () {
            preloadNext(currentIndex);
            preloadPrev(currentIndex);
        });
        updateOffset();

        if (options.onChange)
            options.onChange(currentIndex, imagesElements.length);

        return true;
    }

    function vid() {
        return imagesElements[currentIndex].querySelector('video');
    }

    function playvid(play) {
        if (vid())
            vid()[play ? 'play' : 'pause']();
    }

    function playpause() {
        var v = vid();
        if (v)
            v[v.paused ? "play" : "pause"]();
    }

    function relseek(sec) {
        if (vid())
            vid().currentTime += sec;
    }

    function vidEnd() {
        if (this == vid() && vnext)
            showNextImage();
    }

    function mp_ctl() {
        var v = vid();
        if (!vmute && v && mp.au && !mp.au.paused) {
            mp.fade_out();
            resume_mp = true;
        }
        else if (resume_mp && (vmute || !v) && mp.au && mp.au.paused) {
            mp.fade_in();
            resume_mp = false;
        }
    }

    function bounceAnimation(direction) {
        slider.className = 'bounce-from-' + direction;
        setTimeout(function () {
            slider.className = '';
        }, 400);
    }

    function updateOffset() {
        var offset = -currentIndex * 100 + '%';
        if (options.animation === 'fadeIn') {
            slider.style.opacity = 0;
            setTimeout(function () {
                slider.style.transform = 'translate3d(' + offset + ',0,0)';
                slider.style.opacity = 1;
            }, 400);
        } else {
            slider.style.transform = 'translate3d(' + offset + ',0,0)';
        }
        playvid(false);
        var v = vid();
        if (v) {
            playvid(true);
            v.muted = vmute;
            v.loop = vloop;
        }
        mp_ctl();
        setVmode();
    }

    function preloadNext(index) {
        if (index - currentIndex >= options.preload)
            return;

        loadImage(index + 1, function () {
            preloadNext(index + 1);
        });
    }

    function preloadPrev(index) {
        if (currentIndex - index >= options.preload)
            return;

        loadImage(index - 1, function () {
            preloadPrev(index - 1);
        });
    }

    function bind(element, event, callback, options) {
        element.addEventListener(event, callback, options);
    }

    function unbind(element, event, callback, options) {
        element.removeEventListener(event, callback, options);
    }

    function destroyPlugin() {
        unbindEvents();
        clearCachedData();
        unbind(document, 'keydown', keyDownHandler);
        unbind(document, 'keyup', keyUpHandler);
        document.getElementsByTagName('body')[0].removeChild(ebi('bbox-overlay'));
        data = {};
        currentGallery = [];
        currentIndex = 0;
    }

    return {
        run: run,
        show: show,
        showNext: showNextImage,
        showPrevious: showPreviousImage,
        relseek: relseek,
        playpause: playpause,
        hide: hideOverlay,
        destroy: destroyPlugin
    };
})();
