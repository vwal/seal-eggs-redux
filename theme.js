(() => {
  const key = "sealegs-redux-theme";
  const query = window.matchMedia("(prefers-color-scheme: dark)");
  let selected;
  try { selected = localStorage.getItem(key); } catch {}
  function apply() {
    const dark = selected === "night" || (selected !== "day" && query.matches);
    document.documentElement.dataset.theme = dark ? "night" : "day";
    const control = document.getElementById("theme");
    if (control) {
      control.setAttribute("aria-checked", String(dark));
      control.querySelector("span").textContent = dark ? "Night" : "Day";
    }
  }
  apply();
  query.addEventListener("change", apply);
  document.addEventListener("DOMContentLoaded", () => {
    apply();
    const control = document.getElementById("theme");
    control.hidden = false;
    control.addEventListener("click", () => {
      selected = document.documentElement.dataset.theme === "night" ? "day" : "night";
      try { localStorage.setItem(key, selected); } catch {}
      apply();
    });
  });
})();
