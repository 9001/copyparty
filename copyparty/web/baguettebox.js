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
            bodyClass: 'baguetteBox-open',
            titleTag: false,
            async: false,
            preload: 2,
            animation: 'slideIn',
            afterShow: null,
            afterHide: null,
            onChange: null,
        },
        overlay, slider, previousButton, nextButton, closeButton,
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
        isFullscreen = false;

    var onFSC = function (e) {
        isFullscreen = !!document.fullscreenElement;
    };

    var overlayClickHandler = function (event) {
        if (event.target.id.indexOf('baguette-img') !== -1) {
            hideOverlay();
        }
    };

    var touchstartHandler = function (event) {
        touch.count++;
        if (touch.count > 1) {
            touch.multitouch = true;
        }
        touch.startX = event.changedTouches[0].pageX;
        touch.startY = event.changedTouches[0].pageY;
    };
    var touchmoveHandler = function (event) {
        if (touchFlag || touch.multitouch) {
            return;
        }
        event.preventDefault ? event.preventDefault() : event.returnValue = false;
        var touchEvent = event.touches[0] || event.changedTouches[0];
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
        if (touch.count <= 0) {
            touch.multitouch = false;
        }
        touchFlag = false;
    };
    var contextmenuHandler = function () {
        touchendHandler();
    };

    var trapFocusInsideOverlay = function (event) {
        if (overlay.style.display === 'block' && (overlay.contains && !overlay.contains(event.target))) {
            event.stopPropagation();
            initFocus();
        }
    };

    function run(selector, userOptions) {
        buildOverlay();
        removeFromCache(selector);
        return bindImageClickListeners(selector, userOptions);
    }

    function bindImageClickListeners(selector, userOptions) {
        var galleryNodeList = document.querySelectorAll(selector);
        var selectorData = {
            galleries: [],
            nodeList: galleryNodeList
        };
        data[selector] = selectorData;

        [].forEach.call(galleryNodeList, function (galleryElement) {
            var tagsNodeList = [];
            if (galleryElement.tagName === 'A') {
                tagsNodeList = [galleryElement];
            } else {
                tagsNodeList = galleryElement.getElementsByTagName('a');
            }

            tagsNodeList = [].filter.call(tagsNodeList, function (element) {
                if (element.className.indexOf(userOptions && userOptions.ignoreClass) === -1) {
                    return re_i.test(element.href) || re_v.test(element.href);
                }
            });
            if (tagsNodeList.length === 0) {
                return;
            }

            var gallery = [];
            [].forEach.call(tagsNodeList, function (imageElement, imageIndex) {
                var imageElementClickHandler = function (event) {
                    if (event && (event.ctrlKey || event.metaKey))
                        return true;

                    event.preventDefault ? event.preventDefault() : event.returnValue = false;
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
        for (var selector in data) {
            if (data.hasOwnProperty(selector)) {
                removeFromCache(selector);
            }
        }
    }

    function removeFromCache(selector) {
        if (!data.hasOwnProperty(selector)) {
            return;
        }
        var galleries = data[selector].galleries;
        [].forEach.call(galleries, function (gallery) {
            [].forEach.call(gallery, function (imageItem) {
                unbind(imageItem.imageElement, 'click', imageItem.eventHandler);
            });

            if (currentGallery === gallery) {
                currentGallery = [];
            }
        });

        delete data[selector];
    }

    function buildOverlay() {
        overlay = ebi('baguetteBox-overlay');
        if (overlay) {
            slider = ebi('baguetteBox-slider');
            previousButton = ebi('previous-button');
            nextButton = ebi('next-button');
            closeButton = ebi('close-button');
            return;
        }
        overlay = mknod('div');
        overlay.setAttribute('role', 'dialog');
        overlay.id = 'baguetteBox-overlay';
        document.getElementsByTagName('body')[0].appendChild(overlay);

        slider = mknod('div');
        slider.id = 'baguetteBox-slider';
        overlay.appendChild(slider);

        previousButton = mknod('button');
        previousButton.setAttribute('type', 'button');
        previousButton.id = 'previous-button';
        previousButton.setAttribute('aria-label', 'Previous');
        previousButton.innerHTML = '&lt;';
        overlay.appendChild(previousButton);

        nextButton = mknod('button');
        nextButton.setAttribute('type', 'button');
        nextButton.id = 'next-button';
        nextButton.setAttribute('aria-label', 'Next');
        nextButton.innerHTML = '&gt;';
        overlay.appendChild(nextButton);

        closeButton = mknod('button');
        closeButton.setAttribute('type', 'button');
        closeButton.id = 'close-button';
        closeButton.setAttribute('aria-label', 'Close');
        closeButton.innerHTML = '&times;';
        overlay.appendChild(closeButton);

        previousButton.className = nextButton.className = closeButton.className = 'baguetteBox-button';

        bindEvents();
    }

    function keyDownHandler(e) {
        if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing)
            return;

        var k = e.code + '';

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
        else if (k == "KeyM" && vid())
            vid().muted = !vid().muted;
        else if (k == "KeyF")
            try {
                if (isFullscreen)
                    document.exitFullscreen();
                else
                    vid().requestFullscreen();
            }
            catch (ex) { }
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
        bind(previousButton, 'click', showPreviousImage);
        bind(nextButton, 'click', showNextImage);
        bind(closeButton, 'click', hideOverlay);
        bind(slider, 'contextmenu', contextmenuHandler);
        bind(overlay, 'touchstart', touchstartHandler, nonPassiveEvent);
        bind(overlay, 'touchmove', touchmoveHandler, passiveEvent);
        bind(overlay, 'touchend', touchendHandler);
        bind(document, 'focus', trapFocusInsideOverlay, true);
    }

    function unbindEvents() {
        unbind(overlay, 'click', overlayClickHandler);
        unbind(previousButton, 'click', showPreviousImage);
        unbind(nextButton, 'click', showNextImage);
        unbind(closeButton, 'click', hideOverlay);
        unbind(slider, 'contextmenu', contextmenuHandler);
        unbind(overlay, 'touchstart', touchstartHandler, nonPassiveEvent);
        unbind(overlay, 'touchmove', touchmoveHandler, passiveEvent);
        unbind(overlay, 'touchend', touchendHandler);
        unbind(document, 'focus', trapFocusInsideOverlay, true);
    }

    function prepareOverlay(gallery, userOptions) {
        if (currentGallery === gallery) {
            return;
        }
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

            imagesFiguresIds.push('baguetteBox-figure-' + i);
            imagesCaptionsIds.push('baguetteBox-figcaption-' + i);
            slider.appendChild(imagesElements[i]);
        }
        overlay.setAttribute('aria-labelledby', imagesFiguresIds.join(' '));
        overlay.setAttribute('aria-describedby', imagesCaptionsIds.join(' '));
    }

    function setOptions(newOptions) {
        if (!newOptions) {
            newOptions = {};
        }
        for (var item in defaults) {
            options[item] = defaults[item];
            if (typeof newOptions[item] !== 'undefined') {
                options[item] = newOptions[item];
            }
        }
        slider.style.transition = (options.animation === 'fadeIn' ? 'opacity .4s ease' :
            options.animation === 'slideIn' ? '' : 'none');

        if (options.buttons === 'auto' && ('ontouchstart' in window || currentGallery.length === 1)) {
            options.buttons = false;
        }

        previousButton.style.display = nextButton.style.display = (options.buttons ? '' : 'none');
    }

    function showOverlay(chosenImageIndex) {
        if (options.noScrollbars) {
            document.documentElement.style.overflowY = 'hidden';
            document.body.style.overflowY = 'scroll';
        }
        if (overlay.style.display === 'block') {
            return;
        }

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
            if (options.bodyClass && document.body.classList) {
                document.body.classList.add(options.bodyClass);
            }
            if (options.afterShow) {
                options.afterShow();
            }
        }, 50);
        if (options.onChange) {
            options.onChange(currentIndex, imagesElements.length);
        }
        documentLastFocus = document.activeElement;
        initFocus();
        isOverlayVisible = true;
    }

    function initFocus() {
        if (options.buttons) {
            previousButton.focus();
        } else {
            closeButton.focus();
        }
    }

    function hideOverlay(e) {
        ev(e);
        playvid(false);
        if (options.noScrollbars) {
            document.documentElement.style.overflowY = 'auto';
            document.body.style.overflowY = 'auto';
        }
        if (overlay.style.display === 'none') {
            return;
        }

        unbind(document, 'keydown', keyDownHandler);
        unbind(document, 'keyup', keyUpHandler);
        unbind(document, 'fullscreenchange', onFSC);
        // Fade out and hide the overlay
        overlay.className = '';
        setTimeout(function () {
            overlay.style.display = 'none';
            if (options.bodyClass && document.body.classList) {
                document.body.classList.remove(options.bodyClass);
            }
            if (options.afterHide) {
                options.afterHide();
            }
            documentLastFocus && documentLastFocus.focus();
            isOverlayVisible = false;
        }, 500);
    }

    function loadImage(index, callback) {
        var imageContainer = imagesElements[index];
        var galleryItem = currentGallery[index];

        if (typeof imageContainer === 'undefined' || typeof galleryItem === 'undefined') {
            return;  // out-of-bounds or gallery dirty
        }

        if (imageContainer.querySelector('img, video')) {
            // was loaded, cb and bail
            if (callback) {
                callback();
            }
            return;
        }

        var imageElement = galleryItem.imageElement,
            imageSrc = imageElement.href,
            thumbnailElement = imageElement.querySelector('img, video'),
            imageCaption = typeof options.captions === 'function' ?
                options.captions.call(currentGallery, imageElement) :
                imageElement.getAttribute('data-caption') || imageElement.title;

        var figure = mknod('figure');
        figure.id = 'baguetteBox-figure-' + index;
        figure.innerHTML = '<div class="baguetteBox-spinner">' +
            '<div class="baguetteBox-double-bounce1"></div>' +
            '<div class="baguetteBox-double-bounce2"></div>' +
            '</div>';

        if (options.captions && imageCaption) {
            var figcaption = mknod('figcaption');
            figcaption.id = 'baguetteBox-figcaption-' + index;
            figcaption.innerHTML = imageCaption;
            figure.appendChild(figcaption);
        }
        imageContainer.appendChild(figure);

        var is_vid = re_v.test(imageSrc),
            image = mknod(is_vid ? 'video' : 'img');

        clmod(imageContainer, 'vid', is_vid);

        image.addEventListener(is_vid ? 'loadedmetadata' : 'load', function () {
            // Remove loader element
            var spinner = document.querySelector('#baguette-img-' + index + ' .baguetteBox-spinner');
            figure.removeChild(spinner);
            if (!options.async && callback)
                callback();
        });
        image.setAttribute('src', imageSrc);
        image.setAttribute('controls', 'controls');
        image.alt = thumbnailElement ? thumbnailElement.alt || '' : '';
        if (options.titleTag && imageCaption) {
            image.title = imageCaption;
        }
        figure.appendChild(image);

        if (options.async && callback) {
            callback();
        }
    }

    function showNextImage(e) {
        ev(e);
        return show(currentIndex + 1);
    }

    function showPreviousImage(e) {
        ev(e);
        return show(currentIndex - 1);
    }

    function showFirstImage(event) {
        if (event) {
            event.preventDefault();
        }
        return show(0);
    }

    function showLastImage(event) {
        if (event) {
            event.preventDefault();
        }
        return show(currentGallery.length - 1);
    }

    /**
     * Move the gallery to a specific index
     * @param `index` {number} - the position of the image
     * @param `gallery` {array} - gallery which should be opened, if omitted assumes the currently opened one
     * @return {boolean} - true on success or false if the index is invalid
     */
    function show(index, gallery) {
        if (!isOverlayVisible && index >= 0 && index < gallery.length) {
            prepareOverlay(gallery, options);
            showOverlay(index);
            return true;
        }
        if (index < 0) {
            if (options.animation) {
                bounceAnimation('left');
            }
            return false;
        }
        if (index >= imagesElements.length) {
            if (options.animation) {
                bounceAnimation('right');
            }
            return false;
        }

        playvid(false);
        currentIndex = index;
        loadImage(currentIndex, function () {
            preloadNext(currentIndex);
            preloadPrev(currentIndex);
        });
        updateOffset();

        if (options.onChange) {
            options.onChange(currentIndex, imagesElements.length);
        }

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

    /**
     * Triggers the bounce animation
     * @param {('left'|'right')} direction - Direction of the movement
     */
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
        playvid(true);
    }

    function preloadNext(index) {
        if (index - currentIndex >= options.preload) {
            return;
        }
        loadImage(index + 1, function () {
            preloadNext(index + 1);
        });
    }

    function preloadPrev(index) {
        if (currentIndex - index >= options.preload) {
            return;
        }
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
        document.getElementsByTagName('body')[0].removeChild(ebi('baguetteBox-overlay'));
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
