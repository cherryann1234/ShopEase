// Small progressive-enhancement helpers. All data interactions use HTMX.
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector(".nav-toggle");
  var links = document.getElementById("nav-links");

  if (toggle && links) {
    var setOpen = function (open) {
      links.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    };

    toggle.addEventListener("click", function () {
      setOpen(!links.classList.contains("open"));
    });

    // Close the mobile menu after navigating, and on Escape.
    links.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && links.classList.contains("open")) {
        setOpen(false);
        toggle.focus();
      }
    });
    document.addEventListener("click", function (event) {
      if (links.classList.contains("open") && !event.target.closest(".navbar")) {
        setOpen(false);
      }
    });
  }
});

// HTMX ignores 4xx responses by default. Let 404 inline error partials be swapped in.
document.addEventListener("htmx:beforeSwap", function (event) {
  if (event.detail.xhr.status === 404) {
    event.detail.shouldSwap = true;
    event.detail.isError = false;
  }
});
