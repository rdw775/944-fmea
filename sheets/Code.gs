// 944 FMEA — Google Sheets backend
// Deploy as a Web App (Execute as: Me, Who has access: Anyone). See SETUP.md.
//
// Schema-agnostic: each tab's header row IS the schema. doPost appends a record by
// mapping its keys onto that header row; doGet returns a tab as JSON objects keyed by
// header. Adding a new data type later = add a tab + headers, no script change.

const TABS = {
  ScoreChanges: ["ts", "rowIndex", "failureMode", "fromS", "fromO", "fromD", "toS", "toO", "toD", "reason", "who"],
  Sessions:     ["ts", "sessionDate", "sessionNote", "sys", "characteristic", "status", "itemNote", "who"],
  Comments:     ["ts", "name", "text"],
  BuildTasks:   ["ts", "taskId", "title", "source", "status", "notes", "who"],
};

// Run this ONCE from the Apps Script editor after pasting. Creates every tab with its
// header row if missing; safe to re-run (it never clears data).
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  Object.keys(TABS).forEach(name => {
    let sh = ss.getSheetByName(name);
    if (!sh) sh = ss.insertSheet(name);
    const headers = TABS[name];
    const existing = sh.getRange(1, 1, 1, headers.length).getValues()[0];
    if (existing.join("") === "") {
      sh.getRange(1, 1, 1, headers.length).setValues([headers]);
      sh.setFrozenRows(1);
      sh.getRange(1, 1, 1, headers.length).setFontWeight("bold");
    }
  });
  const blank = ss.getSheetByName("Sheet1");
  if (blank && ss.getSheets().length > 1 && blank.getLastRow() === 0) ss.deleteSheet(blank);
}

function doGet(e) {
  const name = String((e && e.parameter && e.parameter.sheet) || "").trim();
  if (!name) return json({ error: "sheet param required", tabs: Object.keys(TABS) });
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sh) return json({ error: "no such sheet: " + name });
  const values = sh.getDataRange().getValues();
  if (values.length < 2) return json({ rows: [] });
  const headers = values[0];
  const rows = values.slice(1)
    .filter(r => r.some(v => v !== "" && v !== null))
    .map(r => {
      const o = {};
      headers.forEach((h, i) => { o[h] = r[i]; });
      return o;
    });
  return json({ rows });
}

function doPost(e) {
  let body;
  try { body = JSON.parse(e.postData.contents); }
  catch (err) { return json({ error: "invalid JSON" }); }
  const name = String(body.sheet || "").trim();
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sh) return json({ error: "no such sheet: " + name });
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  const records = Array.isArray(body.rows) ? body.rows : (body.row ? [body.row] : []);
  if (!records.length) return json({ error: "no row(s) given" });
  // One batched write instead of N appendRow calls — a whole checklist run lands atomically.
  const values = records.map(rec => headers.map(h => rec[h] === undefined || rec[h] === null ? "" : rec[h]));
  sh.getRange(sh.getLastRow() + 1, 1, values.length, headers.length).setValues(values);
  return json({ ok: true, appended: values.length });
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
