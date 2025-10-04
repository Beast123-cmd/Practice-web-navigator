import type { SearchRequest, SearchResponse } from "@/types/api";

// uses your .env.local if present, otherwise falls back to localhost:8000
const BASE =
  (import.meta as any).env?.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function searchApi(payload: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${BASE}/api/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  const json = (await res.json()) as SearchResponse;

  // normalize price to a digits-only string so your UI can render `₹${r.price}`
  const results = (json.results || []).map(r => ({
    ...r,
    price: String(r.price).replace(/[^0-9.]/g, ""), // "₹48,990" -> "48990"
  }));

  return { ...json, results };
}
