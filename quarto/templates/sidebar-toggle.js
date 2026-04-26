/**
 * sidebar-toggle.js
 * 左・右サイドバーの折りたたみトグルボタンを追加する
 */
document.addEventListener('DOMContentLoaded', function () {

  // ── 左サイドバー ──────────────────────────────────────────
  const leftSidebar = document.getElementById('quarto-sidebar');
  if (leftSidebar) {
    const btn = document.createElement('button');
    btn.id = 'left-sidebar-toggle';
    btn.setAttribute('aria-label', '左サイドバーを折りたたむ');
    btn.innerHTML = '&#8249;'; // ‹

    document.body.appendChild(btn);

    // 初期位置をサイドバー右端に合わせる
    function positionLeftBtn() {
      const rect = leftSidebar.getBoundingClientRect();
      const visible = rect.width > 10;
      btn.innerHTML = visible ? '&#8249;' : '&#8250;'; // ‹ / ›
      btn.style.left = visible ? (rect.right - 14) + 'px' : '0px';
    }
    positionLeftBtn();

    btn.addEventListener('click', function () {
      const isVisible = leftSidebar.getBoundingClientRect().width > 10;
      if (isVisible) {
        leftSidebar.style.width = '0';
        leftSidebar.style.minWidth = '0';
        leftSidebar.style.overflow = 'hidden';
        leftSidebar.style.padding = '0';
        btn.innerHTML = '&#8250;'; // ›
        btn.style.left = '0px';
      } else {
        leftSidebar.style.width = '';
        leftSidebar.style.minWidth = '';
        leftSidebar.style.overflow = '';
        leftSidebar.style.padding = '';
        btn.innerHTML = '&#8249;'; // ‹
        requestAnimationFrame(() => {
          btn.style.left = (leftSidebar.getBoundingClientRect().right - 14) + 'px';
        });
      }
    });
  }

  // ── 右サイドバー ──────────────────────────────────────────
  const rightSidebar = document.getElementById('quarto-margin-sidebar');
  if (rightSidebar) {
    const btn = document.createElement('button');
    btn.id = 'right-sidebar-toggle';
    btn.setAttribute('aria-label', '右サイドバーを折りたたむ');
    btn.innerHTML = '&#8250;'; // ›

    document.body.appendChild(btn);

    function positionRightBtn() {
      const rect = rightSidebar.getBoundingClientRect();
      const visible = rect.width > 10;
      btn.style.left = visible ? (rect.left - 14) + 'px' : (window.innerWidth - 14) + 'px';
    }
    positionRightBtn();

    btn.addEventListener('click', function () {
      const isVisible = rightSidebar.getBoundingClientRect().width > 10;
      if (isVisible) {
        rightSidebar.style.width = '0';
        rightSidebar.style.minWidth = '0';
        rightSidebar.style.overflow = 'hidden';
        rightSidebar.style.padding = '0';
        btn.innerHTML = '&#8249;'; // ‹
        btn.style.left = (window.innerWidth - 14) + 'px';
      } else {
        rightSidebar.style.width = '';
        rightSidebar.style.minWidth = '';
        rightSidebar.style.overflow = '';
        rightSidebar.style.padding = '';
        btn.innerHTML = '&#8250;'; // ›
        requestAnimationFrame(() => positionRightBtn());
      }
    });

    window.addEventListener('resize', positionRightBtn);
  }
});
