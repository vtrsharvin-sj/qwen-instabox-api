/**
 * Cloudflare Worker — Qwen3.5-4B Uncensored API Proxy
 * Public URL: https://qwen-api.vtrsharvin.workers.dev
 * Auth: Bearer sharvin  OR  x-api-key: sharvin
 */

const BACKEND = "https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech";
const API_KEY  = "sharvin";

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // ── CORS preflight (no auth needed) ──────────────────────────────────────
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // ── Auth check ────────────────────────────────────────────────────────────
  const auth    = request.headers.get("Authorization") || "";
  const xapiKey = request.headers.get("x-api-key")     || "";
  const provided = auth.startsWith("Bearer ")
    ? auth.slice(7).trim()
    : xApiKey.trim();

  if (provided !== API_KEY) {
    return new Response(JSON.stringify({
      error: {
        message: "Invalid API key. Provide your key as 'Authorization: Bearer sharvin' or 'x-api-key: sharvin'.",
        type:    "authentication_error",
        param:   null,
        code:    "invalid_api_key",
      }
    }), {
      status: 401,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  }

  // ── Proxy to backend ──────────────────────────────────────────────────────
  const backendUrl = BACKEND + url.pathname + url.search;

  try {
    const proxyReq = new Request(backendUrl, {
      method:  request.method,
      headers: request.headers,
      body:    ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    });

    const res = await fetch(proxyReq);

    const newHeaders = new Headers(res.headers);
    Object.entries(corsHeaders()).forEach(([k, v]) => newHeaders.set(k, v));

    return new Response(res.body, { status: res.status, headers: newHeaders });

  } catch (err) {
    return new Response(JSON.stringify({
      error: {
        message: "Backend unreachable. Try again in 10 seconds.",
        type:    "backend_error",
        param:   null,
        code:    "backend_unreachable",
      }
    }), {
      status: 503,
      headers: { "Content-Type": "application/json", ...corsHeaders() },
    });
  }
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, x-api-key",
  };
}
