export type Rating = string;

export interface Opportunity {
  id?: string;
  opportunity_id?: string;
  title: string;
  source?: string;
  source_group?: string;
  published?: string;
  url?: string;
  comments_url?: string;
  category?: {
    name?: string;
    description?: string;
  };
  total_score?: number;
  rating?: Rating;
  content_summary?: string;
  key_insight?: string;
  action_items?: string;
  scores?: Record<string, number>;
  score_reasons?: Record<string, string>;
  redlines?: Array<string | { id?: number; name?: string; reason?: string }>;
  redline_checks?: Record<string, string>;
  evidence_count?: number;
  source_count?: number;
  sources?: string[];
  source_groups?: string[];
  cluster_keywords?: string[];
  seen_count?: number;
  first_seen_at?: string;
  last_seen_at?: string;
}

export interface Signal {
  id: string;
  title: string;
  content?: string;
  source?: string;
  source_group?: string;
  url?: string;
  comments_url?: string;
  published_at?: string;
  fetched_at?: string;
}

export interface ScanPayload {
  query?: string;
  opportunity_type?: string;
  limit?: number;
  quick?: boolean;
  include_keywords?: string[];
  exclude_keywords?: string[];
  ai_depth?: string;
}

export interface ScanResult {
  ready: boolean;
  opportunities: Opportunity[];
  counts?: Record<string, number>;
  metadata?: Record<string, unknown>;
  redline_stats?: Record<string, number>;
}

export interface OpportunityListResult {
  opportunities: Opportunity[];
  total: number;
  limit: number;
  offset: number;
}

export interface AiReport {
  id: string;
  opportunity_id: string;
  report_markdown?: string;
  report_json?: Record<string, unknown>;
  provider?: string;
  model?: string;
  cache_hit?: boolean;
}

export interface WaitlistPayload {
  email: string;
  public_slug?: string;
  query?: string;
  opportunity_id?: string;
  source?: string;
  utm?: Record<string, string>;
  company_name?: string;
}

export interface WaitlistSignup {
  id: string;
  email: string;
  opportunity_id?: string;
  public_slug?: string;
  query?: string;
  source?: string;
  utm?: Record<string, string>;
  created_at?: string;
}

export interface PublicOpportunity {
  id: string;
  slug: string;
  path?: string;
  url: string;
  markdown_path?: string;
  markdown_url?: string;
  title?: string;
  summary?: string;
  rating?: string;
  total_score?: number;
  evidence_count?: number;
  source_count?: number;
  lead_count?: number;
  last_seen_at?: string;
}

export interface AppConfig {
  public_base_url: string;
}

export interface WaitlistStats {
  total: number;
  public_page_count: number;
  by_slug: Array<{ slug: string; count: number }>;
  by_source: Array<{ source: string; count: number }>;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload?.error === "string" ? payload.error : "Request failed";
    throw new Error(message);
  }
  return payload as T;
}

export function getOpportunityId(opportunity: Opportunity): string {
  return opportunity.opportunity_id || opportunity.id || "";
}

export function slugifyOpportunity(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 90);
}

export function queryFromSlug(slug: string): string {
  return slug.replace(/-/g, " ").trim();
}

export function listOpportunities(query?: string): Promise<OpportunityListResult> {
  const params = new URLSearchParams({ limit: "50", offset: "0" });
  if (query?.trim()) {
    params.set("q", query.trim());
  }
  return requestJson<OpportunityListResult>(`/api/opportunities?${params.toString()}`);
}

export function runScan(payload: ScanPayload): Promise<ScanResult> {
  return requestJson<ScanResult>("/api/scan", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listOpportunitySignals(opportunityId: string): Promise<{ signals: Signal[] }> {
  return requestJson<{ signals: Signal[] }>(`/api/opportunities/${encodeURIComponent(opportunityId)}/signals`);
}

export function createAiReport(opportunityId: string): Promise<{ ready: boolean; report: AiReport }> {
  return requestJson<{ ready: boolean; report: AiReport }>("/api/ai/report", {
    method: "POST",
    body: JSON.stringify({
      opportunity_id: opportunityId,
      report_type: "feasibility",
      force: false,
    }),
  });
}

export function createWaitlistSignup(payload: WaitlistPayload): Promise<{ signup: Record<string, unknown> }> {
  return requestJson<{ signup: Record<string, unknown> }>("/api/waitlist", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listWaitlistSignups(): Promise<{ waitlist: WaitlistSignup[] }> {
  return requestJson<{ waitlist: WaitlistSignup[] }>("/api/waitlist?limit=100");
}

export function getWaitlistStats(): Promise<{ stats: WaitlistStats }> {
  return requestJson<{ stats: WaitlistStats }>("/api/waitlist/stats");
}

export function listPublicOpportunities(): Promise<{ opportunities: PublicOpportunity[] }> {
  return requestJson<{ opportunities: PublicOpportunity[] }>("/public-opportunities.json");
}

export function getAppConfig(): Promise<AppConfig> {
  return requestJson<AppConfig>("/api/config");
}
