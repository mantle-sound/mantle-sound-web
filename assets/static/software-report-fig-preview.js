(function () {
  var PREVIEW_CLASS = 'software-report__fig-preview';
  var LINK_CLASS = 'software-report__fig-link';

  function galleryPreviewSrc(anchorId) {
    var target = document.getElementById(anchorId);
    if (!target) {
      return null;
    }
    if (target.matches && target.matches('img.software-report__gallery-photo')) {
      return target.currentSrc || target.src;
    }
    var img = target.querySelector('.software-report__gallery-photo');
    return img ? img.currentSrc || img.src : null;
  }

  function attachPreview(link) {
    var href = link.getAttribute('href') || '';
    if (href.charAt(0) !== '#') {
      return;
    }
    var anchorId = href.slice(1);
    var src = galleryPreviewSrc(anchorId);
    if (!src || link.querySelector('.' + PREVIEW_CLASS)) {
      return;
    }

    var wrap = document.createElement('span');
    wrap.className = PREVIEW_CLASS;
    wrap.setAttribute('aria-hidden', 'true');

    var img = document.createElement('img');
    img.src = src;
    img.alt = '';
    img.width = 240;
    img.height = 135;
    img.loading = 'lazy';
    img.decoding = 'async';

    wrap.appendChild(img);
    link.appendChild(wrap);
  }

  // The gallery is a carousel: only the active slide is on screen, so a plain
  // anchor jump to an inactive slide scrolls to a photo nobody can see. On
  // touch there is no hover preview either, which left the Fig. links doing
  // nothing visible at all. Drive the carousel to the slide instead.
  function attachGalleryJump(link) {
    var href = link.getAttribute('href') || '';
    if (href.charAt(0) !== '#') {
      return;
    }
    var target = document.getElementById(href.slice(1));
    if (!target || !target.closest) {
      return;
    }
    var slide = target.closest('.home-gallery__slide');
    var gallery = target.closest('[data-home-gallery]');
    if (!slide || !gallery) {
      return;
    }
    var slides = gallery.querySelectorAll('.home-gallery__slide');
    var index = -1;
    for (var i = 0; i < slides.length; i++) {
      if (slides[i] === slide) {
        index = i;
        break;
      }
    }
    if (index < 0) {
      return;
    }

    link.addEventListener('click', function (event) {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return;
      }
      event.preventDefault();
      gallery.dispatchEvent(
        new CustomEvent('home-gallery:goto', { detail: { index: index } })
      );
      gallery.scrollIntoView({ block: 'center', behavior: 'smooth' });
    });
  }

  function init() {
    var links = document.querySelectorAll('a.' + LINK_CLASS + '[href^="#take002-photo-"]');
    for (var i = 0; i < links.length; i++) {
      attachPreview(links[i]);
      attachGalleryJump(links[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
