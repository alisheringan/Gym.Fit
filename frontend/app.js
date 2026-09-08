/* ============================================================
   GymFit — frontend логика (без сборки, без npm)
   ============================================================ */

const API_BASE = "http://localhost:8000";

// ---------------------- Утилиты ----------------------

function $(sel) { return document.querySelector(sel); }
function $all(sel) { return document.querySelectorAll(sel); }

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const body = isJson ? await res.json().catch(() => null) : null;
  if (!res.ok) {
    const detail = body?.detail || `Ошибка сервера (${res.status})`;
    throw new Error(detail);
  }
  return body;
}

function showToast(text, isError = false) {
  const toast = $("#toast");
  toast.textContent = text;
  toast.classList.toggle("is-error", isError);
  toast.classList.add("is-visible");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.remove("is-visible"), 3500);
}

function setMsg(el, text, isError = false) {
  el.textContent = text;
  el.classList.toggle("is-success", !isError && !!text);
  el.classList.toggle("is-error", isError);
}

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function daysAgoISO(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

// ---------------------- Навигация по вкладкам ----------------------

$all(".nav-item").forEach((btn) => {
  btn.addEventListener("click", () => {
    $all(".nav-item").forEach((b) => b.classList.remove("is-active"));
    $all(".panel").forEach((p) => p.classList.remove("is-active"));
    btn.classList.add("is-active");
    $(`#panel-${btn.dataset.tab}`).classList.add("is-active");

    if (btn.dataset.tab === "clients") loadClients();
    if (btn.dataset.tab === "zones") loadZones();
    if (btn.dataset.tab === "analytics") loadAnalytics();
    if (btn.dataset.tab === "calendar") loadCalendar();
  });
});

// ---------------------- Часы в сайдбаре ----------------------

function tickClock() {
  const now = new Date();
  $("#clockOut").textContent = now.toLocaleTimeString("ru-RU");
  $("#dateOut").textContent = now.toLocaleDateString("ru-RU", { day: "2-digit", month: "long", year: "numeric" });
}
setInterval(tickClock, 1000);
tickClock();

// ---------------------- Регистрация визита ----------------------

let clientsCache = [];
let zonesCache = [];

async function loadCheckinOptions() {
  const [clients, zones] = await Promise.all([api("/clients/"), api("/zones/")]);
  clientsCache = clients;
  zonesCache = zones;

  const clientSel = $("#checkinClient");
  clientSel.innerHTML = clients
    .map((c) => `<option value="${c.id}">${c.full_name}</option>`)
    .join("") || `<option value="">Нет клиентов</option>`;

  const zoneSel = $("#checkinZone");
  zoneSel.innerHTML = zones
    .map((z) => `<option value="${z.id}">${z.name}</option>`)
    .join("") || `<option value="">Нет зон</option>`;
}

async function loadRecentVisits() {
  const visits = await api("/visits/?limit=15");
  const tbody = $("#visitsTable tbody");
  const empty = $("#visitsEmpty");

  if (!visits.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    return;
  }
  empty.style.display = "none";
  tbody.innerHTML = visits
    .map(
      (v) => `
      <tr>
        <td class="mono">${formatTime(v.visit_time)}</td>
        <td>${v.client_name}</td>
        <td>${v.zone_name}</td>
      </tr>`
    )
    .join("");
}

async function loadTodayCount() {
  const today = todayISO();
  const zones = await api(`/analytics/zones?date_from=${today}&date_to=${today}`);
  const total = zones.reduce((sum, z) => sum + z.visits_count, 0);
  $("#todayCount").textContent = total;
}

$("#checkinSubmit").addEventListener("click", async () => {
  const clientId = $("#checkinClient").value;
  const zoneId = $("#checkinZone").value;
  const msgEl = $("#checkinMsg");

  if (!clientId || !zoneId) {
    setMsg(msgEl, "Сначала добавьте клиентов и зоны.", true);
    return;
  }

  try {
    const visit = await api("/visits/", {
      method: "POST",
      body: JSON.stringify({ client_id: Number(clientId), zone_id: Number(zoneId) }),
    });
    setMsg(msgEl, `Визит зарегистрирован: ${visit.client_name} → ${visit.zone_name}`);
    showToast("Вход отмечен");
    loadRecentVisits();
    loadTodayCount();
  } catch (e) {
    setMsg(msgEl, e.message, true);
  }
});

// ---------------------- Клиенты ----------------------

async function loadClients() {
  const clients = await api("/clients/");
  const tbody = $("#clientsTable tbody");

  if (!clients.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-row">Пока нет клиентов</td></tr>`;
    return;
  }

  // Подгружаем статус абонемента для каждого клиента
  const rows = await Promise.all(
    clients.map(async (c) => {
      let badge = `<span class="badge badge--expired">нет абонемента</span>`;
      try {
        const subs = await api(`/subscriptions/client/${c.id}`);
        const active = subs.find((s) => new Date(s.end_date) >= new Date(todayISO()));
        if (active) {
          badge = `<span class="badge badge--active">до ${active.end_date}</span>`;
        } else if (subs.length) {
          badge = `<span class="badge badge--expired">истёк ${subs[0].end_date}</span>`;
        }
      } catch (_) { /* пропускаем, если не удалось получить */ }

      return `
        <tr>
          <td>${c.full_name}</td>
          <td class="mono">${c.phone || "—"}</td>
          <td class="mono">${c.email || "—"}</td>
          <td>${badge}</td>
          <td><button class="btn btn--ghost btn--small" data-sub-client="${c.id}" data-sub-name="${c.full_name}">+ Абонемент</button></td>
        </tr>`;
    })
  );

  tbody.innerHTML = rows.join("");

  $all("[data-sub-client]").forEach((btn) => {
    btn.addEventListener("click", () => addSubscriptionPrompt(btn.dataset.subClient, btn.dataset.subName));
  });
}

async function addSubscriptionPrompt(clientId, clientName) {
  const days = prompt(`Абонемент для «${clientName}» — на сколько дней от сегодня?`, "30");
  if (!days) return;
  const n = parseInt(days, 10);
  if (!n || n <= 0) {
    showToast("Введите положительное число дней", true);
    return;
  }
  try {
    await api("/subscriptions/", {
      method: "POST",
      body: JSON.stringify({
        client_id: Number(clientId),
        start_date: todayISO(),
        end_date: daysAgoISO(-n),
      }),
    });
    showToast(`Абонемент выдан: ${clientName}`);
    loadClients();
  } catch (e) {
    showToast(e.message, true);
  }
}

$("#addClientSubmit").addEventListener("click", async () => {
  const name = $("#newClientName").value.trim();
  const phone = $("#newClientPhone").value.trim();
  const email = $("#newClientEmail").value.trim();
  const msgEl = $("#addClientMsg");

  if (!name) {
    setMsg(msgEl, "Укажите ФИО клиента.", true);
    return;
  }

  try {
    await api("/clients/", {
      method: "POST",
      body: JSON.stringify({ full_name: name, phone, email }),
    });
    setMsg(msgEl, "Клиент добавлен.");
    $("#newClientName").value = "";
    $("#newClientPhone").value = "";
    $("#newClientEmail").value = "";
    loadClients();
    loadCheckinOptions();
  } catch (e) {
    setMsg(msgEl, e.message, true);
  }
});

// ---------------------- Зоны ----------------------

async function loadZones() {
  const zones = await api("/zones/");
  const grid = $("#zoneGrid");

  if (!zones.length) {
    grid.innerHTML = `<p class="empty-row">Пока нет зон — добавьте первую выше.</p>`;
    return;
  }

  grid.innerHTML = zones
    .map(
      (z) => `
      <div class="zone-card">
        <div class="zone-card-name">${z.name}</div>
        <div class="zone-card-desc">${z.description || "Без описания"}</div>
      </div>`
    )
    .join("");
}

$("#addZoneSubmit").addEventListener("click", async () => {
  const name = $("#newZoneName").value.trim();
  const desc = $("#newZoneDesc").value.trim();
  const msgEl = $("#addZoneMsg");

  if (!name) {
    setMsg(msgEl, "Укажите название зоны.", true);
    return;
  }

  try {
    await api("/zones/", {
      method: "POST",
      body: JSON.stringify({ name, description: desc || null }),
    });
    setMsg(msgEl, "Зона добавлена.");
    $("#newZoneName").value = "";
    $("#newZoneDesc").value = "";
    loadZones();
    loadCheckinOptions();
  } catch (e) {
    setMsg(msgEl, e.message, true);
  }
});

// ---------------------- Аналитика ----------------------

function renderBars(containerSel, items, labelKey, countKey) {
  const container = $(containerSel);
  if (!items.length) {
    container.innerHTML = `<p class="empty-row">Нет данных за этот период.</p>`;
    return;
  }
  const max = Math.max(...items.map((i) => i[countKey]), 1);
  container.innerHTML = items
    .map(
      (i) => `
      <div class="bar-row">
        <div class="bar-row-label">${i[labelKey]}</div>
        <div class="bar-track"><div class="bar-fill" style="width:${(i[countKey] / max) * 100}%"></div></div>
        <div class="bar-row-value">${i[countKey]}</div>
      </div>`
    )
    .join("");
}

async function loadAnalytics() {
  if (!$("#analyticsFrom").value) $("#analyticsFrom").value = daysAgoISO(30);
  if (!$("#analyticsTo").value) $("#analyticsTo").value = todayISO();

  const from = $("#analyticsFrom").value;
  const to = $("#analyticsTo").value;

  const [zones, weekdays, top] = await Promise.all([
    api(`/analytics/zones?date_from=${from}&date_to=${to}`),
    api(`/analytics/weekdays?date_from=${from}&date_to=${to}`),
    api(`/analytics/top-clients?limit=5`),
  ]);

  renderBars("#zoneBars", zones, "zone_name", "visits_count");
  renderBars("#weekdayBars", weekdays, "weekday_name", "visits_count");

  const topEl = $("#topClients");
  topEl.innerHTML = top.length
    ? top
        .map(
          (c, idx) => `
        <div class="rank-row">
          <div class="rank-num">${idx + 1}</div>
          <div class="rank-name">${c.client_name}</div>
          <div class="rank-count">${c.visits_count} визитов</div>
        </div>`
        )
        .join("")
    : `<p class="empty-row">Нет визитов в этом месяце.</p>`;
}

$("#analyticsRefresh").addEventListener("click", loadAnalytics);

// ---------------------- Календарь ----------------------

const MONTH_NAMES = [
  "январь", "февраль", "март", "апрель", "май", "июнь",
  "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
];

let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth(); // 0-11
let calVisitsByDay = {};   // "YYYY-MM-DD" -> [visit, ...]
let calSelectedDay = null; // "YYYY-MM-DD"

function pad2(n) { return String(n).padStart(2, "0"); }
function dateKey(y, m, d) { return `${y}-${pad2(m + 1)}-${pad2(d)}`; }

async function loadCalendar() {
  const firstDay = new Date(calYear, calMonth, 1);
  const lastDay = new Date(calYear, calMonth + 1, 0);
  const dateFrom = dateKey(calYear, calMonth, 1);
  const dateTo = dateKey(calYear, calMonth, lastDay.getDate());

  $("#calMonthLabel").textContent = `${MONTH_NAMES[calMonth]} ${calYear}`;

  const visits = await api(`/visits/?date_from=${dateFrom}&date_to=${dateTo}&limit=2000`);

  calVisitsByDay = {};
  visits.forEach((v) => {
    const key = v.visit_time.slice(0, 10);
    (calVisitsByDay[key] ||= []).push(v);
  });

  renderCalendarGrid(firstDay, lastDay);

  // Если выбранный день не из этого месяца (или ещё не выбран) — выбираем сегодня
  // или первый день месяца, если сегодня в другом месяце.
  const todayKey = todayISO();
  if (calSelectedDay && calSelectedDay.slice(0, 7) === dateFrom.slice(0, 7)) {
    selectCalendarDay(calSelectedDay);
  } else if (todayKey.slice(0, 7) === dateFrom.slice(0, 7)) {
    selectCalendarDay(todayKey);
  } else {
    selectCalendarDay(dateFrom);
  }
}

function renderCalendarGrid(firstDay, lastDay) {
  const grid = $("#calGrid");
  const todayKey = todayISO();

  // ISO: понедельник = 1 ... воскресенье = 7. Считаем, сколько пустых ячеек
  // нужно перед 1-м числом, чтобы сетка начиналась с понедельника.
  const isoWeekday = (firstDay.getDay() + 6) % 7; // 0=Пн ... 6=Вс
  const cells = [];

  for (let i = 0; i < isoWeekday; i++) {
    cells.push(`<div class="cal-cell is-empty"></div>`);
  }

  for (let d = 1; d <= lastDay.getDate(); d++) {
    const key = dateKey(calYear, calMonth, d);
    const count = (calVisitsByDay[key] || []).length;
    const isToday = key === todayKey;
    cells.push(`
      <div class="cal-cell${isToday ? " is-today" : ""}" data-day="${key}">
        <div class="cal-cell-day">${d}</div>
        <div class="cal-cell-count${count === 0 ? " is-zero" : ""}">${count || "—"}</div>
      </div>`);
  }

  grid.innerHTML = cells.join("");
  $all(".cal-cell[data-day]").forEach((cell) => {
    cell.addEventListener("click", () => selectCalendarDay(cell.dataset.day));
  });
}

function selectCalendarDay(key) {
  calSelectedDay = key;
  $all(".cal-cell[data-day]").forEach((cell) => {
    cell.classList.toggle("is-selected", cell.dataset.day === key);
  });

  const [y, m, d] = key.split("-");
  $("#calDayTitle").textContent = `Визиты — ${d}.${m}.${y}`;

  const visits = (calVisitsByDay[key] || []).slice().sort((a, b) => a.visit_time.localeCompare(b.visit_time));
  const tbody = $("#calDayTable tbody");
  const empty = $("#calDayEmpty");

  if (!visits.length) {
    tbody.innerHTML = "";
    empty.style.display = "block";
    empty.textContent = "В этот день визитов не было.";
    return;
  }
  empty.style.display = "none";
  tbody.innerHTML = visits
    .map(
      (v) => `
      <tr>
        <td class="mono">${formatTime(v.visit_time).split(", ")[1] || formatTime(v.visit_time)}</td>
        <td>${v.client_name}</td>
        <td>${v.zone_name}</td>
      </tr>`
    )
    .join("");
}

$("#calPrev").addEventListener("click", () => {
  calMonth -= 1;
  if (calMonth < 0) { calMonth = 11; calYear -= 1; }
  loadCalendar();
});
$("#calNext").addEventListener("click", () => {
  calMonth += 1;
  if (calMonth > 11) { calMonth = 0; calYear += 1; }
  loadCalendar();
});
$("#calToday").addEventListener("click", () => {
  calYear = new Date().getFullYear();
  calMonth = new Date().getMonth();
  calSelectedDay = todayISO();
  loadCalendar();
});

// ---------------------- Старт ----------------------

(async function init() {
  try {
    await loadCheckinOptions();
    await loadRecentVisits();
    await loadTodayCount();
  } catch (e) {
    showToast(`Не удалось подключиться к API: ${e.message}`, true);
  }
})();
