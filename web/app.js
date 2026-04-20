// Admin Web UI — 登录解密 + 4 个 section 的 CRUD
// 依赖:window.LIVE_INFO_CONFIG(由 scripts/build_web_config.py 生成)
//       @supabase/supabase-js v2(esm.sh CDN)

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.0";

// ---------- state ----------
let supabase = null;
const state = {
  artists: [],   // [{id, canonical_name, created_at}]
  users: [],     // [{id, name, email, feishu_webhook, notify_on_status_change, ...}]
};

// ---------- utils ----------
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function b64decode(s) {
  const bin = atob(s);
  const buf = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
  return buf;
}

function toast(msg, isError = false) {
  const el = $("#toast");
  el.textContent = msg;
  el.classList.toggle("error", isError);
  el.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.hidden = true; }, 2800);
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function confirmOr(msg) {
  return window.confirm(msg);
}

// ---------- login / decrypt ----------
async function decryptServiceKey(password, cfg) {
  const enc = new TextEncoder();
  const material = await crypto.subtle.importKey(
    "raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]
  );
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt: b64decode(cfg.salt), iterations: cfg.iterations, hash: "SHA-256" },
    material,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"]
  );
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: b64decode(cfg.iv) },
    key,
    b64decode(cfg.ciphertext)
  );
  return new TextDecoder().decode(plaintext);
}

async function onLogin(e) {
  e.preventDefault();
  const cfg = window.LIVE_INFO_CONFIG;
  if (!cfg) {
    $("#login-error").textContent = "config.js 未加载或构建失败(缺少 GitHub Secrets?)";
    $("#login-error").hidden = false;
    return;
  }
  const password = $("#admin-key").value;
  const errEl = $("#login-error");
  errEl.hidden = true;
  try {
    const serviceKey = await decryptServiceKey(password, cfg);
    supabase = createClient(cfg.supabaseUrl, serviceKey, {
      auth: { persistSession: false, autoRefreshToken: false },
    });
    $("#login").hidden = true;
    $("#app").hidden = false;
    await Promise.all([loadArtists(), loadUsers()]);
    await Promise.all([renderArtists(), renderUsers(), renderSubscriptions(), renderConcerts()]);
    populateConcertArtistFilter();
    populateSubscriptionSelects();
  } catch (err) {
    console.error(err);
    errEl.textContent = "密钥错误,请重试";
    errEl.hidden = false;
  }
}

// ---------- tabs ----------
function setupTabs() {
  $$(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.tab;
      $$(".tab").forEach(b => b.classList.toggle("active", b === btn));
      $$(".tab-panel").forEach(p => {
        const active = p.id === `tab-${name}`;
        p.classList.toggle("active", active);
        p.hidden = !active;
      });
      if (name === "subscriptions") renderSubscriptions();
      if (name === "concerts") renderConcerts();
    });
  });
}

// ---------- artists ----------
async function loadArtists() {
  const { data, error } = await supabase
    .from("artists")
    .select("id, canonical_name, created_at")
    .order("canonical_name");
  if (error) throw error;
  state.artists = data || [];
}

async function renderArtists() {
  const tbody = $("#artists-table tbody");
  tbody.innerHTML = "";
  if (!state.artists.length) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty">暂无艺人,先添加一个</td></tr>`;
    return;
  }
  for (const a of state.artists) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(a.canonical_name)}</td>
      <td>${fmtDate(a.created_at)}</td>
      <td class="actions"><button class="danger" data-id="${a.id}">删除</button></td>
    `;
    tr.querySelector("button").addEventListener("click", () => deleteArtist(a));
    tbody.appendChild(tr);
  }
}

async function addArtist(e) {
  e.preventDefault();
  const name = $("#artist-name").value.trim();
  if (!name) return;
  const { error } = await supabase
    .from("artists")
    .upsert({ canonical_name: name }, { onConflict: "canonical_name", ignoreDuplicates: true });
  if (error) { toast(error.message, true); return; }
  $("#artist-name").value = "";
  await loadArtists();
  await renderArtists();
  populateConcertArtistFilter();
  populateSubscriptionSelects();
  toast(`已添加:${name}`);
}

async function deleteArtist(a) {
  if (!confirmOr(`删除艺人「${a.canonical_name}」?相关订阅和演唱会会级联删除。`)) return;
  const { error } = await supabase.from("artists").delete().eq("id", a.id);
  if (error) { toast(error.message, true); return; }
  await loadArtists();
  await renderArtists();
  populateConcertArtistFilter();
  populateSubscriptionSelects();
  toast("已删除");
}

// ---------- users ----------
async function loadUsers() {
  const { data, error } = await supabase
    .from("users")
    .select("id, name, email, feishu_webhook, notify_on_status_change, created_at")
    .order("name");
  if (error) throw error;
  state.users = data || [];
}

async function renderUsers() {
  const tbody = $("#users-table tbody");
  tbody.innerHTML = "";
  if (!state.users.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty">暂无用户</td></tr>`;
    return;
  }
  for (const u of state.users) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(u.name)}</td>
      <td>${escapeHtml(u.email || "")}</td>
      <td>${u.feishu_webhook ? "✓" : ""}</td>
      <td>${u.notify_on_status_change ? "✓" : ""}</td>
      <td class="actions">
        <button class="ghost" data-act="edit">编辑</button>
        <button class="danger" data-act="del">删除</button>
      </td>
    `;
    tr.querySelector('[data-act="edit"]').addEventListener("click", () => startEditUser(u));
    tr.querySelector('[data-act="del"]').addEventListener("click", () => deleteUser(u));
    tbody.appendChild(tr);
  }
}

function startEditUser(u) {
  $("#user-id").value = u.id;
  $("#user-name").value = u.name || "";
  $("#user-email").value = u.email || "";
  $("#user-feishu").value = u.feishu_webhook || "";
  $("#user-notify").checked = !!u.notify_on_status_change;
  $("#user-submit").textContent = "保存";
  $("#user-cancel").hidden = false;
  $("#user-name").focus();
}

function resetUserForm() {
  $("#user-id").value = "";
  $("#user-form").reset();
  $("#user-notify").checked = true;
  $("#user-submit").textContent = "添加";
  $("#user-cancel").hidden = true;
}

async function submitUser(e) {
  e.preventDefault();
  const id = $("#user-id").value;
  const payload = {
    name: $("#user-name").value.trim(),
    email: $("#user-email").value.trim() || null,
    feishu_webhook: $("#user-feishu").value.trim() || null,
    notify_on_status_change: $("#user-notify").checked,
  };
  if (!payload.name) { toast("昵称必填", true); return; }
  if (!payload.email && !payload.feishu_webhook) {
    toast("至少填一个通知渠道(邮箱或飞书 webhook)", true);
    return;
  }
  let error;
  if (id) {
    ({ error } = await supabase.from("users").update(payload).eq("id", id));
  } else {
    ({ error } = await supabase.from("users").insert(payload));
  }
  if (error) { toast(error.message, true); return; }
  resetUserForm();
  await loadUsers();
  await renderUsers();
  populateSubscriptionSelects();
  toast(id ? "已更新" : "已添加");
}

async function deleteUser(u) {
  if (!confirmOr(`删除用户「${u.name}」?其所有订阅会级联删除。`)) return;
  const { error } = await supabase.from("users").delete().eq("id", u.id);
  if (error) { toast(error.message, true); return; }
  await loadUsers();
  await renderUsers();
  populateSubscriptionSelects();
  toast("已删除");
}

// ---------- subscriptions ----------
function populateSubscriptionSelects() {
  const uSel = $("#sub-user");
  const aSel = $("#sub-artist");
  uSel.innerHTML = `<option value="">选择用户</option>` +
    state.users.map(u => `<option value="${u.id}">${escapeHtml(u.name)}</option>`).join("");
  aSel.innerHTML = `<option value="">选择艺人</option>` +
    state.artists.map(a => `<option value="${a.id}">${escapeHtml(a.canonical_name)}</option>`).join("");
}

async function renderSubscriptions() {
  const tbody = $("#subscriptions-table tbody");
  tbody.innerHTML = "";
  const { data, error } = await supabase
    .from("subscriptions")
    .select("user_id, artist_id, created_at, users(name), artists(canonical_name)")
    .order("created_at", { ascending: false });
  if (error) { toast(error.message, true); return; }
  if (!data || !data.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty">暂无订阅关系</td></tr>`;
    return;
  }
  for (const r of data) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(r.users?.name || r.user_id)}</td>
      <td>${escapeHtml(r.artists?.canonical_name || r.artist_id)}</td>
      <td>${fmtDate(r.created_at)}</td>
      <td class="actions"><button class="danger">退订</button></td>
    `;
    tr.querySelector("button").addEventListener(
      "click", () => deleteSubscription(r.user_id, r.artist_id, r.users?.name, r.artists?.canonical_name)
    );
    tbody.appendChild(tr);
  }
}

async function addSubscription(e) {
  e.preventDefault();
  const userId = $("#sub-user").value;
  const artistId = $("#sub-artist").value;
  if (!userId || !artistId) { toast("请选择用户和艺人", true); return; }
  const { error } = await supabase
    .from("subscriptions")
    .upsert({ user_id: userId, artist_id: artistId }, { onConflict: "user_id,artist_id", ignoreDuplicates: true });
  if (error) { toast(error.message, true); return; }
  $("#sub-user").value = "";
  $("#sub-artist").value = "";
  await renderSubscriptions();
  toast("已订阅");
}

async function deleteSubscription(userId, artistId, userName, artistName) {
  if (!confirmOr(`退订「${userName}」对「${artistName}」的订阅?`)) return;
  const { error } = await supabase
    .from("subscriptions")
    .delete()
    .eq("user_id", userId)
    .eq("artist_id", artistId);
  if (error) { toast(error.message, true); return; }
  await renderSubscriptions();
  toast("已退订");
}

// ---------- concerts (read-only) ----------
function populateConcertArtistFilter() {
  const sel = $("#concert-artist-filter");
  const current = sel.value;
  sel.innerHTML = `<option value="">全部艺人</option>` +
    state.artists.map(a => `<option value="${a.id}">${escapeHtml(a.canonical_name)}</option>`).join("");
  if (current) sel.value = current;
}

async function renderConcerts() {
  const tbody = $("#concerts-table tbody");
  tbody.innerHTML = `<tr><td colspan="8" class="empty">加载中…</td></tr>`;
  let q = supabase
    .from("concerts")
    .select("id, city, show_date, venue, status, sale_status, sale_open_at, source_url, artist_id, artists(canonical_name)")
    .order("show_date", { ascending: false })
    .limit(200);
  const artistId = $("#concert-artist-filter").value;
  const status = $("#concert-status-filter").value;
  const sale = $("#concert-sale-filter").value;
  if (artistId) q = q.eq("artist_id", artistId);
  if (status) q = q.eq("status", status);
  if (sale) q = q.eq("sale_status", sale);
  const { data, error } = await q;
  if (error) { tbody.innerHTML = `<tr><td colspan="8" class="empty">${escapeHtml(error.message)}</td></tr>`; return; }
  tbody.innerHTML = "";
  if (!data || !data.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty">无数据</td></tr>`;
    return;
  }
  for (const c of data) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${escapeHtml(c.artists?.canonical_name || "")}</td>
      <td>${escapeHtml(c.city || "")}</td>
      <td>${escapeHtml(c.show_date || "")}</td>
      <td>${escapeHtml(c.venue || "")}</td>
      <td>${escapeHtml(c.status || "")}</td>
      <td>${escapeHtml(c.sale_status || "")}</td>
      <td>${c.sale_open_at ? fmtDate(c.sale_open_at) : ""}</td>
      <td>${c.source_url ? `<a href="${escapeAttr(c.source_url)}" target="_blank" rel="noopener">链接</a>` : ""}</td>
    `;
    tbody.appendChild(tr);
  }
}

// ---------- escape ----------
function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
function escapeAttr(s) { return escapeHtml(s); }

// ---------- init ----------
$("#login-form").addEventListener("submit", onLogin);
setupTabs();
$("#artist-form").addEventListener("submit", addArtist);
$("#user-form").addEventListener("submit", submitUser);
$("#user-cancel").addEventListener("click", resetUserForm);
$("#subscription-form").addEventListener("submit", addSubscription);
$("#concerts-refresh").addEventListener("click", renderConcerts);
$("#concert-artist-filter").addEventListener("change", renderConcerts);
$("#concert-status-filter").addEventListener("change", renderConcerts);
$("#concert-sale-filter").addEventListener("change", renderConcerts);
