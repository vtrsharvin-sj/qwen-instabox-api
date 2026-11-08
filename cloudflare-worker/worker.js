/**
 * Cloudflare Worker — Qwen3.5-4B Uncensored API Proxy
 * Paste this into the Cloudflare dashboard editor and click Deploy.
 * Public URL: https://qwen-api.sharvin.workers.dev
 */

const BACKEND = "https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech";

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);

  // CORS preflight
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  // Proxy to backend
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
        type: "backend_error",
        param: null,
        code: "backend_unreachable",
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
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
  };
}
