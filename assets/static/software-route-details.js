(function () {
  var ROOT_SELECTOR = '[data-software-route-details]';
  var OPEN_CLASS = 'is-open';

  function tapMode() {
    if (window.matchMedia('(hover: none)').matches) {
      return true;
    }
    if (window.matchMedia('(pointer: coarse)').matches) {
      return true;
    }
    return window.innerWidth <= 620;
  }

  function initRoot(root) {
    var trigger = root.querySelector('.software-route-details__summary');
    if (!trigger || trigger.tagName !== 'BUTTON') {
      return;
    }

    trigger.addEventListener('click', function (event) {
      if (!tapMode()) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      var open = !root.classList.contains(OPEN_CLASS);
      root.classList.toggle(OPEN_CLASS, open);
      trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  function closeAll(except) {
    var roots = document.querySelectorAll(ROOT_SELECTOR);
    for (var i = 0; i < roots.length; i++) {
      var root = roots[i];
      if (except && root === except) {
        continue;
      }
      if (!root.classList.contains(OPEN_CLASS)) {
        continue;
      }
      root.classList.remove(OPEN_CLASS);
      var trigger = root.querySelector('.software-route-details__summary');
      if (trigger) {
        trigger.setAttribute('aria-expanded', 'false');
      }
    }
  }

  function init() {
    var roots = document.querySelectorAll(ROOT_SELECTOR);
    for (var i = 0; i < roots.length; i++) {
      initRoot(roots[i]);
    }

    document.addEventListener('click', function (event) {
      if (!tapMode()) {
        return;
      }
      var inside = event.target.closest(ROOT_SELECTOR);
      if (!inside) {
        closeAll(null);
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') {
        return;
      }
      closeAll(null);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
