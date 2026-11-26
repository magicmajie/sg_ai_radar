// Category filter on the event list. Works without JS (all events shown).
(function () {
  var chips = document.querySelectorAll('.chip[data-filter]');
  if (!chips.length) return;
  var empty = document.querySelector('.filter-empty');

  function apply(cat) {
    chips.forEach(function (c) { c.classList.toggle('is-on', c.dataset.filter === cat); });
    var shown = 0;
    document.querySelectorAll('[data-day]').forEach(function (day) {
      var n = 0;
      day.querySelectorAll('.ev').forEach(function (ev) {
        var on = cat === 'all' || ev.dataset.cat === cat;
        ev.hidden = !on;
        if (on) n++;
      });
      day.hidden = n === 0;
      var count = day.querySelector('.day-n');
      if (count) count.textContent = n + ' 场';
      shown += n;
    });
    if (empty) empty.hidden = shown !== 0;
  }

  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      apply(c.dataset.filter);
      history.replaceState(null, '', c.dataset.filter === 'all' ? location.pathname : '#' + c.dataset.filter);
    });
  });
  var h = location.hash.slice(1);
  if (h === 'tech' || h === 'community') apply(h);
})();
