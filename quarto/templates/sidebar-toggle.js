(() => {
  const sidebar = document.querySelector("#quarto-sidebar");
  if (!sidebar) return;
  sidebar.setAttribute("data-mechanics-sidebar", "ready");
})();
