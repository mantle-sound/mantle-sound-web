/* Scroll reveal for homepage sections — Samaya-style fade-up for the image
   column and caption. Text keeps the scramble effect in scramble.js. */
(function () {
  var ROOT = '[data-home-reveal]';

  function revealAll() {
    var nodes = document.querySelectorAll(ROOT);
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].classList.add('is-revealed');
    }
  }

  function start() {
    var nodes = document.querySelectorAll(ROOT);
    if (!nodes.length) return;

    if (
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      revealAll();
      return;
    }

    if (!window.IntersectionObserver) {
      revealAll();
      return;
    }

    var seen = new window.IntersectionObserver(
      function (entries, obs) {
        for (var i = 0; i < entries.length; i++) {
          if (!entries[i].isIntersecting) continue;
          var section = entries[i].target;
          section.classList.add('is-revealed');
          obs.unobserve(section);

          var gallery = section.querySelector('[data-home-gallery]');
          if (!gallery || gallery.dataset.zoomPlayed === 'true') {
            continue;
          }
          var img = gallery.querySelector('.home-gallery__slide.is-active img');
          if (!img) {
            continue;
          }
          img.classList.add('is-zooming');
          img.addEventListener(
            'animationend',
            function () {
              img.classList.remove('is-zooming');
              gallery.dataset.zoomPlayed = 'true';
            },
            { once: true }
          );
        }
      },
      { rootMargin: '0px 0px -12% 0px' }
    );

    for (var j = 0; j < nodes.length; j++) {
      seen.observe(nodes[j]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
