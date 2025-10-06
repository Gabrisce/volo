document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".applause-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const postId = btn.dataset.postId;
      if (!postId) return;

      try {
        const res = await fetch(`/posts/${postId}/applause`, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        if (!res.ok) throw new Error("Errore applauso");

        const data = await res.json();
        const countEl = btn.querySelector(".applause-count");
        if (!countEl) return;

        if (data.status === "added") {
          countEl.textContent = parseInt(countEl.textContent) + 1;
          btn.classList.add("active");
          // 👇 trigger animazione
          btn.classList.add("applause-animate");
          setTimeout(() => btn.classList.remove("applause-animate"), 500);
        } else if (data.status === "removed") {
          countEl.textContent = Math.max(0, parseInt(countEl.textContent) - 1);
          btn.classList.remove("active");
        }
      } catch (err) {
        console.error("Errore applauso:", err);
      }
    });
  });
});
