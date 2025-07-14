(function () {
  /* ========= Preloader ======== */
  const preloader = document.querySelectorAll('#preloader')

  window.addEventListener('load', function () {
    if (preloader.length) {
      this.document.getElementById('preloader').style.display = 'none'
    }
  })

  /* ========= Add Box Shadow in Header on Scroll ======== */
  window.addEventListener('scroll', function () {
    const header = document.querySelector('.header')
    if (window.scrollY > 0) {
      header.style.boxShadow = '0px 0px 30px 0px rgba(200, 208, 216, 0.30)'
    } else {
      header.style.boxShadow = 'none'
    }
  })

  /* ========= sidebar toggle ======== */
  const sidebarNavWrapper = document.querySelector('.sidebar-nav-wrapper')
  const mainWrapper = document.querySelector('.main-wrapper')
  const menuToggleButton = document.querySelector('#menu-toggle')
  const menuToggleButtonIcon = document.querySelector('#menu-toggle i')
  const overlay = document.querySelector('.overlay')

  menuToggleButton.addEventListener('click', () => {
    sidebarNavWrapper.classList.toggle('active')
    overlay.classList.add('active')
    mainWrapper.classList.toggle('active')

    if (document.body.clientWidth > 1200) {
      if (menuToggleButtonIcon.classList.contains('lni-chevron-left')) {
        menuToggleButtonIcon.classList.remove('lni-chevron-left')
        menuToggleButtonIcon.classList.add('lni-menu')
      } else {
        menuToggleButtonIcon.classList.remove('lni-menu')
        menuToggleButtonIcon.classList.add('lni-chevron-left')
      }
    } else {
      if (menuToggleButtonIcon.classList.contains('lni-chevron-left')) {
        menuToggleButtonIcon.classList.remove('lni-chevron-left')
        menuToggleButtonIcon.classList.add('lni-menu')
      }
    }
  })
  overlay.addEventListener('click', () => {
    sidebarNavWrapper.classList.remove('active')
    overlay.classList.remove('active')
    mainWrapper.classList.remove('active')
  })

  // ========== theme switcher ==========
  const optionButton = document.querySelector('.option-btn')
  const optionButtonClose = document.querySelector('.option-btn-close')
  const optionBox = document.querySelector('.option-box')
  const optionOverlay = document.querySelector('.option-overlay')

  optionButton.addEventListener('click', () => {
    optionBox.classList.add('show')
    optionOverlay.classList.add('show')
  })
  optionButtonClose.addEventListener('click', () => {
    optionBox.classList.remove('show')
    optionOverlay.classList.remove('show')
  })
  optionOverlay.addEventListener('click', () => {
    optionOverlay.classList.remove('show')
    optionBox.classList.remove('show')
  })

  // ========== layout change
  const leftSidebarButton = document.querySelector('.leftSidebarButton')
  const rightSidebarButton = document.querySelector('.rightSidebarButton')
  const dropdownMenuEnd = document.querySelectorAll(
    '.header-right .dropdown-menu'
  )

  rightSidebarButton.addEventListener('click', () => {
    document.body.classList.add('rightSidebar')
    rightSidebarButton.classList.add('active')
    leftSidebarButton.classList.remove('active')

    dropdownMenuEnd.forEach((el) => {
      el.classList.remove('dropdown-menu-end')
    })
  })
  leftSidebarButton.addEventListener('click', () => {
    document.body.classList.remove('rightSidebar')
    leftSidebarButton.classList.add('active')
    rightSidebarButton.classList.remove('active')

    dropdownMenuEnd.forEach((el) => {
      el.classList.add('dropdown-menu-end')
    })
  })

  // =========== theme change
  const lightThemeButton = document.querySelector('.lightThemeButton')
  const darkThemeButton = document.querySelector('.darkThemeButton')
  const logo = document.querySelector('.navbar-logo img')

  // Check if the user has a saved theme preference
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark') {
    document.body.classList.add('darkTheme')
    darkThemeButton.classList.add('active')
    lightThemeButton.classList.remove('active')
    logo.src = 'assets/images/logo/logo-white.svg'
  } else {
    document.body.classList.remove('darkTheme')
    lightThemeButton.classList.add('active')
    darkThemeButton.classList.remove('active')
    logo.src = 'assets/images/logo/logo.svg'
  }

  darkThemeButton.addEventListener('click', () => {
    document.body.classList.add('darkTheme')
    localStorage.setItem('theme', 'dark') // Save theme preference
    darkThemeButton.classList.add('active')
    lightThemeButton.classList.remove('active')
    logo.src = 'assets/images/logo/logo-white.svg'
  })

  lightThemeButton.addEventListener('click', () => {
    document.body.classList.remove('darkTheme')
    localStorage.setItem('theme', 'light') // Save theme preference
    lightThemeButton.classList.add('active')
    darkThemeButton.classList.remove('active')
    logo.src = 'assets/images/logo/logo.svg'
  })

  // Enabling bootstrap tooltips
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  )
  const tooltipList = [...tooltipTriggerList].map(
    (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl)
  )
})();
