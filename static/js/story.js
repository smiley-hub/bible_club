(() => {
  const journey = document.querySelector('[data-journey]');
  if (!journey) return;
  const road = journey.querySelector('[data-history-road]');
  const opener = journey.querySelector('[data-open-journey]');
  const chapters = [...journey.querySelectorAll('[data-chapter]')];
  const selector = journey.querySelector('[data-chapter-select]');
  const track = journey.querySelector('[data-timeline]');
  const previous = journey.querySelector('[data-timeline-previous]');
  const next = journey.querySelector('[data-timeline-next]');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  let folding;
  function updateControls() {
    previous.disabled = track.scrollLeft < 2;
    next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;
  }
  function goToChapter(chapter, focus = false) {
    if (focus) {
      chapter.tabIndex = -1;
      chapter.focus({preventScroll:true});
    }
    track.scrollTo({left:chapter.offsetLeft, behavior:reduced.matches ? 'instant' : 'smooth'});
    selector.value = chapter.id;
  }
  function step(direction) {
    const index = chapters.reduce((closest, item, i) =>
      Math.abs(item.offsetLeft - track.scrollLeft) < Math.abs(chapters[closest].offsetLeft - track.scrollLeft) ? i : closest, 0);
    goToChapter(chapters[Math.max(0, Math.min(chapters.length - 1, index + direction))]);
  }
  function openJourney(scroll = true) {
    if (folding) {
      folding.cancel();
      folding = null;
    }
    road.inert = false;
    if (opener.getAttribute('aria-expanded') === 'true') return;
    road.hidden = false;
    journey.classList.add('is-open');
    opener.setAttribute('aria-expanded', 'true');
    opener.querySelector('small').textContent = 'Fold our story';
    journey.querySelector('.journey-hint').textContent = 'Swipe through the years, or press the wheel again to fold it back.';
    updateControls();
    if (scroll) road.scrollIntoView({behavior: reduced.matches ? 'instant' : 'smooth', block: 'start'});
  }
  function closeJourney() {
    opener.focus({preventScroll:true});
    opener.setAttribute('aria-expanded', 'false');
    opener.querySelector('small').textContent = 'Unroll our story';
    journey.querySelector('.journey-hint').textContent = 'Press the wheel, then scroll through the years.';
    journey.classList.remove('is-open');
    road.inert = true;
    const finish = () => {
      road.hidden = true;
      folding?.cancel();
      folding = null;
      chapters.forEach(chapter => chapter.classList.remove('is-arriving'));
    };
    if (reduced.matches || !road.animate) {
      finish();
      return;
    }
    folding = road.animate([
      {height:`${road.offsetHeight}px`, opacity:1, clipPath:'inset(0 0 0 0)', overflow:'hidden'},
      {height:'0px', opacity:0, clipPath:'inset(0 0 100% 0)', overflow:'hidden'}
    ], {duration:550, easing:'cubic-bezier(.4,0,.2,1)', fill:'forwards'});
    folding.onfinish = finish;
  }
  journey.classList.add('is-enhanced');
  road.hidden = true;
  journey.querySelector('[data-journey-nav]').hidden = false;
  journey.querySelector('[data-road-toolbar]').hidden = false;
  opener.addEventListener('click', () => {
    if (opener.getAttribute('aria-expanded') === 'true') closeJourney();
    else openJourney();
  });
  selector.addEventListener('change', () => goToChapter(document.getElementById(selector.value), true));
  journey.querySelector('[data-timeline-navigation]').hidden = false;
  previous.addEventListener('click', () => step(-1));
  next.addEventListener('click', () => step(1));
  track.addEventListener('scroll', updateControls, {passive:true});
  track.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'Home') goToChapter(chapters[0]);
    else if (event.key === 'End') goToChapter(chapters[chapters.length - 1]);
    else step(event.key === 'ArrowRight' ? 1 : -1);
  });
  function followHash() {
    const chapter = chapters.find(item => `#${item.id}` === location.hash);
    if (chapter) {
      openJourney(false);
      requestAnimationFrame(() => goToChapter(chapter));
    }
  }
  window.addEventListener('hashchange', followHash);
  window.addEventListener('resize', updateControls);
  if ('ResizeObserver' in window) new ResizeObserver(updateControls).observe(track);
  followHash();
})();
