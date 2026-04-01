window.RICCEShared = (() => {
  const MODE_LABELS = {
    csv: "Publish-safe CSV",
    apps_script: "Apps Script + Google Sheet",
    sheet: "Protected Google Sheet",
    functions: "Firebase Functions"
  };
  const APP_ROOT_PATH = (() => {
    const currentScript = document.currentScript;
    if (currentScript instanceof HTMLScriptElement && currentScript.src) {
      const rootUrl = new URL("../../", currentScript.src);
      return rootUrl.pathname.endsWith("/") ? rootUrl.pathname : `${rootUrl.pathname}/`;
    }

    return "/";
  })();

  function resolveAppPath(candidate) {
    const value = String(candidate ?? "").trim();

    if (!value) {
      return "";
    }

    if (/^[a-z][a-z0-9+.-]*:/i.test(value) || value.startsWith("//")) {
      return value;
    }

    const normalized = value.replace(/^\/+/, "");
    return `${APP_ROOT_PATH}${normalized}`.replace(/\/{2,}/g, "/");
  }

  function getConfig() {
    if (!window.RICCE_SITE_CONFIG) {
      throw new Error("Missing RICCE_SITE_CONFIG.");
    }

    return window.RICCE_SITE_CONFIG;
  }

  function getCsvOverridePath() {
    const params = new URLSearchParams(window.location.search);
    const candidate = params.get("csv");

    if (!candidate) {
      return "";
    }

    if (/^\/?data\/[A-Za-z0-9/_\.-]+\.csv$/.test(candidate)) {
      return resolveAppPath(candidate);
    }

    return "";
  }

  function getRuntimeCsvPath(config) {
    return getCsvOverridePath() || resolveAppPath(config.csvDataPath);
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setStatus(element, message, tone = "info") {
    if (!element) {
      return;
    }

    element.textContent = message;
    element.classList.remove("is-success", "is-warning", "is-error");

    if (tone === "success") {
      element.classList.add("is-success");
    } else if (tone === "warning") {
      element.classList.add("is-warning");
    } else if (tone === "error") {
      element.classList.add("is-error");
    }
  }

  function labelMode(mode) {
    return MODE_LABELS[mode] || mode || "Not configured";
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  return {
    escapeHtml,
    getConfig,
    resolveAppPath,
    getRuntimeCsvPath,
    labelMode,
    setStatus,
    toArray
  };
})();
