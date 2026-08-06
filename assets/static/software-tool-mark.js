(function () {
  var markSrc = document.body && document.body.getAttribute('data-software-tool-mark');
  if (!markSrc) {
    return;
  }

  var toolNames = { soundcite: true, lowdom: true };

  function insertMarkBefore(code) {
    if (
      code.previousElementSibling &&
      code.previousElementSibling.classList.contains('software-tool-mark')
    ) {
      return;
    }
    var img = document.createElement('img');
    img.src = markSrc;
    img.alt = '';
    img.className = 'software-tool-mark';
    img.setAttribute('aria-hidden', 'true');
    img.width = 20;
    img.height = 20;
    img.decoding = 'async';
    code.parentNode.insertBefore(img, code);
  }

  function decorateHeadingCodes(root) {
    root.querySelectorAll(':is(h2, h3) > code').forEach(function (code) {
      var name = (code.textContent || '').trim();
      if (toolNames[name]) {
        insertMarkBefore(code);
      }
    });
  }

  function init() {
    document.querySelectorAll('.software-report, .software-tools-grid').forEach(decorateHeadingCodes);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
