/* ==========================================================================
   Theme switcher (설정 창)
   - 모드: light / dark / system
   - 라이트 테마, 다크 테마를 각각 고르고, 모드에 따라 둘 중 하나가 적용된다.
   - 선택값은 localStorage 에 저장한다.
     jominsong.github.io 아래의 모든 프로젝트 사이트가 같은 localStorage 를
     공유하므로 키 앞에 'jms-theme-' 를 붙여서 다른 앱과 겹치지 않게 한다.
   - head.html 의 인라인 스크립트가 페이지가 그려지기 전에 같은 규칙으로
     data-theme 을 먼저 붙인다(깜빡임 방지). 여기서는 UI 와 이후 변경을 담당한다.
   ========================================================================== */
(function () {
  'use strict';

  var KEY = 'jms-theme-';
  var root = document.documentElement;
  var box = document.getElementById('theme-switcher');
  if (!box) { return; }

  var toggle = document.getElementById('theme-switcher-toggle');
  var panel = document.getElementById('theme-switcher-panel');
  var closeBtn = box.querySelector('.theme-switcher__close');
  var radios = box.querySelectorAll('input[name="theme-mode"]');
  var lightSel = document.getElementById('theme-light');
  var darkSel = document.getElementById('theme-dark');
  var currentLabel = document.getElementById('theme-current');

  // _config.yml 의 theme_switcher 기본값 (include 가 data 속성으로 넘겨준다)
  var DEFAULTS = {
    mode: box.getAttribute('data-default-mode') || 'light',
    light: box.getAttribute('data-default-light') || 'default',
    dark: box.getAttribute('data-default-dark') || 'dark'
  };

  var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var timer = null;

  // ---- 저장소 읽기/쓰기 (사생활 보호 모드 등에서 예외가 나도 동작하게 try/catch) ----
  function read(name, fallback) {
    try {
      var v = window.localStorage.getItem(KEY + name);
      return v ? v : fallback;
    } catch (e) {
      return fallback;
    }
  }
  function write(name, value) {
    try { window.localStorage.setItem(KEY + name, value); } catch (e) { /* 저장 불가: 이번 방문에만 적용 */ }
  }

  // select 안에 실제로 있는 테마인지 검사한다.
  // 저장된 값이 없어졌거나 잘못됐으면 기본값, 기본값도 없으면 첫 항목을 쓴다.
  // (themes.yml 에서 지워진 테마가 저장돼 있을 때 head.html 의 인라인 스크립트와 같은 결과가 나오게 한다)
  function hasOption(select, value) {
    return !!select.querySelector('option[value="' + value + '"]');
  }
  function validTheme(select, stored, preferred) {
    if (hasOption(select, stored)) { return stored; }
    if (hasOption(select, preferred)) { return preferred; }
    return select.options[0].value;
  }

  var state = {
    mode: 'light',
    light: DEFAULTS.light,
    dark: DEFAULTS.dark
  };

  function load() {
    var mode = read('mode', DEFAULTS.mode);
    state.mode = (mode === 'light' || mode === 'dark' || mode === 'system') ? mode : 'light';
    state.light = validTheme(lightSel, read('light', DEFAULTS.light), DEFAULTS.light);
    state.dark = validTheme(darkSel, read('dark', DEFAULTS.dark), DEFAULTS.dark);
  }

  // 지금 실제로 적용할 테마 이름: 모드 -> (라이트 테마 | 다크 테마)
  function resolve() {
    var useDark = state.mode === 'dark' ||
      (state.mode === 'system' && mq && mq.matches);
    return useDark ? state.dark : state.light;
  }

  // 핵심: <html data-theme="..."> 값을 바꾸면 _themes.scss 의 CSS 변수가 통째로 바뀐다.
  // animate 가 true 이면 잠깐 theme-transition 클래스를 붙여 색이 부드럽게 변하게 한다.
  function apply(animate) {
    var theme = resolve();
    if (root.getAttribute('data-theme') === theme) { updateUi(theme); return; }

    if (animate && !reduced) {
      root.classList.add('theme-transition');
      void root.offsetWidth; // 클래스를 먼저 반영시킨 뒤 속성을 바꿔야 전환이 걸린다
      window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        root.classList.remove('theme-transition');
      }, 450);
    }
    root.setAttribute('data-theme', theme);
    updateUi(theme);
  }

  function labelOf(theme) {
    var opt = box.querySelector('option[value="' + theme + '"]');
    return opt ? opt.textContent : theme;
  }

  function updateUi(theme) {
    for (var i = 0; i < radios.length; i++) {
      radios[i].checked = (radios[i].value === state.mode);
    }
    lightSel.value = state.light;
    darkSel.value = state.dark;
    if (currentLabel) { currentLabel.textContent = labelOf(theme); }
  }

  // ---- 입력 이벤트 ----
  for (var i = 0; i < radios.length; i++) {
    radios[i].addEventListener('change', function (e) {
      state.mode = e.target.value;
      write('mode', state.mode);
      apply(true);
    });
  }
  lightSel.addEventListener('change', function () {
    state.light = lightSel.value;
    write('light', state.light);
    apply(true);
  });
  darkSel.addEventListener('change', function () {
    state.dark = darkSel.value;
    write('dark', state.dark);
    apply(true);
  });

  // 시스템 모드일 때 OS 의 라이트/다크 설정이 바뀌면 따라간다
  if (mq) {
    var onSystemChange = function () { if (state.mode === 'system') { apply(true); } };
    if (mq.addEventListener) { mq.addEventListener('change', onSystemChange); }
    else if (mq.addListener) { mq.addListener(onSystemChange); }
  }

  // 다른 탭에서 바꾼 설정도 바로 반영
  window.addEventListener('storage', function (e) {
    if (e.key && e.key.indexOf(KEY) === 0) { load(); apply(true); }
  });

  // ---- 팝업 열기/닫기 ----
  function openPanel() {
    panel.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    var checked = box.querySelector('input[name="theme-mode"]:checked');
    if (checked) { checked.focus(); }
  }
  function closePanel(returnFocus) {
    panel.hidden = true;
    toggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) { toggle.focus(); }
  }

  toggle.addEventListener('click', function () {
    if (panel.hidden) { openPanel(); } else { closePanel(false); }
  });
  closeBtn.addEventListener('click', function () { closePanel(true); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) { closePanel(true); }
  });
  document.addEventListener('click', function (e) {
    if (!panel.hidden && !box.contains(e.target)) { closePanel(false); }
  });

  load();
  apply(false);
})();
