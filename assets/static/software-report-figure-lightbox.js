(function () {
  // Figures the prose cites by number ("see Fig. 2") are reference material,
  // not a slideshow. Sending the reader to the gallery to look one up costs
  // them their place in the paragraph, and on phones the gallery is a carousel
  // showing one photograph at a time, so the anchor jump landed on whichever
  // slide happened to be up. This opens the cited figure over the page instead:
  // nothing scrolls, and closing puts the reader back on the same line.
  //
  // Scoped to galleries marked [data-figure-lightbox]; the homepage carousels
  // are deliberately left alone.

  var GALLERY = '[data-figure-lightbox]';
  var SLIDE = '.home-gallery__slide';
  var PHOTO = '.software-report__gallery-photo';
  var CREDIT = '.software-report__gallery-caption';
  var LINK = 'a.software-report__fig-link';
  var TAP_SLOP_PX = 10;
  var SWIPE_PX = 48;

  var overlay = null;
  var els = {};
  var items = [];
  var index = 0;
  var isOpen = false;
  var pushedState = false;
  var opener = null;
  var scrollY = 0;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function readGallery(gallery) {
    var slides = gallery.querySelectorAll(SLIDE);
    var list = [];
    for (var i = 0; i < slides.length; i++) {
      var img = slides[i].querySelector(PHOTO);
      if (!img) {
        continue;
      }
      var credit = slides[i].querySelector(CREDIT);
      list.push({
        slide: slides[i],
        img: img,
        src: img.getAttribute('src'),
        // The alt becomes the visible caption in the viewer, so the large
        // image itself is given alt="" there — otherwise a screen reader
        // hears the same sentence twice.
        text: img.getAttribute('alt') || '',
        label: slides[i].getAttribute('data-fig-label') || '',
        credit: credit
      });
    }
    return list;
  }

  function build() {
    if (overlay) {
      return;
    }
    overlay = document.createElement('div');
    overlay.className = 'fig-lightbox';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Figure viewer');
    overlay.hidden = true;
    if (reduceMotion) {
      overlay.classList.add('fig-lightbox--no-motion');
    }
    overlay.innerHTML =
      '<div class="fig-lightbox__backdrop" data-fig-close></div>' +
      // Outside the panel on purpose: anchored to the panel it floats beside
      // the photograph, wherever the panel happens to be centred. The way out
      // of a full-screen viewer belongs in the screen's corner.
      '<button type="button" class="fig-lightbox__close" data-fig-close aria-label="Close figure viewer">' +
      '<span aria-hidden="true">✕</span></button>' +
      '<div class="fig-lightbox__panel">' +
      '<figure class="fig-lightbox__figure">' +
      '<img class="fig-lightbox__image" alt="" decoding="async">' +
      '<figcaption class="fig-lightbox__caption">' +
      '<span class="fig-lightbox__label"></span>' +
      '<span class="fig-lightbox__text"></span>' +
      '<span class="fig-lightbox__credit"></span>' +
      '</figcaption></figure>' +
      '<div class="fig-lightbox__nav">' +
      '<button type="button" class="fig-lightbox__prev" aria-label="Previous figure"><span aria-hidden="true">‹</span></button>' +
      '<span class="fig-lightbox__counter" aria-live="polite"></span>' +
      '<button type="button" class="fig-lightbox__next" aria-label="Next figure"><span aria-hidden="true">›</span></button>' +
      '</div></div>';

    els.panel = overlay.querySelector('.fig-lightbox__panel');
    els.image = overlay.querySelector('.fig-lightbox__image');
    els.label = overlay.querySelector('.fig-lightbox__label');
    els.text = overlay.querySelector('.fig-lightbox__text');
    els.credit = overlay.querySelector('.fig-lightbox__credit');
    els.counter = overlay.querySelector('.fig-lightbox__counter');
    els.close = overlay.querySelector('.fig-lightbox__close');
    els.prev = overlay.querySelector('.fig-lightbox__prev');
    els.next = overlay.querySelector('.fig-lightbox__next');

    overlay.addEventListener('click', function (event) {
      if (event.target.closest('[data-fig-close]')) {
        close(false);
      }
    });
    els.prev.addEventListener('click', function () {
      show(index - 1);
    });
    els.next.addEventListener('click', function () {
      show(index + 1);
    });

    var swipeX = null;
    els.panel.addEventListener('pointerdown', function (event) {
      swipeX = event.button === 0 || event.button === undefined ? event.clientX : null;
    });
    els.panel.addEventListener('pointerup', function (event) {
      if (swipeX === null) {
        return;
      }
      var delta = event.clientX - swipeX;
      swipeX = null;
      if (Math.abs(delta) >= SWIPE_PX) {
        show(index + (delta < 0 ? 1 : -1));
      }
    });

    document.body.appendChild(overlay);
  }

  function show(next) {
    if (!items.length) {
      return;
    }
    index = (next + items.length) % items.length;
    var item = items[index];
    els.image.src = item.src;
    els.label.textContent = item.label;
    els.label.hidden = !item.label;
    els.text.textContent = item.text;
    els.text.hidden = !item.text;
    els.credit.textContent = '';
    if (item.credit) {
      els.credit.appendChild(item.credit.cloneNode(true));
    }
    els.counter.textContent = index + 1 + ' / ' + items.length;
    var single = items.length <= 1;
    els.prev.hidden = single;
    els.next.hidden = single;
    els.counter.hidden = single;
  }

  function focusable() {
    var all = overlay.querySelectorAll('button');
    var out = [];
    for (var i = 0; i < all.length; i++) {
      if (!all[i].hidden && all[i].offsetParent !== null) {
        out.push(all[i]);
      }
    }
    return out;
  }

  function onKeydown(event) {
    if (event.key === 'Escape') {
      event.preventDefault();
      close(false);
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault();
      show(index - 1);
    } else if (event.key === 'ArrowRight') {
      event.preventDefault();
      show(index + 1);
    } else if (event.key === 'Tab') {
      var stops = focusable();
      if (!stops.length) {
        return;
      }
      var first = stops[0];
      var last = stops[stops.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  // Two things happen here, and the second one is not optional.
  //
  // The scroll lock is position: fixed rather than overflow: hidden, because
  // iOS Safari scrolls the body regardless of overflow, and losing the reading
  // position on close is the exact problem this viewer exists to solve.
  //
  // Dropping body's filter is what makes the viewer cover the viewport at all.
  // The sheet sets `html, body { filter: saturate(135%) }`; on body — which is
  // not the root element, so it gets no special-casing — that filter makes body
  // the containing block for every position: fixed descendant. The overlay then
  // resolves inset: 0 against body's box and stretches to the full document
  // height, scrolled off with it. Same trap the comment beside that rule warns
  // about. Nothing is lost visually: the page behind sits under a 92% black
  // scrim, and the photograph is better off un-boosted anyway.
  var savedFilter = '';
  var savedScrollRestoration = null;

  function restoreScrollRestoration() {
    if (savedScrollRestoration === null) {
      return;
    }
    try {
      history.scrollRestoration = savedScrollRestoration;
    } catch (err) {
      /* nothing to hand back */
    }
    savedScrollRestoration = null;
  }

  function lockScroll() {
    scrollY = window.scrollY || window.pageYOffset || 0;
    var body = document.body;
    body.style.position = 'fixed';
    body.style.top = -scrollY + 'px';
    body.style.left = '0';
    body.style.right = '0';
    body.style.width = '100%';
    savedFilter = body.style.filter;
    body.style.filter = 'none';
  }

  function unlockScroll() {
    var body = document.body;
    body.style.position = '';
    body.style.top = '';
    body.style.left = '';
    body.style.right = '';
    body.style.width = '';
    body.style.filter = savedFilter;
    window.scrollTo(0, scrollY);
  }

  function open(list, at, trigger) {
    build();
    // Re-entering while open would run lockScroll a second time and record
    // scrollY as 0, because a fixed body reports no scroll offset.
    if (isOpen) {
      items = list;
      show(at);
      return;
    }
    items = list;
    opener = trigger || null;
    show(at);

    // Both of these must happen before the scroll lock.
    //
    // The browser stamps the outgoing history entry with the document's
    // current scroll offset, and a position: fixed body reports 0. Pushing
    // after the lock therefore recorded the entry as "top of page", and the
    // history.back() on close scrolled the reader there — the whole article
    // snapping to the top the moment they tapped outside the photograph.
    //
    // Turning scroll restoration off is the belt to that braces: even with a
    // correctly stamped entry, the browser's own restore races the scrollTo in
    // unlockScroll, and this viewer is the one deciding where the reader lands.
    try {
      if ('scrollRestoration' in history) {
        savedScrollRestoration = history.scrollRestoration;
        history.scrollRestoration = 'manual';
      }
      // Gives Android's back gesture something to pop, so the first back
      // closes the viewer instead of leaving the article.
      history.pushState({ figLightbox: true }, '');
      pushedState = true;
    } catch (err) {
      pushedState = false;
    }

    lockScroll();
    overlay.hidden = false;
    // Read a layout property to flush the display: none -> flex change before
    // flipping opacity, so the fade actually has a starting frame. A rAF would
    // read better but leaves the viewer at opacity 0 anywhere rAF is throttled
    // or coalesced.
    void overlay.offsetHeight;
    overlay.classList.add('is-open');
    isOpen = true;
    document.addEventListener('keydown', onKeydown, true);
    els.close.focus();
  }

  function close(fromPopstate) {
    if (!isOpen) {
      return;
    }
    isOpen = false;
    document.removeEventListener('keydown', onKeydown, true);
    overlay.classList.remove('is-open');

    var finish = function () {
      overlay.hidden = true;
      els.image.removeAttribute('src');
    };
    if (reduceMotion) {
      finish();
    } else {
      window.setTimeout(finish, 160);
    }

    unlockScroll();
    if (opener && opener.focus) {
      opener.focus({ preventScroll: true });
    }
    opener = null;

    if (pushedState && !fromPopstate) {
      pushedState = false;
      // Scroll restoration is handed back in the popstate this triggers.
      history.back();
    } else {
      pushedState = false;
      restoreScrollRestoration();
    }
  }

  window.addEventListener('popstate', function () {
    if (isOpen) {
      close(true);
    }
    restoreScrollRestoration();
  });

  function indexOfSlide(list, slide) {
    for (var i = 0; i < list.length; i++) {
      if (list[i].slide === slide) {
        return i;
      }
    }
    return -1;
  }

  function wireGallery(gallery) {
    var list = readGallery(gallery);
    if (!list.length) {
      return;
    }

    // The affordance is added by script, never by the template: without JS the
    // photograph stays a plain image rather than a control that does nothing.
    for (var i = 0; i < list.length; i++) {
      (function (item, at) {
        var img = item.img;
        img.setAttribute('role', 'button');
        img.setAttribute('tabindex', '0');
        img.setAttribute(
          'aria-label',
          'View ' + (item.label || 'figure ' + (at + 1)) + ' full size'
        );

        // The carousel treats a horizontal drag as a swipe; only a tap that
        // stayed put should open the viewer.
        var downX = null;
        var downY = null;
        img.addEventListener('pointerdown', function (event) {
          downX = event.clientX;
          downY = event.clientY;
        });
        img.addEventListener('click', function (event) {
          if (downX !== null) {
            var moved =
              Math.abs(event.clientX - downX) > TAP_SLOP_PX ||
              Math.abs(event.clientY - downY) > TAP_SLOP_PX;
            downX = null;
            downY = null;
            if (moved) {
              return;
            }
          }
          event.preventDefault();
          event.stopPropagation();
          open(list, at, img);
        });
        img.addEventListener('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open(list, at, img);
          }
        });
      })(list[i], i);
    }

    var links = document.querySelectorAll(LINK + '[href^="#"]');
    for (var l = 0; l < links.length; l++) {
      (function (link) {
        var target = document.getElementById(link.getAttribute('href').slice(1));
        if (!target || !target.closest) {
          return;
        }
        var at = indexOfSlide(list, target.closest(SLIDE));
        if (at < 0) {
          return;
        }
        link.addEventListener('click', function (event) {
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
          }
          event.preventDefault();
          open(list, at, link);
        });
      })(links[l]);
    }
  }

  function init() {
    var galleries = document.querySelectorAll(GALLERY);
    for (var i = 0; i < galleries.length; i++) {
      wireGallery(galleries[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
