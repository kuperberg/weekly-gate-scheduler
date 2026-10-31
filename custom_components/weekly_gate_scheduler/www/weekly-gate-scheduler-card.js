const DAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"];

class WeeklyGateSchedulerCard extends HTMLElement {
  setConfig(config) {
    if (!config.entry_id || !config.status_entity) throw new Error("נדרשים entry_id ו-status_entity");
    this.config = config;
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }

  set hass(value) { this._hass = value; this.render(); }
  getCardSize() { return 12; }

  async call(service, data = {}) {
    try {
      this._error = "";
      await this._hass.callService("weekly_gate_scheduler", service, { entry_id: this.config.entry_id, ...data });
    } catch (error) {
      this._error = error?.message || "הפעולה נכשלה";
      this.render();
    }
  }

  status() { return this._hass?.states[this.config.status_entity]; }
  events() { return this.status()?.attributes?.events || []; }

  row(item) {
    return `<div class="event" data-id="${item.id}">
      <label class="enabled"><input type="checkbox" ${item.enabled ? "checked" : ""}> פעיל</label>
      <label>פתיחה<input class="start" type="time" value="${item.start_time}"></label>
      <label>סיום<input class="end" type="time" value="${item.end_time}"></label>
      <label>הסיום<select class="next"><option value="false" ${!item.end_next_day ? "selected" : ""}>באותו יום</option><option value="true" ${item.end_next_day ? "selected" : ""}>למחרת</option></select></label>
      <button class="delete" title="מחיקת אירוע">🗑</button>
    </div>`;
  }

  render() {
    if (!this.shadowRoot || !this._hass || !this.config) return;
    const entity = this.status();
    const status = entity?.state || "fault";
    const attrs = entity?.attributes || {};
    const grouped = DAYS.map((_, i) => this.events().filter((e) => e.weekday === i));
    const color = status === "fault" ? "red" : status === "hold_open" || status === "working" ? "blue" : "green";
    this.shadowRoot.innerHTML = `<style>
      :host{display:block;--blue:#1976d2;--green:#2e8b57;--red:#c62828}*{box-sizing:border-box}.wrap{direction:rtl;font-family:var(--paper-font-body1_-_font-family,Arial);color:var(--primary-text-color);display:grid;gap:14px}.panel{background:var(--ha-card-background,var(--card-background-color,#fff));border-radius:16px;padding:16px;box-shadow:var(--ha-card-box-shadow,0 2px 8px #0002)}.status{border-right:7px solid var(--${color});display:flex;justify-content:space-between;gap:12px;align-items:center}.status strong{font-size:21px}.muted{color:var(--secondary-text-color);font-size:13px}.actions{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.action{border:0;border-radius:13px;min-height:62px;padding:10px;color:#fff;font-weight:800;font-size:15px;cursor:pointer}.night{background:#4c55a5}.daytime{background:#1976d2}.normal{background:#2e8b57}.days{display:grid;gap:9px}.day{border:1px solid var(--divider-color,#ddd);border-radius:13px;overflow:hidden}.head{display:flex;justify-content:space-between;align-items:center;padding:11px 13px;background:color-mix(in srgb,var(--primary-background-color,#eee) 70%,transparent);font-weight:800}.add{border:1px solid var(--primary-color,#1976d2);background:transparent;color:var(--primary-color,#1976d2);border-radius:9px;padding:7px 10px;font-weight:700}.empty{padding:12px;color:var(--secondary-text-color)}.event{display:grid;grid-template-columns:85px 1fr 1fr 1.2fr 46px;gap:9px;align-items:end;padding:11px;border-top:1px solid var(--divider-color,#ddd)}label{font-size:12px;color:var(--secondary-text-color)}input[type=time],select{width:100%;display:block;margin-top:4px;border:1px solid var(--divider-color,#ccc);border-radius:9px;background:var(--card-background-color,#fff);color:var(--primary-text-color);padding:9px;font-size:15px}.enabled{align-self:center;font-weight:700;color:var(--primary-text-color)}.delete{height:40px;border:0;border-radius:9px;background:#ffebee}.error{color:var(--red)}@media(max-width:700px){.actions{grid-template-columns:1fr}.event{grid-template-columns:1fr 1fr}.delete{grid-column:span 2}.status{align-items:flex-start;flex-direction:column}}
    </style><ha-card><div class="wrap" dir="rtl">
      <div class="panel status"><div><strong>${status === "hold_open" ? "השער פתוח" : status === "fault" ? "תקלה בשער" : status === "working" ? "מבצע פעולה" : "מצב אפליקציה"}</strong><div class="muted">${attrs.active_until ? `סיום: ${new Date(attrs.active_until).toLocaleString("he-IL")}` : "אין פתיחה פעילה"}</div>${this._error ? `<div class="error">${this._error}</div>` : ""}</div><div class="muted">Palgate: ${attrs.observed_mode || "לא זמין"}<br>בדיקה: ${attrs.last_check ? new Date(attrs.last_check).toLocaleTimeString("he-IL") : "—"}</div></div>
      <div class="panel"><div class="actions"><button class="action night" data-service="open_now_until_0400">🌙 פתיחה עכשיו — עד מחר 04:00</button><button class="action daytime" data-service="open_now_until_1700">פתיחה עכשיו — עד 17:00</button><button class="action normal" data-service="finish_active">סיום פתיחה — חזרה למצב אפליקציה</button></div></div>
      <div class="panel"><h2>לוח שבועי לשער</h2><div class="muted">השבוע הנוכחי בלבד</div><div class="days">${DAYS.map((day,i)=>`<section class="day"><div class="head"><span>יום ${day}</span><button class="add" data-day="${i}">＋ הוספת אירוע</button></div>${grouped[i].length ? grouped[i].map(e=>this.row(e)).join("") : '<div class="empty">לא הוגדרו אירועים</div>'}</section>`).join("")}</div></div>
    </div></ha-card>`;
    this.shadowRoot.querySelectorAll("[data-service]").forEach((b)=>b.onclick=()=>this.call(b.dataset.service));
    this.shadowRoot.querySelectorAll(".add").forEach((b)=>b.onclick=()=>this.call("upsert_event",{weekday:Number(b.dataset.day),start_time:"17:00",end_time:"18:00",end_next_day:false,enabled:false}));
    this.shadowRoot.querySelectorAll(".event").forEach((row)=>{
      const id=row.dataset.id, item=this.events().find(e=>e.id===id);
      row.querySelector(".delete").onclick=()=>this.call("delete_event",{event_id:id});
      row.querySelector(".enabled input").onchange=(e)=>this.call("set_event_enabled",{event_id:id,enabled:e.target.checked});
      const save=()=>this.call("upsert_event",{event_id:id,weekday:item.weekday,start_time:row.querySelector(".start").value,end_time:row.querySelector(".end").value,end_next_day:row.querySelector(".next").value==="true",enabled:row.querySelector(".enabled input").checked});
      row.querySelectorAll(".start,.end,.next").forEach((el)=>el.onchange=save);
    });
  }
}

if (!customElements.get("weekly-gate-scheduler-card")) customElements.define("weekly-gate-scheduler-card", WeeklyGateSchedulerCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "weekly-gate-scheduler-card", name: "לוח שבועי לשער", description: "ניהול שבועי מקומי לשער " });
