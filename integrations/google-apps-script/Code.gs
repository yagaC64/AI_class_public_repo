const CONFIG = Object.freeze({
  recordsSheetName: "Records",
  publicFields: ["Name", "Organization", "Service Area"]
});

function doGet(e) {
  const mode = (e && e.parameter && e.parameter.mode) || "records";

  if (mode === "health") {
    return jsonOutput_({
      ok: true,
      service: "ricce-ontology-api",
      timestamp: new Date().toISOString()
    });
  }

  try {
    const records = getPublishedRecords_();
    return jsonOutput_({
      ok: true,
      count: records.length,
      records: records,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return jsonOutput_({
      ok: false,
      error: String(error && error.message ? error.message : error)
    });
  }
}

function getPublishedRecords_() {
  const sheetId = getScriptProperty_("RICCE_SHEET_ID");
  const sheet = SpreadsheetApp.openById(sheetId).getSheetByName(CONFIG.recordsSheetName);

  if (!sheet) {
    throw new Error(`Missing sheet tab: ${CONFIG.recordsSheetName}`);
  }

  const values = sheet.getDataRange().getDisplayValues();
  if (values.length < 2) {
    return [];
  }

  const headers = values[0];
  const records = values
    .slice(1)
    .map((row) => rowToObject_(headers, row))
    .map(normalizeRecord_)
    .filter(Boolean);

  return dedupeRecords_(records);
}

function normalizeRecord_(row) {
  const name = clean_(row.Name || row.name);
  const organization = clean_(row.Organization || row.organization);
  const serviceArea = clean_(
    row["Service Area"] ||
      row.serviceArea ||
      row.service_area ||
      row["Service Area of the Non-Profit Organization"]
  );

  if (!name || !organization) {
    return null;
  }

  return {
    Name: name,
    Organization: organization,
    "Service Area": serviceArea || "Other"
  };
}

function dedupeRecords_(records) {
  const seen = new Set();
  return records.filter((record) => {
    const key = [record.Name, record.Organization, record["Service Area"]]
      .map((value) => String(value).toLowerCase())
      .join("||");
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function rowToObject_(headers, row) {
  const output = {};
  headers.forEach((header, index) => {
    output[header] = row[index];
  });
  return output;
}

function clean_(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

function getScriptProperty_(key) {
  const value = PropertiesService.getScriptProperties().getProperty(key);
  if (!value) {
    throw new Error(`Missing script property: ${key}`);
  }
  return value;
}

function jsonOutput_(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload)).setMimeType(
    ContentService.MimeType.JSON
  );
}
