(() => {
  'use strict';
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-nav');
  if (menu && nav) {
    document.documentElement.classList.add('js-enabled');
    menu.hidden = false;
    const closeMenu = () => { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); };
    menu.addEventListener('click', () => {
      const opened = nav.classList.toggle('is-open');
      menu.setAttribute('aria-expanded', String(opened));
    });
    nav.addEventListener('click', (event) => { if (event.target.closest('a')) closeMenu(); });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) { closeMenu(); menu.focus(); }
    });
  }

  // Expand in-page details when a link points directly at a collapsed section.
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', () => {
      const target = document.getElementById(link.getAttribute('href').slice(1));
      if (target?.tagName === 'DETAILS') target.open = true;
    });
  });

  const carousel = document.querySelector('[data-slideshow]');
  if (!carousel) return;
  const slides = Array.from(carousel.querySelectorAll('[data-slide]'));
  if (slides.length < 2) return;
  const toggle = carousel.querySelector('[data-photo-toggle]');
  const status = carousel.querySelector('[data-slide-status]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let current = 0;
  let paused = reducedMotion.matches;
  let timer;
  toggle.hidden = false;

  function updateTimer() {
    window.clearInterval(timer);
    toggle.setAttribute('aria-label', paused ? 'Resume photo slideshow' : 'Pause photo slideshow');
    toggle.title = paused ? 'Click to resume the slideshow' : 'Click to pause the slideshow';
    carousel.dataset.paused = String(paused);
    if (!paused && !document.hidden) timer = window.setInterval(() => show(current + 1, false), 6500);
  }
  function show(index, manual = true) {
    slides[current].hidden = true;
    current = (index + slides.length) % slides.length;
    slides[current].hidden = false;
    if (manual) {
      paused = true;
      status.textContent = `Photo ${current + 1} of ${slides.length}. Slideshow paused.`;
      updateTimer();
    }
  }
  toggle.addEventListener('click', () => {
    paused = !paused;
    status.textContent = paused ? 'Slideshow paused. Activate the photo to resume.' : 'Slideshow playing. Activate the photo to pause.';
    updateTimer();
  });
  toggle.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      show(current + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) paused = true; updateTimer(); });
  document.addEventListener('visibilitychange', updateTimer);
  updateTimer();
})();
