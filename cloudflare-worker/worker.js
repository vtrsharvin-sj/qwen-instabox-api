/**
 * Cloudflare Worker — Qwen3.5-4B Uncensored API Proxy
 * Public URL: https://qwen-api.vtrsharvin.workers.dev
 *
 * API key is stored as a Cloudflare secret — NOT hardcoded here.
 * To set it:
 *   Workers dashboard → qwen-api → Settings → Variables → Add secret
 *   Name: API_KEY  |  Value: your_secret_key
 */

const BACKEND = "https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech";

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // ── CORS preflight ────────────────────────────────────────────────────────
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // ── /docs — no auth needed ────────────────────────────────────────────────
  if (url.pathname === "/docs" || url.pathname.startsWith("/openapi")) {
    const res = await fetch(new Request(BACKEND + url.pathname + url.search, {
      method: request.method, headers: request.headers,
    }));
    const h = new Headers(res.headers);
    Object.entries(corsHeaders()).forEach(([k, v]) => h.set(k, v));
    return new Response(res.body, { status: res.status, headers: h });
  }

  // ── Browser GET with no auth → 405 ───────────────────────────────────────
  const auth     = request.headers.get("Authorization") || "";
  const xApiKey  = request.headers.get("x-api-key")     || "";
  const provided = auth.startsWith("Bearer ") ? auth.slice(7).trim() : xApiKey.trim();

  if (request.method === "GET" && provided === "") {
    return new Response(JSON.stringify({
      error: { message: "Only POST requests are supported.", type: "invalid_request_error", param: null, code: "method_not_supported" }
    }), { status: 405, headers: { "Content-Type": "application/json", ...corsHeaders() } });
  }

  // ── Auth check against secret ─────────────────────────────────────────────
  // API_KEY is injected by Cloudflare from Worker secrets — never in source code
  if (provided !== API_KEY) {
    return new Response(JSON.stringify({
      error: { message: "Incorrect API key provided.", type: "authentication_error", param: null, code: "invalid_api_key" }
    }), { status: 401, headers: { "Content-Type": "application/json", ...corsHeaders() } });
  }

  // ── Proxy to backend ──────────────────────────────────────────────────────
  try {
    const res = await fetch(new Request(BACKEND + url.pathname + url.search, {
      method:  request.method,
      headers: request.headers,
      body:    ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    }));

    const h = new Headers(res.headers);
    Object.entries(corsHeaders()).forEach(([k, v]) => h.set(k, v));
    return new Response(res.body, { status: res.status, headers: h });

  } catch (err) {
    return new Response(JSON.stringify({
      error: { message: "Backend unreachable. Try again in 10 seconds.", type: "backend_error", param: null, code: "backend_unreachable" }
    }), { status: 503, headers: { "Content-Type": "application/json", ...corsHeaders() } });
  }
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
  };
}
