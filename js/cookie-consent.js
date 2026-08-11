// Studio GH — cookie consent lišta (GA4 Consent Mode v2, default je nastaven v <head>)

(function () {
  const KEY = "cookieConsent";

  const stored = (() => {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  })();
  if (stored) return;

  const bar = document.createElement("div");
  bar.className = "cookie-bar";
  bar.setAttribute("role", "dialog");
  bar.setAttribute("aria-label", "Souhlas s cookies");
  bar.innerHTML =
    '<p class="cookie-bar-text">' +
    "Používáme cookies k měření návštěvnosti (Google Analytics). " +
    'Nezbytné cookies jsou aktivní vždy. <a class="link-underline" href="ochrana-osobnich-udaju.html">Více informací</a>' +
    "</p>" +
    '<div class="cookie-bar-actions">' +
    '<button type="button" class="btn btn-sm" data-consent="granted">Přijmout vše</button>' +
    '<button type="button" class="btn btn-ghost btn-sm" data-consent="denied">Pouze nezbytné</button>' +
    "</div>";
  document.body.appendChild(bar);

  // krátká prodleva, aby proběhla vstupní animace (rAF se v neaktivním tabu nespustí)
  setTimeout(() => bar.classList.add("is-visible"), 60);

  bar.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-consent]");
    if (!btn) return;
    const value = btn.getAttribute("data-consent");
    try {
      localStorage.setItem(KEY, value);
    } catch (err) {}
    if (value === "granted" && typeof gtag === "function") {
      gtag("consent", "update", { analytics_storage: "granted" });
    }
    bar.classList.remove("is-visible");
    setTimeout(() => bar.remove(), 500);
  });
})();
