// Highlight every occurrence of the word selected in the word index.
(() => {
  const words = document.querySelectorAll(".lyrics a[data-word]");
  function highlightWord() {
    const selected = new URLSearchParams(window.location.search).get("highlight");
    const target = selected?.toLowerCase().replaceAll("'", "’");
    let firstMatch;
    for (const word of words) {
      const matches = word.dataset.word === target;
      word.classList.toggle("word-highlight", matches);
      if (matches && !firstMatch) firstMatch = word;
    }
    if (firstMatch && !window.location.hash) {
      firstMatch.scrollIntoView({ block: "center" });
    }
  }
  highlightWord();
  window.addEventListener("popstate", highlightWord);
})();
