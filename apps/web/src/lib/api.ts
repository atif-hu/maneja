import { createClient } from "@/lib/supabase/client";

export type Brand = {
  id: string;
  name: string;
  slug: string;
  timezone: string;
  daily_run_at: string;
  status: string;
  style_guide: string | null;
  created_at: string;
  updated_at: string;
};

export type ConceptType = "product" | "lifestyle" | "engagement";

export type ContentIdeaSummary = {
  headline: string;
  rationale: string;
  concept_type?: ConceptType | null;
};

export type GeneratedImage = {
  id: string;
  run_id: string;
  brand_id: string;
  slot: number;
  prompt: string;
  storage_path: string | null;
  status: string;
  provider: string | null;
  signed_url: string | null;
  created_at: string;
  updated_at: string;
  concept_type?: ConceptType | null;
  content_idea?: ContentIdeaSummary | null;
};

export type GenerationRun = {
  id: string;
  brand_id: string;
  scheduled_for: string;
  status: string;
  agent_meta: Record<string, unknown>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
};

export type BrandColor = { hex: string; label: string };

export type BrandProfile = {
  brand_id: string;
  industry: string | null;
  description: string | null;
  website: string | null;
  location: string | null;
  target_customer: string | null;
  audience_age_range: string | null;
  audience_interests: string | null;
  brand_colors: BrandColor[] | null;
  typography: string | null;
  photography_style: string | null;
  tone: string | null;
  voice: string | null;
  brand_dna: string[] | null;
  things_i_like: string | null;
  things_i_dislike: string | null;
  visual_elements_to_avoid: string | null;
  words_to_avoid: string | null;
  avoid_neon: boolean | null;
  avoid_clutter: boolean | null;
  creativity_level: number | null;
  brand_consistency_level: number | null;
  reference_priority_level: number | null;
  content_diversity_level: number | null;
  logo_storage_path: string | null;
};

export type Product = {
  id: string;
  brand_id: string;
  name: string;
  description: string | null;
  price: string | null;
  category: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
};

export type ContentPillar = {
  id: string;
  brand_id: string;
  name: string;
  description: string | null;
  sort_order: number;
};

export type ReferenceCategory =
  | "products"
  | "brand"
  | "lifestyle"
  | "people"
  | "locations"
  | "inspiration";

export type ReferenceImage = {
  id: string;
  brand_id: string;
  product_id: string | null;
  category: ReferenceCategory;
  title: string | null;
  signed_url: string | null;
  is_priority: boolean;
  usage_count: number;
  embedding_status: "pending" | "ready" | "failed";
  uploaded_at: string;
};

export type Notification = {
  id: string;
  brand_id: string;
  type: string;
  title: string;
  body: string | null;
  link_path: string | null;
  read_at: string | null;
  created_at: string;
};

export type BrandStats = {
  pending_review: number;
  approved_this_week: number;
  rejected_this_week: number;
  total_reference_images: number;
};

const supabase = createClient();

async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const token = await getAccessToken();
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const isFormData = init.body instanceof FormData;
  const headers = new Headers(init.headers);
  if (!isFormData) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${base}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `API error ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// -- Brands ------------------------------------------------------------

export async function listBrands() {
  return apiFetch<Brand[]>("/brands");
}

export async function createBrand(body: {
  name: string;
  timezone?: string;
  style_guide?: string;
}) {
  return apiFetch<Brand>("/brands", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getBrand(brandId: string) {
  return apiFetch<Brand>(`/brands/${brandId}`);
}

export async function updateBrand(brandId: string, body: Partial<Brand>) {
  return apiFetch<Brand>(`/brands/${brandId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

// -- Images / runs -------------------------------------------------------

export async function listImages(brandId: string, status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<GeneratedImage[]>(`/brands/${brandId}/images${q}`);
}

export async function listRuns(brandId: string) {
  return apiFetch<GenerationRun[]>(`/brands/${brandId}/runs`);
}

export async function approveImage(imageId: string, note?: string) {
  return apiFetch(`/images/${imageId}/approve`, {
    method: "POST",
    body: JSON.stringify({ note: note ?? null }),
  });
}

export async function rejectImage(imageId: string, note?: string) {
  return apiFetch(`/images/${imageId}/reject`, {
    method: "POST",
    body: JSON.stringify({ note: note ?? null }),
  });
}

// -- Brand profile -------------------------------------------------------

export async function getBrandProfile(brandId: string) {
  return apiFetch<BrandProfile>(`/brands/${brandId}/profile`);
}

export async function updateBrandProfile(
  brandId: string,
  body: Partial<BrandProfile>,
) {
  return apiFetch<BrandProfile>(`/brands/${brandId}/profile`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

// -- Products --------------------------------------------------------------

export async function listProducts(brandId: string) {
  return apiFetch<Product[]>(`/brands/${brandId}/products`);
}

export async function createProduct(
  brandId: string,
  body: Partial<Product>,
) {
  return apiFetch<Product>(`/brands/${brandId}/products`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updateProduct(productId: string, body: Partial<Product>) {
  return apiFetch<Product>(`/products/${productId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deleteProduct(productId: string) {
  return apiFetch<void>(`/products/${productId}`, { method: "DELETE" });
}

// -- Content pillars ---------------------------------------------------

export async function listPillars(brandId: string) {
  return apiFetch<ContentPillar[]>(`/brands/${brandId}/pillars`);
}

export async function createPillar(
  brandId: string,
  body: { name: string; description?: string; sort_order?: number },
) {
  return apiFetch<ContentPillar>(`/brands/${brandId}/pillars`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function updatePillar(
  pillarId: string,
  body: Partial<ContentPillar>,
) {
  return apiFetch<ContentPillar>(`/pillars/${pillarId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function deletePillar(pillarId: string) {
  return apiFetch<void>(`/pillars/${pillarId}`, { method: "DELETE" });
}

// -- Reference images ------------------------------------------------------

export async function listReferenceImages(
  brandId: string,
  category?: ReferenceCategory | "all",
) {
  const q = category && category !== "all" ? `?category=${encodeURIComponent(category)}` : "";
  return apiFetch<ReferenceImage[]>(`/brands/${brandId}/reference-images${q}`);
}

export async function uploadReferenceImage(
  brandId: string,
  body: { file: File; category: ReferenceCategory; title?: string; productId?: string },
) {
  const form = new FormData();
  form.set("file", body.file);
  form.set("category", body.category);
  if (body.title) form.set("title", body.title);
  if (body.productId) form.set("product_id", body.productId);
  return apiFetch<ReferenceImage>(`/brands/${brandId}/reference-images`, {
    method: "POST",
    body: form,
  });
}

export async function updateReferenceImage(
  brandId: string,
  referenceImageId: string,
  body: { is_priority: boolean },
) {
  return apiFetch<ReferenceImage>(
    `/brands/${brandId}/reference-images/${referenceImageId}`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}

export async function deleteReferenceImage(brandId: string, referenceImageId: string) {
  return apiFetch<void>(`/brands/${brandId}/reference-images/${referenceImageId}`, {
    method: "DELETE",
  });
}

// -- Notifications -------------------------------------------------------

export async function listNotifications(unreadOnly = false) {
  const q = unreadOnly ? "?unread=true" : "";
  return apiFetch<Notification[]>(`/notifications${q}`);
}

export async function markNotificationRead(notificationId: string) {
  return apiFetch<void>(`/notifications/${notificationId}/read`, { method: "POST" });
}

export async function markAllNotificationsRead() {
  return apiFetch<void>(`/notifications/read-all`, { method: "POST" });
}

// -- On-demand generation --------------------------------------------------

export async function generateNow(
  brandId: string,
  body: { promotion: string; content_type?: string; platform?: string },
) {
  return apiFetch<GenerationRun>(`/brands/${brandId}/jobs/generate-now`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// -- Stats -----------------------------------------------------------------

export async function getBrandStats(brandId: string) {
  return apiFetch<BrandStats>(`/brands/${brandId}/stats`);
}
