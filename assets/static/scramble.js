/* Scramble-reveal for the homepage section headings.
 *
 * Mechanism follows musicforprogramming.net; the implementation here is our
 * own. Per frame the string is composed of three bands:
 *
 *     settled text | noise | not-yet-reached (spaces)
 *
 * The reveal front advances on a squared sine-ease, so it starts slow. The
 * noise band width follows a triangle envelope — zero at both ends, widest
 * halfway through — which is what stops it reading as a plain typewriter
 * wipe. Characters inside the band settle probabilistically rather than
 * flipping until the front reaches them.
 *
 * The effect walks to text nodes, so inline markup inside a heading survives.
 * The original strings are kept and restored on any failure: a heading must
 * never be left blank because an animation threw.
 */
(function () {
  var NOISE = '—~±§|[].+$^@*()•x%!?#';
  var SETTLE = 0.35; // default chance a rewrite lands the real character

  /* Homepage headings sit near the top and fire on load. Report sidenotes are
     scattered down a very long page, so they wait until they scroll into view
     — firing them all at load would spend the effect off-screen. Their band is
     much wider because a sidenote paragraph is many times longer than a
     heading; a 34-character band on 200 characters reads as a slow wipe. */
  var GROUPS = [
    { selector: '.home-sections h2.intro-h',
      duration: 1400, band: 34, stagger: 0, observe: true,
      colour: true, palette: 'v' },
    /* The section descriptions trail their heading by a beat, so each block
       resolves top-down rather than everything moving at once. Their band is
       wider because a description is four times the length of its heading. */
    { selector: '.home-sections .home-intro__text p',
      duration: 1600, band: 70, stagger: 0, delay: 260, observe: true,
      colour: true, palette: 'm', settle: 0.16 },
    { selector: '.sidenote .sidenote__body',
      duration: 1800, band: 90, stagger: 0, observe: true },
    /* Software index cards. Observed rather than fired on load for the same
       reason as the sidenotes: the tool cards sit below the fold. The tool
       headings wrap their name in <code> next to an <img> mark — the walker
       only collects text nodes, so the mark is left alone. */
    { selector: '.software-test-note-promo__title, .software-tool-column-heading',
      duration: 1400, band: 34, stagger: 0, observe: true, colour: true,
      pinColumn: true },
    { selector: '.software-tool-card .blog-post-card-info p',
      duration: 1600, band: 70, stagger: 0, delay: 260, observe: true,
      colour: true, palette: 'm', settle: 0.16, pinColumn: true }
  ];

  function prefersReducedMotion() {
    return (
      window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    );
  }

  function textNodes(root) {
    var out = [];
    var kids = root.childNodes;
    for (var i = 0; i < kids.length; i++) {
      var node = kids[i];
      if (node.nodeType === 3) {
        if (node.nodeValue.trim() === '') continue;
        node.nodeValue = node.nodeValue.replace(/[\n\r\t]/g, '');
        out.push(node);
      } else if (node.nodeType === 1) {
        out.push.apply(out, textNodes(node));
      }
    }
    return out;
  }

  function noiseChar() {
    return NOISE.charAt((Math.random() * NOISE.length) | 0);
  }

  function overwrite(str, at, ch) {
    if (at < 0 || at > str.length - 1) return str;
    return str.substring(0, at) + ch + str.substring(at + 1);
  }

  function pinSoftwareColumn(el) {
    var column = el.closest('.software-tool-column');
    if (!column) return null;
    var count = Number(column.dataset.scramblePin || 0);
    if (!count) {
      var columnWidth = column.getBoundingClientRect().width;
      column.style.minWidth = columnWidth + 'px';
      column.style.maxWidth = columnWidth + 'px';
    }
    column.dataset.scramblePin = String(count + 1);
    return column;
  }

  function unpinSoftwareColumn(column) {
    if (!column) return;
    var count = Math.max(0, Number(column.dataset.scramblePin || 0) - 1);
    if (!count) {
      column.style.minWidth = '';
      column.style.maxWidth = '';
      delete column.dataset.scramblePin;
    } else {
      column.dataset.scramblePin = String(count);
    }
  }

  function run(el, duration, band, colour, palette, settle, pinColumn) {
    var nodes = textNodes(el);
    if (!nodes.length) return;

    var column = pinColumn ? pinSoftwareColumn(el) : null;

    var lengths = [];
    var target = '';
    for (var i = 0; i < nodes.length; i++) {
      lengths.push(nodes[i].nodeValue.length);
      target += nodes[i].nodeValue;
    }
    if (!target.length) return;

    var blank = new Array(target.length + 1).join(' ');
    var buffer = blank;

    /* Colouring a single character means wrapping it, and a text node cannot
       carry a colour. So each text node is swapped for a shell <span> that the
       per-character spans live in, and swapped back on restore. Only text
       nodes are touched, so the <img> mark and the <code> element around a
       tool name survive the animation untouched. */
    var shells = null;
    if (colour) {
      shells = [];
      for (var n = 0; n < nodes.length; n++) {
        var shell = document.createElement('span');
        nodes[n].parentNode.replaceChild(shell, nodes[n]);
        shells.push(shell);
      }
    }

    function paintPlain(str) {
      var cursor = 0;
      for (var i = 0; i < nodes.length; i++) {
        nodes[i].nodeValue = str.slice(cursor, cursor + lengths[i]);
        cursor += lengths[i];
      }
    }

    function paintColour(str, from, to) {
      var cursor = 0;
      for (var i = 0; i < shells.length; i++) {
        var frag = document.createDocumentFragment();
        var run_ = '';
        for (var j = 0; j < lengths[i]; j++) {
          var at = cursor + j;
          var ch = str.charAt(at);
          if (at >= from && at < to && ch !== ' ') {
            if (run_) { frag.appendChild(document.createTextNode(run_)); run_ = ''; }
            var sp = document.createElement('span');
            sp.className =
              'scramble-ch scramble-ch--' + palette + (1 + ((Math.random() * 4) | 0));
            sp.textContent = ch;
            frag.appendChild(sp);
          } else {
            run_ += ch;
          }
        }
        if (run_) frag.appendChild(document.createTextNode(run_));
        shells[i].textContent = '';
        shells[i].appendChild(frag);
        cursor += lengths[i];
      }
    }

    function paint(str, from, to) {
      if (colour) paintColour(str, from, to || 0);
      else paintPlain(str);
    }

    function restore() {
      if (colour && shells) {
        for (var i = 0; i < shells.length; i++) {
          nodes[i].nodeValue = target.slice(
            lengths.slice(0, i).reduce(function (a, b) { return a + b; }, 0),
            lengths.slice(0, i + 1).reduce(function (a, b) { return a + b; }, 0)
          );
          if (shells[i].parentNode) {
            shells[i].parentNode.replaceChild(nodes[i], shells[i]);
          }
        }
        shells = null;
      } else {
        paintPlain(target);
      }
      el.style.minHeight = '';
      unpinSoftwareColumn(column);
    }

    // Blanking the text would collapse the heading box and shove the page
    // around for the length of the animation, so the height is pinned first.
    el.style.minHeight = el.getBoundingClientRect().height + 'px';

    // Whatever happens to the animation, the heading is readable again.
    var safety = window.setTimeout(restore, duration + 2000);
    var started = null;

    function frame(now) {
      try {
        if (started === null) started = now;
        var raw = Math.min((now - started) / duration, 1);
        var eased = Math.pow(-(Math.cos(Math.PI * raw) - 1) / 2, 2);
        var front = (target.length * eased) | 0;
        var width = (2 * (0.5 - Math.abs(raw - 0.5)) * band) | 0;

        if (raw > 0 && raw < 1 && Math.random() < 0.5) {
          for (var k = 0; k < 20; k++) {
            var at = front + (((1 - Math.random()) * band * (k / 20)) | 0);
            if (target.charAt(at) !== ' ' && target.charAt(at) !== '') {
              buffer = overwrite(
                buffer,
                at,
                Math.random() < settle ? target.charAt(at) : noiseChar()
              );
            }
          }
        }

        paint(
          target.slice(0, front) +
            buffer.slice(front, front + width) +
            blank.slice(front + width),
          front,
          front + width
        );

        if (raw < 1) {
          window.requestAnimationFrame(frame);
        } else {
          window.clearTimeout(safety);
          restore();
        }
      } catch (err) {
        window.clearTimeout(safety);
        restore();
      }
    }

    window.requestAnimationFrame(frame);
  }

  function fire(el, group) {
    try {
      run(el, group.duration, group.band, group.colour, group.palette || '',
          typeof group.settle === 'number' ? group.settle : SETTLE,
          !!group.pinColumn);
    } catch (err) {
      /* element keeps its server-rendered text */
    }
  }

  function onLoadGroup(els, group) {
    var base = group.delay || 0;
    for (var i = 0; i < els.length; i++) {
      (function (el, delay) {
        window.setTimeout(function () { fire(el, group); }, delay);
      })(els[i], base + i * group.stagger);
    }
  }

  function onScrollGroup(els, group) {
    // Without IntersectionObserver the text simply stays as rendered, which
    // is the correct fallback for a decorative reveal.
    if (!window.IntersectionObserver) return;
    var base = group.delay || 0;
    var seen = new window.IntersectionObserver(function (entries, obs) {
      for (var i = 0; i < entries.length; i++) {
        if (!entries[i].isIntersecting) continue;
        obs.unobserve(entries[i].target); // once only
        (function (el) {
          window.setTimeout(function () { fire(el, group); }, base);
        })(entries[i].target);
      }
    }, { rootMargin: '0px 0px -15% 0px' });
    for (var j = 0; j < els.length; j++) seen.observe(els[j]);
  }

  function start() {
    if (prefersReducedMotion()) return;
    if (!window.requestAnimationFrame) return;
    for (var g = 0; g < GROUPS.length; g++) {
      var group = GROUPS[g];
      var els = document.querySelectorAll(group.selector);
      if (!els.length) continue;
      if (group.observe) onScrollGroup(els, group);
      else onLoadGroup(els, group);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
