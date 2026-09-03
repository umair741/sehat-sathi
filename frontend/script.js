// Sehat Sathi — Landing Page

// ---------- Scroll Reveal ----------
const revealables = document.querySelectorAll(
  ".feature-card, .condition-card, .trust-card, .step-card, .emergency-card, .example-box, .stats-bar, .problem-stat, .mission-card, .impact-card, .audience-card"
);

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.08 }
);

revealables.forEach((el) => observer.observe(el));

// ---------- Smooth scroll ----------
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    const target = document.querySelector(this.getAttribute("href"));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});
