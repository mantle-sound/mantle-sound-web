(function () {
  var ROOT = '[data-home-gallery]';
  var SWIPE_PX = 48;
  var AUTO_MS = 6000;

  function isGalleryControl(target) {
    return (
      target &&
      target.closest &&
      target.closest('.home-gallery__prev, .home-gallery__next, .home-gallery__dot')
    );
  }

  function maxSlideHeight() {
    if (window.innerWidth <= 600) {
      return 220;
    }
    if (window.innerWidth <= 1300) {
      return 280;
    }
    return 380;
  }

  function initGallery(root) {
    if (root.dataset.homeGalleryReady === 'true') {
      return;
    }
    var viewport = root.querySelector('.home-gallery__viewport');
    var track = root.querySelector('.home-gallery__track');
    var slides = root.querySelectorAll('.home-gallery__slide');
    if (!viewport || !track || !slides.length) {
      return;
    }

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      track.style.transition = 'none';
    }

    var index = 0;
    var count = slides.length;
    var prevBtn = root.querySelector('.home-gallery__prev');
    var nextBtn = root.querySelector('.home-gallery__next');
    var dots = root.querySelectorAll('.home-gallery__dot');

    function syncViewportHeight() {
      var slide = slides[index];
      if (!slide) {
        return;
      }
      var img = slide.querySelector('img');
      if (!img) {
        return;
      }
      var apply = function () {
        var maxH = maxSlideHeight();
        var width = viewport.clientWidth;
        if (!width || !img.naturalWidth || !img.naturalHeight) {
          return;
        }
        var scaled = Math.round(width * (img.naturalHeight / img.naturalWidth));
        viewport.style.height = Math.min(maxH, scaled) + 'px';
      };
      if (img.complete) {
        apply();
      } else {
        img.addEventListener('load', apply, { once: true });
      }
    }

    function setIndex(next) {
      index = (next + count) % count;
      track.style.transform = 'translate3d(' + -index * 100 + '%,0,0)';
      for (var i = 0; i < dots.length; i++) {
        dots[i].classList.toggle('is-active', i === index);
        dots[i].setAttribute('aria-selected', i === index ? 'true' : 'false');
      }
      if (prevBtn) {
        prevBtn.disabled = count <= 1;
      }
      if (nextBtn) {
        nextBtn.disabled = count <= 1;
      }
      syncViewportHeight();
    }

    var autoTimer = null;

    function stopAuto() {
      if (autoTimer !== null) {
        window.clearInterval(autoTimer);
        autoTimer = null;
      }
    }

    function startAuto() {
      stopAuto();
      if (reduceMotion || count <= 1) {
        return;
      }
      autoTimer = window.setInterval(function () {
        go(1);
      }, AUTO_MS);
    }

    function restartAuto() {
      stopAuto();
      startAuto();
    }

    function go(delta) {
      setIndex(index + delta);
      restartAuto();
    }

    if (prevBtn) {
      prevBtn.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        go(-1);
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        go(1);
      });
    }

    for (var d = 0; d < dots.length; d++) {
      (function (dotIndex) {
        dots[dotIndex].addEventListener('click', function (event) {
          event.preventDefault();
          event.stopPropagation();
          setIndex(dotIndex);
          restartAuto();
        });
      })(d);
    }

    root.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        go(-1);
      } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        go(1);
      }
    });

    var pointerStartX = null;
    var pointerActive = false;
    var blockSlideLinkClick = false;

    root.addEventListener('click', function (event) {
      if (count <= 1) {
        return;
      }
      if (isGalleryControl(event.target)) {
        return;
      }
      var slideLink = event.target.closest('.home-gallery__slide a');
      if (!slideLink) {
        return;
      }
      if (blockSlideLinkClick) {
        blockSlideLinkClick = false;
        event.preventDefault();
        return;
      }
      event.preventDefault();
      go(1);
    });

    root.addEventListener('pointerdown', function (event) {
      if (count <= 1) {
        return;
      }
      if (isGalleryControl(event.target)) {
        return;
      }
      if (event.button !== undefined && event.button !== 0) {
        return;
      }
      pointerActive = true;
      pointerStartX = event.clientX;
      if (root.setPointerCapture) {
        root.setPointerCapture(event.pointerId);
      }
    });

    root.addEventListener('pointerup', function (event) {
      if (!pointerActive || pointerStartX === null) {
        return;
      }
      var delta = event.clientX - pointerStartX;
      pointerActive = false;
      pointerStartX = null;
      if (Math.abs(delta) < SWIPE_PX) {
        return;
      }
      blockSlideLinkClick = true;
      go(delta < 0 ? 1 : -1);
    });

    root.addEventListener('pointercancel', function () {
      pointerActive = false;
      pointerStartX = null;
    });

    for (var s = 0; s < slides.length; s++) {
      var slideImg = slides[s].querySelector('img');
      if (slideImg) {
        slideImg.addEventListener('load', syncViewportHeight);
      }
    }

    if (count <= 1) {
      root.classList.add('home-gallery--single');
    }

    root.addEventListener('mouseenter', stopAuto);
    root.addEventListener('mouseleave', startAuto);
    root.addEventListener('focusin', stopAuto);
    root.addEventListener('focusout', function (event) {
      if (!root.contains(event.relatedTarget)) {
        startAuto();
      }
    });

    setIndex(0);
    startAuto();
    root.dataset.homeGalleryReady = 'true';
  }

  var resizeTimer;
  function onResize() {
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(function () {
      var nodes = document.querySelectorAll(ROOT + '[data-home-gallery-ready="true"]');
      for (var n = 0; n < nodes.length; n++) {
        var viewport = nodes[n].querySelector('.home-gallery__viewport');
        var track = nodes[n].querySelector('.home-gallery__track');
        var slides = nodes[n].querySelectorAll('.home-gallery__slide');
        if (!viewport || !slides.length) {
          continue;
        }
        var active = 0;
        var dots = nodes[n].querySelectorAll('.home-gallery__dot.is-active');
        for (var d = 0; d < dots.length; d++) {
          if (dots[d].classList.contains('is-active')) {
            active = d;
            break;
          }
        }
        var img = slides[active].querySelector('img');
        if (img && img.naturalWidth) {
          var maxH = maxSlideHeight();
          var width = viewport.clientWidth;
          var scaled = Math.round(width * (img.naturalHeight / img.naturalWidth));
          viewport.style.height = Math.min(maxH, scaled) + 'px';
        }
      }
    }, 120);
  }

  function init() {
    var nodes = document.querySelectorAll(ROOT);
    for (var i = 0; i < nodes.length; i++) {
      initGallery(nodes[i]);
    }
    window.addEventListener('resize', onResize);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
