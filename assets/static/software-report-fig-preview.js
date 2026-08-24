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

  function init() {
    var links = document.querySelectorAll('a.' + LINK_CLASS + '[href^="#take002-photo-"]');
    for (var i = 0; i < links.length; i++) {
      attachPreview(links[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
