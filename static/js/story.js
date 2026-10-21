(() => {
  'use strict';
  const journey = document.querySelector('[data-journey]');
  if (!journey) return;
  const chapters = Array.from(journey.querySelectorAll('[data-chapter]'));
  const buttons = Array.from(journey.querySelectorAll('[data-chapter-button]'));
  if (!chapters.length || buttons.length !== chapters.length) return;
  const orbit = journey.querySelector('[data-wheel-orbit]');
  const previous = journey.querySelector('[data-history-previous]');
  const next = journey.querySelector('[data-history-next]');
  const select = journey.querySelector('[data-chapter-select]');
  const counter = journey.querySelector('[data-chapter-counter]');
  const year = journey.querySelector('[data-wheel-year]');
  const status = journey.querySelector('[data-history-status]');
  let current = 0;

  function show(index, announce = true) {
    current = Math.max(0, Math.min(index, chapters.length - 1));
    // Up to eight stops per wheel keeps long histories usable on phones.
    const start = Math.floor(current / 8) * 8;
    const count = Math.min(8, chapters.length - start);
    const rotation = -(current - start) * 360 / count;
    orbit.style.setProperty('--turn', `${rotation}deg`);
    orbit.style.setProperty('--counter-turn', `${-rotation}deg`);
    chapters.forEach((chapter, i) => { chapter.hidden = i !== current; });
    buttons.forEach((button, i) => {
      const visible = i >= start && i < start + count;
      button.hidden = !visible;
      button.setAttribute('aria-pressed', String(i === current));
      if (visible) {
        const angle = ((i - start) * 360 / count - 90) * Math.PI / 180;
        button.style.left = `${50 + Math.cos(angle) * 42}%`;
        button.style.top = `${50 + Math.sin(angle) * 42}%`;
      }
    });
    previous.disabled = current === 0;
    next.disabled = current === chapters.length - 1;
    counter.textContent = `${current + 1} / ${chapters.length}`;
    year.textContent = buttons[current].dataset.year;
    select.value = String(current);
    if (announce) status.textContent = `Chapter ${current + 1} of ${chapters.length}. ${buttons[current].getAttribute('aria-label')}`;
  }
  buttons.forEach((button, index) => {
    button.addEventListener('click', () => show(index));
    button.addEventListener('keydown', (event) => {
      const key = event.key;
      if (!['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp', 'Home', 'End'].includes(key)) return;
      event.preventDefault();
      const target = key === 'Home' ? 0 : key === 'End' ? chapters.length - 1 : current + (['ArrowRight', 'ArrowDown'].includes(key) ? 1 : -1);
      show(target);
      buttons[current].focus();
    });
  });
  previous.addEventListener('click', () => { show(current - 1); if (previous.disabled) next.focus(); });
  next.addEventListener('click', () => { show(current + 1); if (next.disabled) previous.focus(); });
  select.addEventListener('change', () => show(Number(select.value)));
  journey.classList.add('is-enhanced');
  journey.querySelector('[data-journey-nav]').hidden = false;
  show(0, false);
})();
