/*====== MENU TOGGLE =====*/
const showMenu = (toggleId, navId) => {
    const toggle = document.getElementById(toggleId),
          nav = document.getElementById(navId);
  
    if (toggle && nav) {
      toggle.addEventListener('click', () => {
        nav.classList.toggle('show');
      });
    }
  };
  showMenu('nav-toggle', 'nav-menu');
  
  /*====== RELLAX PARALLAX =====*/
  new Rellax('.parallax');
  
  /*====== GSAP ANIMATIONS =====*/
  /* Navbar Entrance */
  gsap.from('.nav__logo', {
    opacity: 0,
    duration: 3,
    delay: 0.5,
    y: 30,
    ease: 'expo.out'
  });
  gsap.from('.nav__toggle', {
    opacity: 0,
    duration: 3,
    delay: 0.7,
    y: 30,
    ease: 'expo.out'
  });
  gsap.from('.nav__item', {
    opacity: 0,
    duration: 3,
    delay: 0.7,
    y: 35,
    ease: 'expo.out',
    stagger: 0.2
  });
  
  /* Home Text */
  gsap.from('.home__title', {
    opacity: 0,
    duration: 3,
    delay: 1.3,
    y: 35,
    ease: 'expo.out'
  });
  gsap.from('.home__subtitle', {
    opacity: 0,
    duration: 3,
    delay: 1.1,
    y: 35,
    ease: 'expo.out'
  });
  gsap.from('.home__scroll', {
    opacity: 0,
    duration: 3,
    delay: 1.5,
    y: 25,
    ease: 'expo.out'
  });
  
  /*====== SCROLL REVEAL ======*/
  const sr = ScrollReveal({
    distance: '50px',
    duration: 1000,
    easing: 'ease-in-out',
    origin: 'bottom',
    interval: 100,
    reset: false,
    beforeReveal: function (el) {
      el.classList.add('reveal-visible');
    },
    beforeReset: function (el) {
      el.classList.remove('reveal-visible');
    }
  });
  
  /* Sections */
  sr.reveal('.section__data', { origin: 'left', distance: '70px' });
  sr.reveal('.section__img', { origin: 'right', distance: '90px', delay: 200 });
  sr.reveal('.gauge__card', { origin: 'bottom', interval: 200, beforeReveal: function(el) { el.classList.add('reveal-visible'); }, beforeReset: function(el) { el.classList.remove('reveal-visible'); } });
  sr.reveal('.summary__card', { origin: 'bottom', delay: 300 });
  sr.reveal('.btn-checkup, .btn-report', { origin: 'bottom', delay: 400, interval: 100 });
