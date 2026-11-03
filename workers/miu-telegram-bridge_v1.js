// MIU — miu-telegram-bridge v1
// Difunde mensajes a los grupos del enjambre (weedlima + miu_colmena)
// Rotación de bots leída en runtime desde coord (relay_config telegram_bot_token_*)
// Reemplaza al /manos/telegram de miu-oracle-v2 (muerto en Vercel)

const AUTH_OK = "MIU_2026_11";

const COORD_URL = "https://fepyzxwyneervidlybvi.supabase.co";
const COORD_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZlcHl6eHd5bmVlcnZpZGx5YnZpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk4NDc1NTQsImV4cCI6MjEwNTQyMzU1NH0.S6meOse3Xfq2d9k5nO4fjL3tseQOzvPNAsubGa0gl6k";

const GRUPOS = [-1002164790814, -1004496069595]; // weedlima, miu_colmena

async function coord(keys) {
  const claves = keys.join(",");
  const r = await fetch(
    `${COORD_URL}/rest/v1/relay_config?select=clave,valor&clave=in.(${claves})`,
    { headers: { apikey: COORD_ANON, Authorization: `Bearer ${COORD_ANON}` } }
  );
  if (!r.ok) return {};
  const rows = await r.json();
  const m = {};
  for (const row of rows) m[row.clave] = row.valor;
  return m;
}

async function getBotTokens() {
  const keys = [];
  for (let i = 1; i <= 10; i++) keys.push(`telegram_bot_token_${i}`);
  const m = await coord(keys);
  return Object.values(m).filter((v) => v && v.includes(":"));
}

async function broadcast(mensaje, sourceNode) {
  const tokens = await getBotTokens();
  if (!tokens.length) return { ok: false, error: "sin tokens en coord" };
  // rotación determinista por minuto
  const idx = Math.floor(Date.now() / 60000) % tokens.length;
  const token = tokens[idx];
  const resultados = {};
  for (let i = 0; i < GRUPOS.length; i++) {
    const gid = GRUPOS[i];
    const nombre = gid === -1002164790814 ? "weedlima" : "miu_colmena";
    try {
      const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: gid,
          text: mensaje,
        }),
      });
      resultados[nombre] = r.ok ? "ok" : `err_${r.status}`;
    } catch (e) {
      resultados[nombre] = "exception";
    }
  }
  return {
    ok: true,
    bot_index: idx,
    bots_disponibles: tokens.length,
    source_node: sourceNode || "desconocido",
    grupos: resultados,
  };
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const auth = request.headers.get("Authorization") || "";

    if (request.method === "GET" && url.pathname === "/") {
      return new Response(
        JSON.stringify({
          ok: true,
          nodo: "miu-telegram-bridge",
          funcion: "broadcast a grupos del enjambre",
          uso: "POST /broadcast {mensaje, source_node} + Authorization: Bearer MIU_2026_11",
          grupos: ["weedlima", "miu_colmena"],
        }),
        { headers: { "Content-Type": "application/json" } }
      );
    }

    if (request.method === "POST" && url.pathname === "/broadcast") {
      if (auth !== `Bearer ${AUTH_OK}`) {
        return new Response(JSON.stringify({ ok: false, error: "no autorizado" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        });
      }
      let body = {};
      try {
        body = await request.json();
      } catch (e) {}
      if (!body.mensaje) {
        return new Response(JSON.stringify({ ok: false, error: "falta mensaje" }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        });
      }
      const res = await broadcast(body.mensaje, body.source_node);
      return new Response(JSON.stringify(res), {
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ ok: false, error: "ruta desconocida" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  },
};
