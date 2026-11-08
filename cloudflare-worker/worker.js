/**
 * Cloudflare Worker — Proxy for Qwen3.5-4B Uncensored API
 * Public URL: https://qwen-api.sharvin.workers.dev
 * Forwards all requests to the Instabox backend.
 */

const BACKEND = "https://8000-agq3kirkx25dxx5s7haejfgk4a.instabox.tech";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // ── CORS preflight ────────────────────────────────────────────────────────
    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders(),
      });
    }

    // ── Proxy request to backend ──────────────────────────────────────────────
    const backendUrl = BACKEND + url.pathname + url.search;

    const proxyRequest = new Request(backendUrl, {
      method:  request.method,
      headers: request.headers,
      body:    request.method !== "GET" && request.method !== "HEAD"
                 ? request.body
                 : undefined,
    });

    let response;
    try {
      response = await fetch(proxyRequest);
    } catch (err) {
      return new Response(
        JSON.stringify({
          error: {
            message: "Backend unreachable. The Instabox server may be starting up — try again in 10 seconds.",
            type: "backend_error",
            param: null,
            code: "backend_unreachable",
          },
        }),
        {
          status: 503,
          headers: { "Content-Type": "application/json", ...corsHeaders() },
        }
      );
    }

    // ── Stream-through response with CORS headers ─────────────────────────────
    const newHeaders = new Headers(response.headers);
    Object.entries(corsHeaders()).forEach(([k, v]) => newHeaders.set(k, v));

    return new Response(response.body, {
      status:  response.status,
      headers: newHeaders,
    });
  },
};

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key",
  };
}
