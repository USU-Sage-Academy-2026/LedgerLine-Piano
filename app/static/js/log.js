// Log practice page: piece info, minute chips and note templates.
const pieceSelect = document.getElementById("piece");
const minutesInput = document.getElementById("minutes");
const note = document.getElementById("note");

if (pieceSelect) {
  // Show the chosen piece's stage, last session and assignment (stored in data-* on each <option>).
  const showPiece = () => {
    const opt = pieceSelect.selectedOptions[0];
    document.getElementById("pieceInfo").textContent = `${opt.dataset.stage} · ${opt.dataset.last}`;
    document.getElementById("assignment").textContent = opt.dataset.assignment || "No assignment yet.";
  };
  pieceSelect.addEventListener("change", showPiece);
  showPiece();

  // Minute chips fill the number box; typing in the box un-presses the chips.
  const chips = document.querySelectorAll("#chips .chip");
  const pressChip = () => chips.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.min === minutesInput.value)));
  chips.forEach((chip) => chip.addEventListener("click", () => {
    minutesInput.value = chip.dataset.min;
    pressChip();
  }));
  minutesInput.addEventListener("input", pressChip);
  pressChip();

  // Note templates add text at the end, if it fits in 500 characters.
  document.querySelectorAll("[data-template]").forEach((btn) => btn.addEventListener("click", () => {
    const add = (note.value && !note.value.endsWith("\n") ? "\n" : "") + btn.dataset.template;
    if (note.value.length + add.length > note.maxLength) {
      alert("That template doesn’t fit in 500 characters. Shorten your note first.");
      return;
    }
    note.value += add;
    note.dispatchEvent(new Event("input"));   // updates the counter in app.js
    note.focus();
  }));

  // "Clear form" (type=reset) also resets the chips after the browser clears the fields.
  document.getElementById("logForm").addEventListener("reset", () => setTimeout(() => { pressChip(); showPiece(); note.dispatchEvent(new Event("input")); }));
}
