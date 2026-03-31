(function () {
  const DEFAULT_LENGTHS = {
    centerToArea: 250,
    areaToOrg: 150,
    orgToPerson: 80
  };

  const nodes = new vis.DataSet();
  const edges = new vis.DataSet();
  let network = null;

  document.addEventListener("DOMContentLoaded", init);

  async function init() {
    const shared = window.RICCEShared;
    const config = shared.getConfig();
    const elements = getElements();

    renderRuntimeMetadata(elements, config, shared);
    wireControls(elements, shared);

    try {
      const rows = await loadConfiguredRows(config);

      if (!rows.length) {
        throw new Error("The configured dataset is empty after public-field sanitization.");
      }

      buildGraph(rows, elements);
      updateStats(rows, elements);
      shared.setStatus(
        elements.statusMessage,
        `Loaded ${rows.length} publish-safe records from ${shared.labelMode(config.dataMode)}.`,
        "success"
      );
    } catch (error) {
      console.error(error);
      elements.fileFallback.classList.remove("is-hidden");
      shared.setStatus(
        elements.statusMessage,
        `${error.message} Use the manual CSV fallback if needed.`,
        "warning"
      );
    }
  }

  function getElements() {
    return {
      profileCount: document.getElementById("profileCount"),
      organizationCount: document.getElementById("organizationCount"),
      serviceAreaCount: document.getElementById("serviceAreaCount"),
      statusMessage: document.getElementById("statusMessage"),
      fileFallback: document.getElementById("fileFallback"),
      csvFileInput: document.getElementById("csvFileInput"),
      searchInput: document.getElementById("searchInput"),
      btnSearch: document.getElementById("btnSearch"),
      btnReset: document.getElementById("btnReset"),
      sliderArea: document.getElementById("sliderArea"),
      sliderOrg: document.getElementById("sliderOrg"),
      sliderName: document.getElementById("sliderName"),
      panelTitle: document.getElementById("panelTitle"),
      panelContent: document.getElementById("panelContent"),
      selectionPlaceholder: document.getElementById("selectionPlaceholder"),
      dataModeLabel: document.getElementById("dataModeLabel"),
      dataSourceLabel: document.getElementById("dataSourceLabel"),
      adminModeLabel: document.getElementById("adminModeLabel"),
      debugModeLabel: document.getElementById("debugModeLabel")
    };
  }

  function renderRuntimeMetadata(elements, config, shared) {
    const runtimeCsvPath = shared.getRuntimeCsvPath(config);

    elements.dataModeLabel.textContent = shared.labelMode(config.dataMode);
    elements.dataSourceLabel.textContent =
      config.dataMode === "apps_script" && config.appsScriptWebAppUrl
        ? config.appsScriptWebAppUrl
        : runtimeCsvPath;
    elements.adminModeLabel.textContent = shared.labelMode(config.adminMode);
    elements.debugModeLabel.textContent = config.debugUi ? "Enabled" : "Disabled";
  }

  function wireControls(elements, shared) {
    elements.btnSearch.addEventListener("click", () => performSearch(elements, shared));
    elements.searchInput.addEventListener("keypress", (event) => {
      if (event.key === "Enter") {
        performSearch(elements, shared);
      }
    });

    elements.btnReset.addEventListener("click", () => resetView(elements));
    elements.sliderArea.addEventListener("input", () => {
      updateEdgeLengths("center_to_area", Number(elements.sliderArea.value));
    });
    elements.sliderOrg.addEventListener("input", () => {
      updateEdgeLengths("area_to_org", Number(elements.sliderOrg.value));
    });
    elements.sliderName.addEventListener("input", () => {
      updateEdgeLengths("org_to_person", Number(elements.sliderName.value));
    });

    elements.csvFileInput.addEventListener("change", async (event) => {
      const [file] = event.target.files || [];

      if (!file) {
        return;
      }

      try {
        const rows = await parseCsvRows(file);

        if (!rows.length) {
          throw new Error("The selected file did not contain valid public rows.");
        }

        buildGraph(rows, elements);
        updateStats(rows, elements);
        shared.setStatus(
          elements.statusMessage,
          `Loaded ${rows.length} publish-safe rows from ${file.name}.`,
          "success"
        );
      } catch (error) {
        shared.setStatus(elements.statusMessage, error.message, "error");
      }
    });
  }

  async function loadConfiguredRows(config) {
    if (config.dataMode === "apps_script") {
      if (!config.appsScriptWebAppUrl) {
        throw new Error("Apps Script mode is selected but no web app URL is configured.");
      }

      return loadRowsFromAppsScript(config.appsScriptWebAppUrl);
    }

    return parseCsvRows(window.RICCEShared.getRuntimeCsvPath(config));
  }

  async function loadRowsFromAppsScript(url) {
    const separator = url.includes("?") ? "&" : "?";
    const response = await fetch(`${url}${separator}mode=records`, { method: "GET" });

    if (!response.ok) {
      throw new Error(`Apps Script data request failed with status ${response.status}.`);
    }

    const payload = await response.json();

    if (payload.ok === false) {
      throw new Error(payload.error || "Apps Script returned an error.");
    }

    const sourceRows = Array.isArray(payload.records) ? payload.records : payload;
    return sourceRows.map(normalizeRow).filter(Boolean);
  }

  async function parseCsvRows(source) {
    return new Promise((resolve, reject) => {
      Papa.parse(source, {
        download: typeof source === "string",
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const rows = results.data.map(normalizeRow).filter(Boolean);
          resolve(rows);
        },
        error: (error) => reject(new Error(`CSV parsing failed: ${error.message}`))
      });
    });
  }

  function normalizeRow(row) {
    const name = extractValue(row, ["Name", "name"]);
    const organization = extractValue(row, ["Organization", "organization"]);
    const serviceArea = extractValue(row, [
      "Service Area",
      "serviceArea",
      "service_area",
      "Service Area of the Non-Profit Organization"
    ]);

    if (!name || !organization) {
      return null;
    }

    return {
      Name: name,
      Organization: organization,
      "Service Area": serviceArea || "Other"
    };
  }

  function extractValue(row, keys) {
    for (const key of keys) {
      if (row && row[key] !== undefined && row[key] !== null) {
        const value = String(row[key]).replace(/\s+/g, " ").trim();
        if (value) {
          return value;
        }
      }
    }

    return "";
  }

  function buildGraph(rows, elements) {
    nodes.clear();
    edges.clear();
    clearSelection(elements);

    const centerId = "center_hub";
    const organizationIds = new Map();
    const areaIds = new Map();

    nodes.add({
      id: centerId,
      label: "RICCE\nOntology Hub",
      group: "center",
      shape: "star",
      size: 32
    });

    rows.forEach((row, index) => {
      const personId = `person:${index}`;
      const organizationKey = row.Organization.toLowerCase();

      nodes.add({
        id: personId,
        label: row.Name,
        group: "person",
        title: row.Name,
        details: {
          Name: row.Name,
          Organization: row.Organization,
          "Service Area": row["Service Area"]
        }
      });

      let orgId = organizationIds.get(organizationKey);

      if (!orgId) {
        orgId = `org:${organizationIds.size}`;
        organizationIds.set(organizationKey, orgId);
        nodes.add({
          id: orgId,
          label: row.Organization,
          group: "org"
        });
      }

      edges.add({
        id: `${orgId}->${personId}`,
        from: orgId,
        to: personId,
        type: "org_to_person",
        length: Number(elements.sliderName.value),
        color: { opacity: 0.62 }
      });

      splitServiceAreas(row["Service Area"]).forEach((area) => {
        const areaKey = area.toLowerCase();
        let areaId = areaIds.get(areaKey);

        if (!areaId) {
          areaId = `area:${areaIds.size}`;
          areaIds.set(areaKey, areaId);
          nodes.add({
            id: areaId,
            label: area,
            group: "area"
          });
          edges.add({
            id: `${centerId}->${areaId}`,
            from: centerId,
            to: areaId,
            type: "center_to_area",
            length: Number(elements.sliderArea.value),
            width: 2,
            color: { opacity: 0.84 }
          });
        }

        const areaToOrgEdgeId = `${areaId}->${orgId}`;
        if (!edges.get(areaToOrgEdgeId)) {
          edges.add({
            id: areaToOrgEdgeId,
            from: areaId,
            to: orgId,
            type: "area_to_org",
            length: Number(elements.sliderOrg.value),
            width: 1.5,
            color: { opacity: 0.72 }
          });
        }
      });
    });

    initNetwork(elements);
  }

  function splitServiceAreas(value) {
    const trimmed = String(value || "Other").trim();

    if (!trimmed) {
      return ["Other"];
    }

    const areas = trimmed
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) =>
        item.toLowerCase().includes("combination") ? "Multiple Services / Combination" : item
      );

    return [...new Set(areas)];
  }

  function initNetwork(elements) {
    const container = document.getElementById("mynetwork");
    const options = {
      nodes: {
        shape: "dot",
        borderWidth: 2,
        shadow: true,
        font: {
          size: 14,
          color: "#18343e",
          face: "Avenir Next"
        }
      },
      groups: {
        center: {
          color: { background: "#18343e", border: "#0f2730" },
          font: { size: 22, color: "#18343e", bold: true }
        },
        area: {
          color: { background: "#d38f2b", border: "#a96f17" },
          shape: "hexagon",
          size: 26,
          font: { size: 16, color: "#744900", bold: true }
        },
        org: {
          color: { background: "#8bc2d7", border: "#3e8aa6" },
          shape: "box",
          margin: 10,
          font: { size: 14 }
        },
        person: {
          color: { background: "#0f7a78", border: "#0a5755" },
          size: 10,
          font: { size: 12, color: "#0f7a78" }
        }
      },
      edges: {
        smooth: { type: "continuous" }
      },
      physics: {
        solver: "forceAtlas2Based",
        forceAtlas2Based: {
          gravitationalConstant: -110,
          centralGravity: 0.012,
          springConstant: 0.08,
          springLength: 100,
          damping: 0.42
        },
        stabilization: { iterations: 220 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 180,
        zoomView: true
      }
    };

    if (network) {
      network.destroy();
    }

    network = new vis.Network(container, { nodes, edges }, options);
    network.once("stabilized", () => {
      network.fit({ animation: { duration: 800, easingFunction: "easeInOutQuad" } });
    });

    network.on("click", (params) => {
      if (!params.nodes.length) {
        clearSelection(elements);
        return;
      }

      const selectedNode = nodes.get(params.nodes[0]);
      if (!selectedNode || selectedNode.group !== "person" || !selectedNode.details) {
        clearSelection(elements);
        return;
      }

      renderSelection(selectedNode, elements, window.RICCEShared);
    });
  }

  function renderSelection(node, elements, shared) {
    elements.selectionPlaceholder.classList.add("is-hidden");
    elements.panelTitle.textContent = "Profile details";
    elements.panelContent.innerHTML = Object.entries(node.details)
      .map(
        ([label, value]) =>
          `<div class="detail-item"><span class="detail-label">${shared.escapeHtml(
            label
          )}</span><span class="detail-value">${shared.escapeHtml(value)}</span></div>`
      )
      .join("");
  }

  function clearSelection(elements) {
    elements.panelTitle.textContent = "Profile details";
    elements.selectionPlaceholder.classList.remove("is-hidden");
    elements.panelContent.innerHTML = "";
  }

  function updateStats(rows, elements) {
    const organizations = new Set();
    const areas = new Set();

    rows.forEach((row) => {
      organizations.add(row.Organization.toLowerCase());
      splitServiceAreas(row["Service Area"]).forEach((area) => areas.add(area.toLowerCase()));
    });

    elements.profileCount.textContent = String(rows.length);
    elements.organizationCount.textContent = String(organizations.size);
    elements.serviceAreaCount.textContent = String(areas.size);
  }

  function performSearch(elements, shared) {
    if (!network) {
      return;
    }

    const term = elements.searchInput.value.toLowerCase().trim();
    if (!term) {
      shared.setStatus(elements.statusMessage, "Enter a profile name to search.", "warning");
      return;
    }

    const match = nodes
      .get()
      .find((node) => node.group === "person" && node.label.toLowerCase().includes(term));

    if (!match) {
      shared.setStatus(elements.statusMessage, "Profile not found in the sample dataset.", "warning");
      return;
    }

    network.focus(match.id, {
      scale: 1.45,
      animation: { duration: 750, easingFunction: "easeInOutQuad" }
    });
    network.selectNodes([match.id]);
    renderSelection(match, elements, shared);
    shared.setStatus(elements.statusMessage, `Focused on ${match.label}.`, "success");
  }

  function resetView(elements) {
    elements.searchInput.value = "";
    elements.sliderArea.value = String(DEFAULT_LENGTHS.centerToArea);
    elements.sliderOrg.value = String(DEFAULT_LENGTHS.areaToOrg);
    elements.sliderName.value = String(DEFAULT_LENGTHS.orgToPerson);
    clearSelection(elements);

    updateEdgeLengths("center_to_area", DEFAULT_LENGTHS.centerToArea);
    updateEdgeLengths("area_to_org", DEFAULT_LENGTHS.areaToOrg);
    updateEdgeLengths("org_to_person", DEFAULT_LENGTHS.orgToPerson);

    if (network) {
      network.unselectAll();
      network.fit({ animation: { duration: 700, easingFunction: "easeInOutQuad" } });
    }
  }

  function updateEdgeLengths(type, newLength) {
    const updates = edges
      .get()
      .filter((edge) => edge.type === type)
      .map((edge) => ({ id: edge.id, length: newLength }));

    if (!updates.length) {
      return;
    }

    edges.update(updates);
    if (network) {
      network.startSimulation();
    }
  }
})();
