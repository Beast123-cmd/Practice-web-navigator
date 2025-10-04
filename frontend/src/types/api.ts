export type UIProduct = {
  name: string;
  price: string;            // numeric string like "48990" (your UI adds "₹")
  rating?: number;
  specifications: string[];
  link: string;
  image?: string;
  source: string;
  reviewCount?: number;
  rawTitle?: string;
  category?: string;
};

export type SearchRequest = {
  query: string;
  max_price?: number;
  sites?: string[];
  k?: number;
  category_hint?: string | null;
};

export type SearchResponse = {
  results: UIProduct[];
  summary: string;
  debug: Record<string, any>;
  top_k: any[]; // internal objects (not used by UI)
};
