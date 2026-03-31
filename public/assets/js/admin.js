(function () {
  document.addEventListener("DOMContentLoaded", init);

  function init() {
    const shared = window.RICCEShared;
    const config = shared.getConfig();
    const runtimeConfig = document.getElementById("runtimeConfig");
    const configLinks = document.getElementById("configLinks");
    const nextSteps = document.getElementById("nextSteps");

    const runtimeRows = [
      ["App name", config.appName],
      ["Data mode", shared.labelMode(config.dataMode)],
      ["CSV path", config.csvDataPath],
      ["Apps Script URL", config.appsScriptWebAppUrl || "Not configured"],
      ["Admin mode", shared.labelMode(config.adminMode)],
      ["Admin sheet URL", config.adminSheetUrl || "Not configured"],
      ["Allowed emails", shared.toArray(config.adminAllowedEmails).join(", ") || "None configured"],
      ["Debug UI", config.debugUi ? "Enabled" : "Disabled"]
    ];

    runtimeConfig.innerHTML = runtimeRows
      .map(
        ([label, value]) =>
          `<div><dt>${shared.escapeHtml(label)}</dt><dd>${shared.escapeHtml(value)}</dd></div>`
      )
      .join("");

    const links = [
      config.adminSheetUrl
        ? `<li><a class="text-link" href="${shared.escapeHtml(config.adminSheetUrl)}" target="_blank" rel="noreferrer">Open admin Google Sheet</a></li>`
        : "<li>Admin Google Sheet URL is not configured yet.</li>",
      config.appsScriptWebAppUrl
        ? `<li><a class="text-link" href="${shared.escapeHtml(config.appsScriptWebAppUrl)}" target="_blank" rel="noreferrer">Open Apps Script endpoint</a></li>`
        : "<li>Apps Script web app URL is not configured yet.</li>",
      '<li><a class="text-link" href="/data/ricce-ontology-sample.csv">Inspect the bundled sample dataset</a></li>',
      "<li>Local private preview path: /data/local/ricce-ontology-private-preview.csv</li>"
    ];

    configLinks.innerHTML = links.join("");

    const tasks = [
      config.dataMode === "csv"
        ? "Keep the default site on the sample CSV and use the local preview CSV only for private local review."
        : "Verify the Apps Script endpoint returns sanitized JSON to anonymous callers.",
      config.appsScriptWebAppUrl
        ? "Smoke-test the Apps Script endpoint before switching production dataMode to apps_script."
        : "Deploy the Google Apps Script integration and then set appsScriptWebAppUrl in site-config.js.",
      config.adminSheetUrl
        ? "Confirm Google Sheet sharing is limited to approved admins."
        : "Create the protected admin Google Sheet and add its URL to site-config.js.",
      "Run scripts/security-checks.sh before your first Firebase deploy and after major data/model changes."
    ];

    nextSteps.innerHTML = tasks.map((task) => `<li>${shared.escapeHtml(task)}</li>`).join("");
  }
})();
