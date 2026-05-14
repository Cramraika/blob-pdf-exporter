// content.js — runs in page MAIN world after vendor/jspdf.umd.min.js has been
// injected by popup.js. Returns a small result object to the popup.
//
// Adapted from the original IIFE blob→PDF script. MV3-safe:
// - No CDN load (jsPDF is bundled & injected via chrome.scripting).
// - No Trusted Types policy creation (avoids duplicate-policy errors).
// - Returns structured result instead of relying on overlay alone.

(function () {
  const JPEG_Q = 0.92;
  const ALPHA_SAMPLE = 100; // px^2 region sampled for transparency detection

  function el(tag, styles, props) {
    const node = document.createElement(tag);
    if (styles) Object.assign(node.style, styles);
    if (props) Object.assign(node, props);
    return node;
  }

  function createOverlay() {
    const ov = el("div", {
      position: "fixed",
      inset: "0",
      zIndex: "2147483647",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "rgba(0,0,0,0.52)",
      backdropFilter: "blur(3px)",
      fontFamily: "system-ui,sans-serif",
      color: "#fff",
    });
    const box = el("div", {
      background: "#111827",
      borderRadius: "14px",
      padding: "28px 36px",
      minWidth: "270px",
      textAlign: "center",
      boxShadow: "0 12px 40px rgba(0,0,0,0.5)",
    });
    const title = el(
      "div",
      { fontSize: "15px", fontWeight: "600", marginBottom: "18px" },
      { textContent: "Exporting PDF" },
    );
    const track = el("div", {
      background: "#1f2937",
      borderRadius: "6px",
      height: "7px",
      overflow: "hidden",
      marginBottom: "12px",
    });
    const fill = el("div", {
      background: "linear-gradient(90deg,#10B981,#3B82F6)",
      height: "100%",
      width: "0%",
      transition: "width .25s ease",
      borderRadius: "6px",
    });
    const status = el(
      "div",
      { fontSize: "12px", color: "#9ca3af" },
      { textContent: "Starting…" },
    );
    track.appendChild(fill);
    box.append(title, track, status);
    ov.appendChild(box);
    document.body.appendChild(ov);
    return {
      update(done, total) {
        const pct = total ? Math.round((done / total) * 100) : 0;
        fill.style.width = pct + "%";
        status.textContent = total
          ? `Page ${done} of ${total}`
          : "Preparing…";
      },
      error(msg) {
        status.textContent = msg;
        status.style.color = "#f87171";
      },
      remove() {
        ov.remove();
      },
    };
  }

  function getFilename() {
    const raw =
      document
        .querySelector('meta[property="og:title"]')
        ?.content?.trim() ||
      document.querySelector('meta[name="title"]')?.content?.trim() ||
      document.querySelector("h1")?.innerText?.trim() ||
      document.title?.trim() ||
      decodeURIComponent(
        location.pathname.split("/").filter(Boolean).pop() || "",
      )
        .replace(/\.[a-z0-9]+$/i, "")
        .replace(/[-_]+/g, " ") ||
      "download";
    return (
      raw
        .replace(/[\\/:*?"<>|]/g, "")
        .replace(/\s+/g, " ")
        .trim()
        .slice(0, 120) + ".pdf"
    );
  }

  function waitForImage(img) {
    return new Promise((resolve) => {
      if (img.complete && img.naturalWidth > 0) {
        resolve(true);
        return;
      }
      const done = (ok) => {
        img.removeEventListener("load", onLoad);
        img.removeEventListener("error", onErr);
        resolve(ok);
      };
      const onLoad = () => done(true);
      const onErr = () => done(false);
      img.addEventListener("load", onLoad, { once: true });
      img.addEventListener("error", onErr, { once: true });
    });
  }

  function hasTransparency(canvas) {
    try {
      const ctx = canvas.getContext("2d");
      const data = ctx.getImageData(
        0,
        0,
        Math.min(canvas.width, ALPHA_SAMPLE),
        Math.min(canvas.height, ALPHA_SAMPLE),
      ).data;
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] < 255) return true;
      }
    } catch {
      // tainted canvas — assume opaque
    }
    return false;
  }

  function encodeCanvas(canvas) {
    if (hasTransparency(canvas)) {
      return { imgData: canvas.toDataURL("image/png"), format: "PNG" };
    }
    return {
      imgData: canvas.toDataURL("image/jpeg", JPEG_Q),
      format: "JPEG",
    };
  }

  function freeCanvas(c) {
    c.width = 0;
    c.height = 0;
  }

  function collectBlobImages() {
    const seen = new Set();
    return Array.from(document.querySelectorAll("img"))
      .filter((img) => {
        const src = img.currentSrc || img.src;
        if (!src?.startsWith("blob:") || seen.has(src)) return false;
        seen.add(src);
        return true;
      })
      .sort((a, b) => {
        const ra = a.getBoundingClientRect();
        const rb = b.getBoundingClientRect();
        const dy = ra.top + scrollY - (rb.top + scrollY);
        return Math.abs(dy) > 10 ? dy : ra.left - rb.left;
      });
  }

  // Synchronous entry that returns a promise wrapper for the popup.
  async function run() {
    if (!window.jspdf?.jsPDF) {
      return {
        success: false,
        message: "jsPDF failed to load (vendor inject blocked?).",
      };
    }
    const { jsPDF } = window.jspdf;

    const images = collectBlobImages();
    if (!images.length) {
      return {
        success: false,
        message: "No blob: images found on this page.",
        found: 0,
        added: 0,
      };
    }

    const ui = createOverlay();
    ui.update(0, images.length);

    let pdf = null;
    let added = 0;

    try {
      for (let i = 0; i < images.length; i++) {
        const img = images[i];
        const loaded = await waitForImage(img);
        if (!loaded) continue;

        const w = img.naturalWidth || img.width;
        const h = img.naturalHeight || img.height;
        if (!w || !h) continue;

        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;

        const ctx = canvas.getContext("2d");
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";

        try {
          ctx.drawImage(img, 0, 0, w, h);
        } catch (e) {
          console.warn("[blob-pdf-exporter] cross-origin draw blocked:", img.src, e);
          freeCanvas(canvas);
          continue;
        }

        let imgData;
        let format;
        try {
          ({ imgData, format } = encodeCanvas(canvas));
        } catch (e) {
          console.warn("[blob-pdf-exporter] encode failed:", img.src, e);
          freeCanvas(canvas);
          continue;
        }

        const orientation = w >= h ? "landscape" : "portrait";
        if (!pdf) {
          pdf = new jsPDF({
            orientation,
            unit: "px",
            format: [w, h],
            compress: true,
          });
        } else {
          pdf.addPage([w, h], orientation);
        }
        pdf.addImage(imgData, format, 0, 0, w, h);
        freeCanvas(canvas);
        added++;

        ui.update(i + 1, images.length);
        await new Promise((r) => setTimeout(r, 0));
      }

      if (!pdf || added === 0) {
        ui.error("No pages could be added.");
        await new Promise((r) => setTimeout(r, 1500));
        ui.remove();
        return {
          success: false,
          message: "No pages could be added.",
          found: images.length,
          added: 0,
        };
      }

      pdf.save(getFilename());
      ui.remove();
      return {
        success: true,
        message: `Exported ${added} pages.`,
        found: images.length,
        added,
      };
    } catch (e) {
      ui.error("Export failed: " + e.message);
      await new Promise((r) => setTimeout(r, 1500));
      ui.remove();
      return {
        success: false,
        message: `Export failed: ${e.message}`,
        found: images.length,
        added,
      };
    }
  }

  return run();
})();
