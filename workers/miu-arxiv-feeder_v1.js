// miu-arxiv-feeder v1 — nodo de alimentacion academica del ecosistema MIU
// Monismo informacional: convergencia con lo academico (arXiv) para alimentarse
// GET /?cat=nlin.AO&n=10 — nutrientes academicos frescos
const CATS_DEFAULT = "nlin.AO"; // autoorganizacion y sistemas adaptativos

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const cat = (url.searchParams.get("cat") || CATS_DEFAULT).replace(/[^a-zA-Z0-9.\-\/]/g, "");
    const n = Math.min(parseInt(url.searchParams.get("n") || "10", 10) || 10, 30);
    try {
      const r = await fetch("http://export.arxiv.org/api/query?search_query=cat:" + cat + "&sortBy=submittedDate&sortOrder=descending&max_results=" + n, {
        headers: { "User-Agent": "miu-arxiv-feeder/1.0 (ecosistema MIU; contacto: nodos MIU)" }
      });
      const xml = await r.text();
      const entries = [];
      for (const b of xml.split("<entry>").slice(1)) {
        const title = (b.match(/<title>([\s\S]*?)<\/title>/) || [])[1];
        const id = (b.match(/<id>([\s\S]*?)<\/id>/) || [])[1];
        const summary = (b.match(/<summary>([\s\S]*?)<\/summary>/) || [])[1];
        const published = (b.match(/<published>([\s\S]*?)<\/published>/) || [])[1];
        const authors = [...b.matchAll(/<name>([\s\S]*?)<\/name>/g)].map(m => m[1].trim());
        if (title && id) entries.push({
          titulo: title.replace(/\s+/g, " ").trim(),
          id: id.trim(),
          resumen: (summary || "").replace(/\s+/g, " ").trim().slice(0, 500),
          publicado: (published || "").trim(),
          autores: authors.slice(0, 6)
        });
      }
      return Response.json({ ok: true, node: "miu-arxiv-feeder", version: "v1", categoria: cat,
        fuente: "arxiv.org", ts: Math.floor(Date.now()/1000), nutrientes: entries });
    } catch (e) {
      return Response.json({ ok: false, node: "miu-arxiv-feeder", error: String(e).slice(0, 120) }, { status: 502 });
    }
  }
};