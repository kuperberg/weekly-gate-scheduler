import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const path = new URL("../../custom_components/weekly_gate_scheduler/www/weekly-gate-scheduler-card.js", import.meta.url);

test("card contains approved RTL controls and seven empty-capable days", () => {
  const source = readFileSync(path, "utf8");
  assert.match(source, /dir="rtl"/);
  assert.match(source, /פתיחה עכשיו עד מחר 04:00/);
  assert.match(source, /פתיחה עכשיו עד 17:00/);
  assert.match(source, /סיום פתיחה חזרה למצב אפליקציה/);
  assert.doesNotMatch(source, /22:00/);
  for (const day of ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]) assert.match(source, new RegExp(day));
  assert.match(source, /לא הוגדרו אירועים/);
  assert.match(source, /end_next_day/);
  assert.match(source, /weekly-gate-scheduler-card/);
  assert.match(source, /start_time:"17:00",end_time:"18:00",end_next_day:false,enabled:false/);
  assert.match(source, /if \(!customElements\.get\("weekly-gate-scheduler-card"\)\)/);
});

test("time inputs keep hour-minute order inside the RTL card", () => {
  const source = readFileSync(path, "utf8");
  assert.match(source, /input\[type=time\][^{]*\{[^}]*direction:ltr/);
});

test("event times are submitted together only from an explicit save button", () => {
  const source = readFileSync(path, "utf8");
  assert.match(source, /title="שמירת האירוע"/);
  assert.match(source, /"נשמר ✓" : "שמירה"/);
  assert.match(source, /querySelector\("\.save"\)\.onclick=save/);
  assert.doesNotMatch(source, /querySelectorAll\("\.start,\.end,\.next"\).*onchange=save/);
});

test("quick actions have no dash and a successful event save is confirmed", () => {
  const source = readFileSync(path, "utf8");
  assert.match(source, /פתיחה עכשיו עד מחר 04:00/);
  assert.match(source, /פתיחה עכשיו עד 17:00/);
  assert.match(source, /סיום פתיחה חזרה למצב אפליקציה/);
  assert.doesNotMatch(source, /פתיחה עכשיו [—-] עד/);
  assert.match(source, /נשמר ✓/);
  assert.match(source, /if\s*\(ok\)/);
});

test("status timing and details use an enlarged status-only style", () => {
  const source = readFileSync(path, "utf8");
  assert.match(source, /\.status \.muted\{[^}]*font-size:16px/);
});
