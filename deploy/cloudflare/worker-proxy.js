/**
 * Cloudflare Worker reverse proxy for backend API.
 * Route example:
 *   api.yourdomain.com/*  -> this worker
 *
 * Set BACKEND_ORIGIN in wrangler.toml vars:
 *   BACKEND_ORIGIN = "https://api-origin.yourdomain.com"
 */

export default {
  async fetch(request, env) {
    const origin = env.BACKEND_ORIGIN;
    if (!origin) {
      return new Response("BACKEND_ORIGIN is not configured", { status: 500 });
    }

    const url = new URL(request.url);
    const target = new URL(origin);
    target.pathname = url.pathname;
    target.search = url.search;

    const proxyReq = new Request(target.toString(), request);
    const resp = await fetch(proxyReq, { cf: { cacheEverything: false } });

    const out = new Response(resp.body, resp);
    out.headers.set("Access-Control-Allow-Origin", "*");
    out.headers.set("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS");
    out.headers.set("Access-Control-Allow-Headers", "*");
    return out;
  },
};

