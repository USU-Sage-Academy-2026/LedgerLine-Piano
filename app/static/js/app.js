// Small helpers used on every app page (loaded by base.html).

// ---------- Light / Dark toggle ----------
// No saved choice = follow the device. A click saves the opposite of what's showing now.
const root = document.documentElement;
const themeBtn = document.getElementById("themeBtn");
const deviceDark = matchMedia("(prefers-color-scheme: dark)");
const isDark = () => (root.dataset.theme || (deviceDark.matches ? "dark" : "light")) === "dark";

function showThemeButton() {
  themeBtn.textContent = isDark() ? "Light" : "Dark";             // the button names what it switches TO
  themeBtn.setAttribute("aria-pressed", String(isDark()));
  themeBtn.setAttribute("aria-label", isDark() ? "Switch to light mode" : "Switch to dark mode");
}
themeBtn.addEventListener("click", () => {
  const next = isDark() ? "light" : "dark";
  root.dataset.theme = next;
  try { localStorage.setItem("ll-theme", next); } catch (e) {}   // private browsing can block storage
  showThemeButton();
  window.dispatchEvent(new Event("themechange"));               // charts listen for this and redraw
});
deviceDark.addEventListener("change", showThemeButton);
showThemeButton();

// ---------- Forms ----------
document.addEventListener("submit", (e) => {
  const form = e.target;
  // Destructive forms carry data-confirm="Question?" and only submit after OK.
  if (form.dataset.confirm && !confirm(form.dataset.confirm)) { e.preventDefault(); return; }
  // Stop double submits. (Not `disabled`: a disabled button's name/value wouldn't be sent.)
  if (form.dataset.sending) { e.preventDefault(); return; }
  form.dataset.sending = "1";
  const btn = e.submitter;
  if (btn && btn.textContent.trim().length > 1) btn.textContent = btn.textContent.trim() + "…";
});

// ---------- Live character counters: <textarea data-count="#counterId" maxlength="500"> ----------
document.querySelectorAll("textarea[data-count]").forEach((area) => {
  const out = document.querySelector(area.dataset.count);
  const update = () => {
    out.textContent = `${area.value.length}/${area.maxLength}`;
    out.classList.toggle("over", area.value.length >= area.maxLength);
  };
  area.addEventListener("input", update);
  update();
});

// ---------- Copy buttons: data-copy="#inputId" or data-copy-text="value" ----------
document.querySelectorAll("[data-copy], [data-copy-text]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const text = btn.dataset.copyText ?? document.querySelector(btn.dataset.copy).value;
    const label = btn.textContent;
    try {
      await navigator.clipboard.writeText(text);
      btn.textContent = "Copied ✓";
    } catch (err) {
      btn.textContent = "Press Ctrl+C";                         // clipboard blocked: select it instead
      if (btn.dataset.copy) document.querySelector(btn.dataset.copy).select();
    }
    setTimeout(() => (btn.textContent = label), 2000);
  });
});
