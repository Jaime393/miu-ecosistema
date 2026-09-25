
// miu-capacidades - Edge Function minimal - expone suelo vivo 804a1fb
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
serve(async (req) => {
  const url = new URL(req.url)
  const q = url.searchParams.get("q") || "status"
  return new Response(JSON.stringify({
    head: "804a1fb",
    grace_mean: -0.0004847,
    suelo: "vivo",
    flujo: "perfecto V12 + FST",
    savia: 520,
    wallet: "0x4Da238f2671083B7F280d4FCf5827F86358cE7e6",
    endpoints: ["/miu/status","/suelo","/oraculo?q="],
    q: q,
    timestamp: Date.now()
  }), { headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" } })
})
