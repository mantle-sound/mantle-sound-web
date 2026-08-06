// Navbar功能脚本
document.addEventListener('DOMContentLoaded', function() {
  // 汉堡菜单功能
  const hamburger = document.querySelector('.hamburger-icon');
  const navMenu = document.querySelector('.nav-menu');
  
  if (hamburger && navMenu) {
    const hamburgerMenu = document.querySelector('.hamburger-menu');
    
    function setMenuOpen(open) {
      navMenu.classList.toggle('menu-open', open);
      if (hamburgerMenu) {
        hamburgerMenu.classList.toggle('menu-open', open);
        hamburgerMenu.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
    }
    
    hamburger.addEventListener('click', function(e) {
      e.stopPropagation();
      const isOpen = !hamburgerMenu.classList.contains('menu-open');
      setMenuOpen(isOpen);
    });
    
    // 关闭菜单
    function closeMenu() {
      setMenuOpen(false);
      navMenu.querySelectorAll('.nav-dropdown.is-open').forEach(function(el) { el.classList.remove('is-open'); });
    }
    // 点击普通链接时关闭菜单（手风琴的 .dropdown-toggle 由上面单独处理，不关菜单）
    // 电脑端、navbar 已固定时点击站内链接，在新页面恢复同样滚动进度
    const navBoxForSave = document.querySelector('.nav-box');
    navMenu.querySelectorAll('a').forEach(link => {
      if (link.classList.contains('dropdown-toggle') && link.closest('.nav-dropdown-accordion')) return;
      link.addEventListener('click', function() {
        if (navBoxForSave && navBoxForSave.classList.contains('navbar-fixed') && window.innerWidth >= 1300) {
          var href = link.getAttribute('href');
          if (href && (href.indexOf('/') === 0 || (href.indexOf('http') === 0 && new URL(href, location.origin).hostname === location.hostname))) {
            try { sessionStorage.setItem('mantle-navbar-restore-scroll', String(window.pageYOffset)); } catch (e) {}
          }
        }
        closeMenu();
      });
    });
    // 手机端 Contact 手风琴：点击展开/收起，不跳转
    const accordions = navMenu.querySelectorAll('.nav-dropdown-accordion');
    accordions.forEach(function(dropdown) {
      const toggle = dropdown.querySelector('.dropdown-toggle');
      if (!toggle) return;
      toggle.addEventListener('click', function(e) {
        if (window.innerWidth > 1300) return;
        e.preventDefault();
        dropdown.classList.toggle('is-open');
      });
    });
    
    // 点击外部时关闭菜单
    document.addEventListener('click', function(e) {
      if (!hamburgerMenu?.contains(e.target) && !navMenu.contains(e.target)) {
        closeMenu();
      }
    });
  }
  
  // Logo-box滚动缩小逻辑
  const logoBox = document.querySelector('#logo-box');
  const navBox = document.querySelector('.nav-box');
  
  if (logoBox && navBox) {
    const navSentinel = document.createElement('span');
    navSentinel.setAttribute('aria-hidden', 'true');
    navSentinel.style.cssText = 'display:block;width:0;height:0;pointer-events:none';
    navBox.parentNode.insertBefore(navSentinel, navBox);

    let navBoxTop = 0;
    let scrollFrame = null;

    function updateNavBoxTop() {
      navBoxTop = navSentinel.getBoundingClientRect().top + window.pageYOffset;
    }

    function updateMascot() {
      var show =
        navBox.classList.contains('navbar-fixed') &&
        window.matchMedia('(min-width: 1301px)').matches;
      document.body.classList.toggle('has-scroll-mascot', show);
    }

    function handleLogoScroll() {
      if (scrollFrame !== null) return;
      scrollFrame = window.requestAnimationFrame(function() {
        navBox.classList.toggle('navbar-fixed', window.pageYOffset >= navBoxTop);
        updateMascot();
        scrollFrame = null;
      });
    }
    
    updateNavBoxTop();
    handleLogoScroll();
    window.addEventListener('scroll', handleLogoScroll, { passive: true });
    window.addEventListener('resize', function() {
      updateNavBoxTop();
      handleLogoScroll();
    });

    // 从站内菜单点击跳转过来时，恢复相同滚动进度（左上 MAN NETWORK + 固定 menu 状态）
    var savedScroll = sessionStorage.getItem('mantle-navbar-restore-scroll');
    if (savedScroll != null) {
      sessionStorage.removeItem('mantle-navbar-restore-scroll');
      var y = parseInt(savedScroll, 10);
      if (!isNaN(y)) {
        requestAnimationFrame(function() { window.scrollTo(0, y); });
      }
    }
  }
});
