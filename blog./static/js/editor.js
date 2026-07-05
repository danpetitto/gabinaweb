/* Quill WYSIWYG editor for article body. Inline images upload to the server
   (re-encoded, stored locally) so the editor never holds base64 blobs. */
(function () {
  "use strict";

  const quill = new Quill("#editor", {
    theme: "snow",
    placeholder: "Začněte psát…",
    modules: {
      toolbar: {
        container: [
          [{ header: [2, 3, 4, false] }],
          ["bold", "italic", "underline", "strike"],
          ["blockquote", "code-block"],
          [{ list: "ordered" }, { list: "bullet" }],
          ["link", "image"],
          ["clean"],
        ],
        handlers: { image: imageHandler },
      },
    },
  });

  if (INITIAL) {
    quill.clipboard.dangerouslyPasteHTML(INITIAL);
  }

  function imageHandler() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/png,image/jpeg,image/webp,image/gif";
    input.onchange = async () => {
      const file = input.files && input.files[0];
      if (!file) return;
      if (file.size > 8 * 1024 * 1024) {
        alert("Soubor je příliš velký (max 8 MB).");
        return;
      }
      const range = quill.getSelection(true);
      quill.insertText(range.index, "Nahrávám obrázek…", { italic: true });

      try {
        const fd = new FormData();
        fd.append("image", file);
        const res = await fetch(UPLOAD_URL, {
          method: "POST",
          headers: { "X-CSRFToken": CSRF },
          body: fd,
        });
        quill.deleteText(range.index, "Nahrávám obrázek…".length);
        if (!res.ok) throw new Error("upload failed");
        const data = await res.json();
        quill.insertEmbed(range.index, "image", data.url);
        quill.setSelection(range.index + 1);
      } catch (err) {
        quill.deleteText(range.index, "Nahrávám obrázek…".length);
        alert("Obrázek se nepodařilo nahrát.");
      }
    };
    input.click();
  }

  // Cover preview
  const coverInput = document.getElementById("cover-input");
  const coverPreview = document.getElementById("cover-preview");
  coverInput.addEventListener("change", () => {
    const file = coverInput.files && coverInput.files[0];
    if (!file) return;
    coverPreview.src = URL.createObjectURL(file);
    coverPreview.style.display = "block";
  });

  // Sync editor HTML into hidden input on submit
  const form = document.getElementById("article-form");
  form.addEventListener("submit", function (e) {
    const html = quill.getSemanticHTML();
    if (!quill.getText().trim()) {
      e.preventDefault();
      alert("Obsah článku nemůže být prázdný.");
      return;
    }
    document.getElementById("body-input").value = html;
  });
})();
