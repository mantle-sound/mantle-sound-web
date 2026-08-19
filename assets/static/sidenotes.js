/* Footnotes become margin notes.
 *
 * Mistune renders a footnote as `<sup class="footnote-ref" id="fnref-N">` in
 * the prose plus an `<li id="fn-N">` in a trailing list. This lifts each item
 * out of that list into an `<aside class="sidenote">` placed right after the
 * block that cites it, then drops the emptied list. Wide viewports push the
 * aside into the free space right of the text column; narrow ones leave it in
 * flow (style.css). Either way the note stays beside the sentence that needs
 * it instead of at the far bottom of the page.
 *
 * Nothing here names a page or a template. The text column is found by walking
 * up from the reference, so a new layout needs no change to this file. */
(function () {
  'use strict';

  /* Prose blocks are not containers: if the walk up from a reference stops on
     one of these, the column is its parent. */
  var PROSE = 'p,ul,ol,dl,blockquote,pre,table,h1,h2,h3,h4,h5,h6';

  function columnFor(ref, page) {
    var el = ref;
    while (el.parentElement && el.parentElement !== page) {
      el = el.parentElement;
    }
    if (el === ref || el.matches(PROSE)) return page;
    return el;
  }

  /* The note goes after the smallest prose block that holds the reference, so
     in flow it lands under the sentence rather than under the whole section.
     A reference inside a list item anchors to the list: <aside> is not
     allowed between one <li> and the next. */
  function blockFor(ref, column) {
    var block = ref.closest(PROSE + ',li,figure,figcaption,td,dd,dt');
    if (block && block.matches('li,dd,dt,td')) {
      block = block.closest('ul,ol,dl,table') || block.parentElement;
    }
    if (block && block !== ref && column.contains(block)) return block;
    var el = ref;
    while (el.parentElement && el.parentElement !== column) {
      el = el.parentElement;
    }
    return el;
  }

  function noteFor(ref) {
    var link = ref.querySelector('a[href^="#"]');
    if (!link) return null;
    return document.getElementById(decodeURIComponent(link.hash.slice(1)));
  }

  function build(ref, index, anchors) {
    var page = ref.closest('.page');
    if (!page) return null;
    var item = noteFor(ref);
    if (!item) return null;

    var column = columnFor(ref, page);
    var block = blockFor(ref, column);

    var aside = document.createElement('aside');
    aside.className = 'sidenote';
    aside.id = 'sidenote-' + index;

    var num = document.createElement('span');
    num.className = 'sidenote__num';
    num.setAttribute('aria-hidden', 'true');
    num.textContent = String(index);
    aside.appendChild(num);

    var body = document.createElement('div');
    body.className = 'sidenote__body';
    while (item.firstChild) body.appendChild(item.firstChild);
    /* The back-reference arrow is for a footnote at the foot of the page. A
       note sitting beside its own sentence has nothing to go back to. */
    var back = body.querySelector('a.footnote');
    if (back) back.remove();
    aside.appendChild(body);

    var list = item.parentElement;
    item.remove();

    column.classList.add('sidenote-host');
    /* Two references in one paragraph anchor to the same block, so the second
       has to follow the first rather than displace it. */
    (anchors.get(block) || block).insertAdjacentElement('afterend', aside);
    anchors.set(block, aside);

    /* Numbering is per markdown field, so a page assembled from two fields —
       a shared intro plus a body, say — restarts at 1 halfway down and emits a
       second fnref-1. Renumber across the whole document, which fixes the
       duplicate ids along with the duplicate numerals. */
    ref.id = 'sidenote-ref-' + index;
    var link = ref.querySelector('a[href^="#"]');
    if (link) {
      link.setAttribute('href', '#' + aside.id);
      link.textContent = String(index);
    }

    return { ref: ref, aside: aside, column: column, list: list };
  }

  function place(notes) {
    /* Only the margin layout needs measuring; in flow the aside is already
       where it belongs. The flag comes from CSS so the breakpoint lives in one
       place. */
    var margin =
      getComputedStyle(document.documentElement)
        .getPropertyValue('--sidenote-margin')
        .trim() === '1';

    document.body.classList.toggle('has-margin-sidenotes', margin);
    if (!margin) {
      notes.forEach(function (note) {
        note.aside.style.removeProperty('top');
      });
      return;
    }

    var bottoms = new Map();
    notes.forEach(function (note) {
      var top =
        note.ref.getBoundingClientRect().top -
        note.column.getBoundingClientRect().top;
      var floor = bottoms.get(note.column);
      if (floor !== undefined && top < floor) top = floor;
      note.aside.style.top = Math.round(top) + 'px';
      bottoms.set(
        note.column,
        top + note.aside.getBoundingClientRect().height + 16
      );
    });
  }

  function init() {
    var refs = Array.prototype.slice.call(
      document.querySelectorAll('sup.footnote-ref')
    );
    if (!refs.length) return;

    var notes = [];
    var lists = new Set();
    var anchors = new Map();
    refs.forEach(function (ref, i) {
      var note = build(ref, i + 1, anchors);
      if (!note) return;
      notes.push(note);
      lists.add(note.list);
    });
    if (!notes.length) return;

    lists.forEach(function (list) {
      if (list.children.length) return;
      /* mistune wraps the list in <div class="footnotes"> with a rule above
         it. Both go with the last item, or the page keeps a stray divider. */
      var wrapper = list.closest('.footnotes');
      list.remove();
      if (wrapper && !wrapper.querySelector('li') && !wrapper.textContent.trim()) {
        wrapper.remove();
      }
    });

    place(notes);

    var pending;
    function reflow() {
      clearTimeout(pending);
      pending = setTimeout(function () {
        place(notes);
      }, 100);
    }
    window.addEventListener('resize', reflow);
    /* Images and web fonts settle after load and move the text under the
       notes, so measure once more when they have. */
    window.addEventListener('load', reflow);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
