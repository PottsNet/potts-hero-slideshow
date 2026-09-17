(function () {
  'use strict';

  const TRANSITION_EFFECTS = ['fade', 'zoom', 'slide-left', 'slide-up', 'blur'];
  const TRANSITION_CLASSES = TRANSITION_EFFECTS.concat(['random']).map(function (effect) {
    return 'ourfamily-hero-transition-' + effect;
  });

  function normaliseTransition(value) {
    if (value === 'random') {
      return 'random';
    }

    return TRANSITION_EFFECTS.includes(value) ? value : 'zoom';
  }

  function chooseTransition(hero, instant) {
    const configured = normaliseTransition(hero.dataset.transition || 'zoom');

    if (instant) {
      return configured === 'random' ? 'zoom' : configured;
    }

    if (configured !== 'random') {
      return configured;
    }

    let effect = TRANSITION_EFFECTS[Math.floor(Math.random() * TRANSITION_EFFECTS.length)] || 'fade';
    const previous = hero.dataset.currentTransition || '';

    if (TRANSITION_EFFECTS.length > 1 && effect === previous) {
      const index = TRANSITION_EFFECTS.indexOf(effect);
      effect = TRANSITION_EFFECTS[(index + 1) % TRANSITION_EFFECTS.length];
    }

    return effect;
  }

  function setTransitionClass(hero, effect) {
    hero.classList.remove.apply(hero.classList, TRANSITION_CLASSES);
    hero.classList.add('ourfamily-hero-transition-' + effect);
    hero.dataset.currentTransition = effect;
  }


  function getOverlayCaptionOffset(hero) {
    const raw = hero.dataset.captionOffset || window.getComputedStyle(hero).getPropertyValue('--ourfamily-hero-overlay-caption-offset') || '20';
    const parsed = Number.parseInt(String(raw).replace('px', ''), 10);

    return Number.isFinite(parsed) ? Math.min(160, Math.max(0, parsed)) : 20;
  }

  function applyOverlayCaptionOffset(hero) {
    if (!hero || !hero.classList.contains('ourfamily-hero-caption-overlay')) {
      return;
    }

    const offset = getOverlayCaptionOffset(hero);
    hero.style.setProperty('--ourfamily-hero-overlay-caption-offset', offset + 'px');

    hero.querySelectorAll('.ourfamily-hero-slide figcaption').forEach(function (caption) {
      caption.style.setProperty('bottom', offset + 'px', 'important');
    });
  }

  function activateHeroSlide(hero, slides, dots, index, instant) {
    const current = slides.findIndex(function (slide) {
      return slide.classList.contains('is-active');
    });

    const effect = chooseTransition(hero, Boolean(instant));
    setTransitionClass(hero, effect);

    const parsedTransitionSpeed = Number.parseInt(hero.dataset.transitionSpeed || '1150', 10);
    const transitionSpeed = Number.isFinite(parsedTransitionSpeed) ? Math.min(5000, Math.max(300, parsedTransitionSpeed)) : 1150;

    applyOverlayCaptionOffset(hero);

    slides.forEach(function (slide) {
      slide.classList.remove('is-exiting');
    });

    if (!instant && current >= 0 && current !== index && slides[current]) {
      slides[current].classList.add('is-exiting');
      window.setTimeout(function () {
        slides[current].classList.remove('is-exiting');
      }, transitionSpeed + 150);
    }

    slides.forEach(function (slide, slideIndex) {
      slide.classList.toggle('is-active', slideIndex === index);
      slide.setAttribute('aria-hidden', slideIndex === index ? 'false' : 'true');
    });

    dots.forEach(function (dot, dotIndex) {
      dot.classList.toggle('is-active', dotIndex === index);
      dot.setAttribute('aria-pressed', dotIndex === index ? 'true' : 'false');
    });

    Array.from(hero.querySelectorAll('.ourfamily-hero-caption-item')).forEach(function (caption, captionIndex) {
      caption.classList.toggle('is-active', captionIndex === index);
      caption.setAttribute('aria-hidden', captionIndex === index ? 'false' : 'true');
    });

    hero.dataset.activeSlide = String(index);
  }

  function initialiseHeroSlideshows() {
    const reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.querySelectorAll('.ourfamily-hero').forEach(function (hero) {
      if (hero.dataset.pottsHeroInitialised === '1') {
        return;
      }

      const slides = Array.from(hero.querySelectorAll('.ourfamily-hero-slide'));

      if (slides.length === 0) {
        return;
      }

      hero.dataset.pottsHeroInitialised = '1';
      hero.dataset.activeSlide = '0';
      applyOverlayCaptionOffset(hero);

      let dots = [];

      if (hero.dataset.dots === '0') {
        const existingDots = hero.querySelector('.ourfamily-hero-dots');
        if (existingDots) {
          existingDots.remove();
        }
      }

      if (slides.length > 1 && hero.dataset.dots !== '0') {
        let dotsContainer = hero.querySelector('.ourfamily-hero-dots');

        if (!dotsContainer) {
          dotsContainer = document.createElement('div');
          dotsContainer.className = 'ourfamily-hero-dots';
          dotsContainer.setAttribute('aria-label', 'Hero image selector');
          hero.appendChild(dotsContainer);
        } else {
          dotsContainer.textContent = '';
        }

        slides.forEach(function (_slide, index) {
          const dot = document.createElement('button');
          dot.type = 'button';
          dot.className = 'ourfamily-hero-dot';
          dot.setAttribute('aria-label', 'Show hero image ' + String(index + 1));
          dot.addEventListener('click', function () {
            activateHeroSlide(hero, slides, dots, index, false);
          });
          dotsContainer.appendChild(dot);
          dots.push(dot);
        });
      }

      const startIndex = hero.dataset.randomStart === '1' && slides.length > 1
        ? Math.floor(Math.random() * slides.length)
        : 0;

      activateHeroSlide(hero, slides, dots, startIndex, true);

      if (slides.length < 2 || reducedMotion) {
        return;
      }

      const parsedInterval = Number.parseInt(hero.dataset.interval || '7000', 10);
      const interval = Number.isFinite(parsedInterval) ? Math.max(3500, parsedInterval) : 7000;
      let paused = false;

      hero.addEventListener('mouseenter', function () {
        paused = true;
      });

      hero.addEventListener('mouseleave', function () {
        paused = false;
      });

      window.setInterval(function () {
        if (paused) {
          return;
        }

        const current = Number.parseInt(hero.dataset.activeSlide || '0', 10) || 0;
        activateHeroSlide(hero, slides, dots, (current + 1) % slides.length, false);
      }, interval);
    });
  }

  function updateSlideSortValues(list) {
    Array.from(list.querySelectorAll('.potts-hero-slide-row')).forEach(function (row, index) {
      const input = row.querySelector('.potts-hero-sort-input');
      if (input) {
        input.value = String(index + 1);
      }
    });
  }

  function moveRow(row, direction) {
    const list = row && row.parentElement;
    if (!list) {
      return;
    }

    if (direction < 0 && row.previousElementSibling) {
      list.insertBefore(row, row.previousElementSibling);
    }

    if (direction > 0 && row.nextElementSibling) {
      list.insertBefore(row.nextElementSibling, row);
    }

    updateSlideSortValues(list);
    row.focus({ preventScroll: true });
  }

  function initialiseSlideOrdering() {
    document.querySelectorAll('.potts-hero-slides[data-sortable="1"]').forEach(function (list) {
      if (list.dataset.pottsSortableInitialised === '1') {
        return;
      }

      list.dataset.pottsSortableInitialised = '1';
      let draggedRow = null;

      list.querySelectorAll('.potts-hero-slide-row').forEach(function (row) {
        row.setAttribute('tabindex', '0');

        row.addEventListener('dragstart', function (event) {
          draggedRow = row;
          row.classList.add('is-dragging');
          if (event.dataTransfer) {
            event.dataTransfer.effectAllowed = 'move';
            event.dataTransfer.setData('text/plain', row.dataset.slideFile || '');
          }
        });

        row.addEventListener('dragend', function () {
          row.classList.remove('is-dragging');
          list.querySelectorAll('.drag-over').forEach(function (item) {
            item.classList.remove('drag-over');
          });
          draggedRow = null;
          updateSlideSortValues(list);
        });

        row.addEventListener('dragover', function (event) {
          if (!draggedRow || draggedRow === row) {
            return;
          }

          event.preventDefault();
          row.classList.add('drag-over');
          const rect = row.getBoundingClientRect();
          const before = event.clientY < rect.top + rect.height / 2;

          if (before) {
            list.insertBefore(draggedRow, row);
          } else {
            list.insertBefore(draggedRow, row.nextSibling);
          }
        });

        row.addEventListener('dragleave', function () {
          row.classList.remove('drag-over');
        });
      });

      list.addEventListener('click', function (event) {
        const up = event.target.closest('.potts-hero-move-up');
        const down = event.target.closest('.potts-hero-move-down');

        if (up) {
          moveRow(up.closest('.potts-hero-slide-row'), -1);
        }

        if (down) {
          moveRow(down.closest('.potts-hero-slide-row'), 1);
        }
      });

      updateSlideSortValues(list);
    });
  }

  function initialise() {
    initialiseHeroSlideshows();
    initialiseSlideOrdering();

    const captionOffsetInput = document.getElementById('potts-hero-caption-offset');
    if (captionOffsetInput) {
      captionOffsetInput.addEventListener('input', function () {
        const value = String(this.value || '20');
        document.querySelectorAll('.ourfamily-hero').forEach(function (hero) {
          hero.dataset.captionOffset = value;
          applyOverlayCaptionOffset(hero);
        });
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialise);
  } else {
    initialise();
  }
})();
