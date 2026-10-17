"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, X } from "lucide-react";
import { useBrandContext } from "@/lib/brand-context";
import {
  BrandColor,
  BrandProfile,
  ContentPillar,
  createPillar,
  deletePillar,
  getBrandProfile,
  listPillars,
  updateBrandProfile,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const INDUSTRIES = [
  "Fashion & apparel",
  "Beauty",
  "Food & beverage",
  "Retail",
  "Health & wellness",
  "Professional services",
  "Home & lifestyle",
  "Other",
];

const SLIDER_FIELDS = [
  { key: "creativity_level", label: "Creativity" },
  { key: "brand_consistency_level", label: "Brand consistency" },
  { key: "reference_priority_level", label: "Reference-image priority" },
  { key: "content_diversity_level", label: "Content diversity" },
] as const;

function emptyProfile(brandId: string): BrandProfile {
  return {
    brand_id: brandId,
    industry: null,
    description: null,
    website: null,
    location: null,
    target_customer: null,
    audience_age_range: null,
    audience_interests: null,
    brand_colors: [],
    typography: null,
    photography_style: null,
    tone: null,
    voice: null,
    brand_dna: [],
    things_i_like: null,
    things_i_dislike: null,
    visual_elements_to_avoid: null,
    words_to_avoid: null,
    avoid_neon: false,
    avoid_clutter: false,
    creativity_level: 2,
    brand_consistency_level: 2,
    reference_priority_level: 2,
    content_diversity_level: 2,
    logo_storage_path: null,
  };
}

export default function BrandBrainPage() {
  const { brand } = useBrandContext();
  const [profile, setProfile] = useState<BrandProfile | null>(null);
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [newPillar, setNewPillar] = useState("");
  const [dnaInput, setDnaInput] = useState("");
  const [colorInput, setColorInput] = useState({ hex: "#F59197", label: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  const queryClient = useQueryClient();
  const brandQuery = useQuery({
    queryKey: ["brand-profile", brand?.id],
    queryFn: async () => {
      const [p, pl] = await Promise.all([
        getBrandProfile(brand!.id).catch(() => emptyProfile(brand!.id)),
        listPillars(brand!.id).catch(() => [] as ContentPillar[]),
      ]);
      return { profile: p ?? emptyProfile(brand!.id), pillars: pl };
    },
    enabled: !!brand,
  });

  useEffect(() => {
    if (!brandQuery.data) return;
    setProfile(brandQuery.data.profile);
    setPillars(brandQuery.data.pillars);
    setError(null);
  }, [brandQuery.data]);

  useEffect(() => {
    if (brandQuery.error) {
      setError(
        brandQuery.error instanceof Error
          ? brandQuery.error.message
          : "Failed to load brand profile",
      );
    }
  }, [brandQuery.error]);

  const load = async () => {
    await queryClient.invalidateQueries({ queryKey: ["brand-profile", brand?.id] });
  };

  function set<K extends keyof BrandProfile>(key: K, value: BrandProfile[K]) {
    setProfile((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function save() {
    if (!brand || !profile) return;
    setSaving(true);
    try {
      const saved = await updateBrandProfile(brand.id, profile);
      setProfile(saved);
      setSavedAt(Date.now());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save brand profile");
    } finally {
      setSaving(false);
    }
  }

  async function addPillar() {
    if (!brand || !newPillar.trim()) return;
    try {
      const created = await createPillar(brand.id, {
        name: newPillar.trim(),
        sort_order: pillars.length,
      });
      setPillars((prev) => [...prev, created]);
      setNewPillar("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add pillar");
    }
  }

  async function removePillar(id: string) {
    setPillars((prev) => prev.filter((p) => p.id !== id));
    try {
      await deletePillar(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove pillar");
      void load();
    }
  }

  function addDna() {
    if (!dnaInput.trim() || !profile) return;
    set("brand_dna", [...(profile.brand_dna ?? []), dnaInput.trim()]);
    setDnaInput("");
  }

  function removeDna(value: string) {
    if (!profile) return;
    set("brand_dna", (profile.brand_dna ?? []).filter((d) => d !== value));
  }

  function addColor() {
    if (!colorInput.label.trim() || !profile) return;
    const next: BrandColor[] = [...(profile.brand_colors ?? []), colorInput];
    set("brand_colors", next);
    setColorInput({ hex: "#F59197", label: "" });
  }

  function removeColor(hex: string) {
    if (!profile) return;
    set("brand_colors", (profile.brand_colors ?? []).filter((c) => c.hex !== hex));
  }

  if (!brand || !profile) {
    return <p className="text-sm text-muted-foreground">Loading brand profile…</p>;
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8">
      <section>
        <p className="mb-2 text-sm font-medium text-primary">Brand Brain</p>
        <h2 className="mb-2 font-serif text-3xl font-semibold tracking-tight text-foreground">
          This is what Maneja knows about {brand.name}.
        </h2>
        <p className="max-w-2xl text-muted-foreground">
          Keep your brand details current so every recommendation feels considered, consistent,
          and unmistakably yours.
        </p>
      </section>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <Card className="gap-4 rounded-xl border-primary/30 bg-[#fffaf8] p-5 sm:p-6">
        <CardHeader className="flex-row items-start justify-between gap-4 p-0">
          <div>
            <CardTitle className="font-serif text-lg">Brand DNA</CardTitle>
            <CardDescription>The qualities that guide your content.</CardDescription>
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2 p-0">
          {(profile.brand_dna ?? []).map((d) => (
            <Badge key={d} variant="secondary" className="gap-1 rounded-full">
              {d}
              <button type="button" aria-label={`Remove ${d}`} onClick={() => removeDna(d)}>
                <X className="size-3" />
              </button>
            </Badge>
          ))}
          <div className="flex items-center gap-2">
            <Input
              value={dnaInput}
              onChange={(e) => setDnaInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addDna())}
              placeholder="Add a quality (e.g. Warm)"
              className="h-8 w-44 rounded-full"
            />
            <Button type="button" size="sm" variant="outline" onClick={addDna}>
              <Plus className="size-3.5" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">Business</CardTitle>
            <CardDescription>The foundation of your brand profile.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-0">
            <div className="grid gap-2">
              <Label>Business name</Label>
              <Input value={brand.name} disabled />
            </div>
            <div className="grid gap-2">
              <Label>Industry</Label>
              <Select
                value={profile.industry ?? undefined}
                onValueChange={(v) => set("industry", v)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select an industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map((i) => (
                    <SelectItem key={i} value={i}>
                      {i}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>Description</Label>
              <Textarea
                value={profile.description ?? ""}
                onChange={(e) => set("description", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Website</Label>
              <Input value={profile.website ?? ""} onChange={(e) => set("website", e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label>Location</Label>
              <Input value={profile.location ?? ""} onChange={(e) => set("location", e.target.value)} />
            </div>
          </CardContent>
        </Card>

        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">Audience</CardTitle>
            <CardDescription>Who your content is made for.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-0">
            <div className="grid gap-2">
              <Label>Target customer</Label>
              <Input
                value={profile.target_customer ?? ""}
                onChange={(e) => set("target_customer", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Age range</Label>
              <Input
                value={profile.audience_age_range ?? ""}
                onChange={(e) => set("audience_age_range", e.target.value)}
                placeholder="e.g. 25–44"
              />
            </div>
            <div className="grid gap-2">
              <Label>Interests</Label>
              <Input
                value={profile.audience_interests ?? ""}
                onChange={(e) => set("audience_interests", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">Visual identity</CardTitle>
            <CardDescription>Your visual language and references.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5 p-0">
            <div className="flex flex-wrap items-center gap-3">
              {(profile.brand_colors ?? []).map((c) => (
                <div
                  key={c.hex}
                  className="flex items-center gap-2 rounded-lg border border-border px-2 py-2 text-sm"
                >
                  <span
                    className="size-5 rounded-full border border-border"
                    style={{ background: c.hex }}
                  />
                  {c.hex} {c.label ? `· ${c.label}` : ""}
                  <button type="button" aria-label={`Remove ${c.hex}`} onClick={() => removeColor(c.hex)}>
                    <X className="size-3.5" />
                  </button>
                </div>
              ))}
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={colorInput.hex}
                  onChange={(e) => setColorInput((prev) => ({ ...prev, hex: e.target.value }))}
                  className="size-8 rounded border border-border"
                  aria-label="Pick color"
                />
                <Input
                  value={colorInput.label}
                  onChange={(e) => setColorInput((prev) => ({ ...prev, label: e.target.value }))}
                  placeholder="Label"
                  className="h-9 w-32"
                />
                <Button type="button" size="sm" variant="outline" onClick={addColor}>
                  <Plus className="size-3.5" />
                </Button>
              </div>
            </div>
            <div className="grid gap-2">
              <Label>Typography</Label>
              <Input
                value={profile.typography ?? ""}
                onChange={(e) => set("typography", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Photography</Label>
              <Input
                value={profile.photography_style ?? ""}
                onChange={(e) => set("photography_style", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">Content personality</CardTitle>
            <CardDescription>How your brand sounds and what it talks about.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-0">
            <div className="grid gap-2">
              <Label>Tone</Label>
              <Input value={profile.tone ?? ""} onChange={(e) => set("tone", e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label>Voice</Label>
              <Input value={profile.voice ?? ""} onChange={(e) => set("voice", e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label>Content pillars</Label>
              <div className="flex flex-wrap items-center gap-2">
                {pillars.map((p) => (
                  <Badge key={p.id} variant="secondary" className="gap-1 rounded-full">
                    {p.name}
                    <button
                      type="button"
                      aria-label={`Remove ${p.name}`}
                      onClick={() => void removePillar(p.id)}
                    >
                      <X className="size-3" />
                    </button>
                  </Badge>
                ))}
                <div className="flex items-center gap-2">
                  <Input
                    value={newPillar}
                    onChange={(e) => setNewPillar(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addPillar())}
                    placeholder="e.g. Education"
                    className="h-8 w-40 rounded-full"
                  />
                  <Button type="button" size="sm" variant="outline" onClick={addPillar}>
                    <Plus className="size-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">Preferences</CardTitle>
            <CardDescription>Helpful boundaries for more relevant suggestions.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 p-0">
            <div className="grid gap-2">
              <Label>Things I like</Label>
              <Input
                value={profile.things_i_like ?? ""}
                onChange={(e) => set("things_i_like", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Things I don&apos;t like</Label>
              <Input
                value={profile.things_i_dislike ?? ""}
                onChange={(e) => set("things_i_dislike", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Visual elements to avoid</Label>
              <Input
                value={profile.visual_elements_to_avoid ?? ""}
                onChange={(e) => set("visual_elements_to_avoid", e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label>Words to avoid</Label>
              <Input
                value={profile.words_to_avoid ?? ""}
                onChange={(e) => set("words_to_avoid", e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-3 pt-1">
              <label className="flex items-center gap-3 text-sm">
                <Checkbox
                  checked={Boolean(profile.avoid_neon)}
                  onCheckedChange={(v) => set("avoid_neon", Boolean(v))}
                />
                Avoid neon
              </label>
              <label className="flex items-center gap-3 text-sm">
                <Checkbox
                  checked={Boolean(profile.avoid_clutter)}
                  onCheckedChange={(v) => set("avoid_clutter", Boolean(v))}
                />
                Avoid clutter
              </label>
            </div>
          </CardContent>
        </Card>

        <Card className="gap-6 rounded-xl border-border p-5 sm:p-6">
          <CardHeader className="gap-1 p-0">
            <CardTitle className="font-serif">AI behaviour</CardTitle>
            <CardDescription>Set the balance Maneja uses when creating content.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5 p-0">
            {SLIDER_FIELDS.map(({ key, label }) => (
              <div key={key} className="grid gap-2">
                <Label>{label}</Label>
                <input
                  aria-label={label}
                  type="range"
                  min={1}
                  max={3}
                  step={1}
                  value={profile[key] ?? 2}
                  onChange={(e) => set(key, Number(e.target.value))}
                  className="w-full accent-primary"
                />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="flex items-center justify-end gap-3 border-t border-border pt-6">
        {savedAt ? <span className="text-sm text-muted-foreground">Saved</span> : null}
        <Button onClick={save} disabled={saving} className="gap-2">
          <Check className="size-4" />
          {saving ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </div>
  );
}
