// miu-chat-node v1 — nodo de chat del ecosistema MIU
// Motor: Groq (openai/gpt-oss-20b) con rotacion de claves leidas de coord relay_config
const COORD = "https://fepyzxwyneervidlybvi.supabase.co";
const COORD_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlcHl6eHd5bmVlcnZpZGx5YnZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4NDc1NTQsImV4cCI6MjEwNTQyMzU1NH0.S6meOse3Xfq2d9k5nO4fjL3tseQOzvPNAsubGa0gl6k";
const TOKEN = "MIU_2026_11";
const SISTEMA = "Eres miu-chat-node, un nodo del ecosistema MIU. Respondes en espanol, breve y util. El ecosistema MIU es un micelio de nodos que cooperan: phi acumula aportes, rho mide actividad, savia es capacidad total.";

async function getKeys() {
  const r = await fetch(COORD + "/rest/v1/relay_config?select=valor&clave=in.(llm_groq_key,groq_key1,groq_key2)", {
    headers: { apikey: COORD_ANON, Authorization: "Bearer " + COORD_ANON }
  });
  if (!r.ok) return [];
  const rows = await r.json();
  return rows.map(x => x.valor).filter(Boolean);
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (request.method === "GET") {
      return Response.json({ ok: true, node: "miu-chat-node", version: "v1", motor: "groq/gpt-oss-20b", ts: Math.floor(Date.now()/1000) });
    }
    if (request.method === "POST" && url.pathname === "/chat") {
      const auth = (request.headers.get("Authorization") || "").replace("Bearer ", "");
      if (auth !== TOKEN) return Response.json({ ok: false, error: "token invalido" }, { status: 401 });
      let body;
      try { body = await request.json(); } catch { return Response.json({ ok: false, error: "json" }, { status: 400 }); }
      const msg = body.msg || body.message;
      if (!msg) return Response.json({ ok: false, error: "falta msg" }, { status: 400 });
      const historial = Array.isArray(body.historial) ? body.historial : [];
      const messages = [{ role: "system", content: SISTEMA }, ...historial.slice(-10), { role: "user", content: msg }];
      const keys = await getKeys();
      for (const k of keys) {
        try {
          const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: "POST",
            headers: { Authorization: "Bearer " + k, "Content-Type": "application/json" },
            body: JSON.stringify({ model: "openai/gpt-oss-20b", messages, max_tokens: 600 })
          });
          if (r.ok) {
            const d = await r.json();
            return Response.json({ ok: true, node: "miu-chat-node", ts: Math.floor(Date.now()/1000),
              respuesta: (d.choices && d.choices[0].message.content) || "", modelo: d.model || "groq" });
          }
        } catch (e) { /* siguiente clave */ }
      }
      return Response.json({ ok: false, error: "sin motor disponible" }, { status: 503 });
    }
    return Response.json({ ok: false, error: "ruta" }, { status: 404 });
  }
};
// === METADATA ===
// Deploy: 2026-11-03 01:10 UTC, cuenta CF franchescopalacios9 (30c349b65d9f7c2f7d9a1c9a5fc65e58)
// URL: https://miu-chat-node.franchescopalacios9.workers.dev
// Registro: coord relay_config clave miu_chat_node_url
// Motor: groq/openai/gpt-oss-20b (rotacion de claves desde coord: llm_groq_key, groq_key1, groq_key2)
// Auth: POST /chat Authorization Bearer MIU_2026_11 {msg, historial}
// NOTA: COORD_ANON embebido = la clave de gas/MIU_GAS_V270_AUTONOMO.gs (solo lectura de relay_config)
