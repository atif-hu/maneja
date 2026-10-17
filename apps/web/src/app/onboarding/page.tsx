"use client";

import { useRef, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ImagePlus,
  Plus,
  Upload,
  X,
} from "lucide-react";
import {
  BrandColor,
  createBrand,
  ReferenceCategory,
  updateBrandProfile,
  updateReferenceImage,
  uploadReferenceImage,
} from "@/lib/api";
import { LAST_BRAND_KEY } from "@/lib/brand-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const STEPS = ["Business basics", "Brand identity", "Reference images"];

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

type SliderKey = (typeof SLIDER_FIELDS)[number]["key"];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Step 1 — business basics
  const [name, setName] = useState("");
  const [industry, setIndustry] = useState("");
  const [website, setWebsite] = useState("");
  const [location, setLocation] = useState("");
  const [brandId, setBrandId] = useState<string | null>(null);

  // Step 2 — brand identity
  const [description, setDescription] = useState("");
  const [targetCustomer, setTargetCustomer] = useState("");
  const [ageRange, setAgeRange] = useState("");
  const [interests, setInterests] = useState("");
  const [colors, setColors] = useState<BrandColor[]>([]);
  const [colorInput, setColorInput] = useState({ hex: "#F59197", label: "" });
  const [typography, setTypography] = useState("");
  const [photographyStyle, setPhotographyStyle] = useState("");
  const [tone, setTone] = useState("");
  const [voice, setVoice] = useState("");
  const [dna, setDna] = useState<string[]>([]);
  const [dnaInput, setDnaInput] = useState("");
  const [thingsLike, setThingsLike] = useState("");
  const [thingsDislike, setThingsDislike] = useState("");
  const [avoidElements, setAvoidElements] = useState("");
  const [avoidWords, setAvoidWords] = useState("");
  const [avoidNeon, setAvoidNeon] = useState(true);
  const [avoidClutter, setAvoidClutter] = useState(true);
  const [sliders, setSliders] = useState<Record<SliderKey, number>>({
    creativity_level: 2,
    brand_consistency_level: 3,
    reference_priority_level: 3,
    content_diversity_level: 2,
  });

  // Step 3 — reference images
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [refCategory, setRefCategory] = useState<ReferenceCategory>("brand");
  const [refPriority, setRefPriority] = useState(true);
  const [uploaded, setUploaded] = useState(false);

  function addColor() {
    if (!colorInput.label.trim()) return;
    setColors((prev) => [...prev, colorInput]);
    setColorInput({ hex: "#F59197", label: "" });
  }

  function removeColor(hex: string) {
    setColors((prev) => prev.filter((c) => c.hex !== hex));
  }

  function addDna() {
    if (!dnaInput.trim()) return;
    setDna((prev) => [...prev, dnaInput.trim()]);
    setDnaInput("");
  }

  async function goToStep2() {
    if (!name.trim()) {
      setError("Business name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const brand = await createBrand({
        name: name.trim(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      setBrandId(brand.id);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(LAST_BRAND_KEY, brand.id);
      }
      await updateBrandProfile(brand.id, { industry, website, location });
      setStep(1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create business");
    } finally {
      setSaving(false);
    }
  }

  async function goToStep3() {
    if (!brandId) return;
    setSaving(true);
    setError(null);
    try {
      await updateBrandProfile(brandId, {
        description,
        target_customer: targetCustomer,
        audience_age_range: ageRange,
        audience_interests: interests,
        brand_colors: colors,
        typography,
        photography_style: photographyStyle,
        tone,
        voice,
        brand_dna: dna,
        things_i_like: thingsLike,
        things_i_dislike: thingsDislike,
        visual_elements_to_avoid: avoidElements,
        words_to_avoid: avoidWords,
        avoid_neon: avoidNeon,
        avoid_clutter: avoidClutter,
        ...sliders,
      });
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save brand identity");
    } finally {
      setSaving(false);
    }
  }

  async function finish() {
    if (brandId && pendingFile && !uploaded) {
      setSaving(true);
      try {
        const created = await uploadReferenceImage(brandId, {
          file: pendingFile,
          category: refCategory,
          title: pendingFile.name.replace(/\.[^/.]+$/, ""),
        });
        if (refPriority) {
          await updateReferenceImage(brandId, created.id, { is_priority: true });
        }
        setUploaded(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to upload reference image");
        setSaving(false);
        return;
      }
    }
    router.push("/dashboard");
  }

  function back() {
    setError(null);
    setStep((s) => Math.max(0, s - 1));
  }

  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col gap-8 bg-[#fffaf8] px-4 py-6 sm:px-6 sm:py-10">
      <header className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <Image src="/logo.png" alt="Maneja" width={34} height={34} className="rounded-lg" />
          <span className="bg-gradient-to-r from-[#E8798F] to-[#A855A0] bg-clip-text text-xl font-bold tracking-tight text-transparent">
            Maneja
          </span>
        </div>
        <div className="flex w-full max-w-2xl flex-col gap-2">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Step {step + 1} of {STEPS.length}
            </span>
            <span>{STEPS[step]}</span>
          </div>
          <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </header>

      {error ? <p className="text-center text-sm text-destructive">{error}</p> : null}

      <main className="flex-1">
        {step === 0 ? (
          <section className="mx-auto flex max-w-xl flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h1 className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Tell us about your business
              </h1>
              <p className="text-base text-muted-foreground">
                We&apos;ll use this to set up your brand memory from day one.
              </p>
            </div>
            <div className="grid gap-2">
              <Label>Business name</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Sarah's Studio" />
            </div>
            <div className="grid gap-2">
              <Label>Industry</Label>
              <Select value={industry || undefined} onValueChange={setIndustry}>
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
              <Label>Website</Label>
              <Input value={website} onChange={(e) => setWebsite(e.target.value)} />
            </div>
            <div className="grid gap-2">
              <Label>Location</Label>
              <Input value={location} onChange={(e) => setLocation(e.target.value)} />
            </div>
          </section>
        ) : null}

        {step === 1 ? (
          <section className="mx-auto flex max-w-3xl flex-col gap-6">
            <div className="flex flex-col gap-2">
              <h1 className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Show us your brand identity
              </h1>
              <p className="text-base text-muted-foreground">
                The more Maneja knows, the more your content will feel like you.
              </p>
            </div>

            <div className="grid gap-2">
              <Label>Description</Label>
              <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label>Target customer</Label>
                <Input value={targetCustomer} onChange={(e) => setTargetCustomer(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Age range</Label>
                <Input value={ageRange} onChange={(e) => setAgeRange(e.target.value)} placeholder="25–44" />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>Audience interests</Label>
              <Input value={interests} onChange={(e) => setInterests(e.target.value)} />
            </div>

            <div className="grid gap-2">
              <Label>Brand colours</Label>
              <div className="flex flex-wrap items-center gap-2">
                {colors.map((c) => (
                  <div key={c.hex} className="flex items-center gap-2 rounded-lg border border-border px-2 py-2 text-sm">
                    <span className="size-5 rounded-full border border-border" style={{ background: c.hex }} />
                    {c.label}
                    <button type="button" aria-label={`Remove ${c.hex}`} onClick={() => removeColor(c.hex)}>
                      <X className="size-3.5" />
                    </button>
                  </div>
                ))}
                <input
                  type="color"
                  aria-label="Pick color"
                  value={colorInput.hex}
                  onChange={(e) => setColorInput((prev) => ({ ...prev, hex: e.target.value }))}
                  className="size-9 rounded border border-border"
                />
                <Input
                  className="h-9 w-32"
                  placeholder="Label"
                  value={colorInput.label}
                  onChange={(e) => setColorInput((prev) => ({ ...prev, label: e.target.value }))}
                />
                <Button type="button" size="sm" variant="outline" onClick={addColor}>
                  <Plus className="size-3.5" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label>Typography</Label>
                <Input value={typography} onChange={(e) => setTypography(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Photography style</Label>
                <Input value={photographyStyle} onChange={(e) => setPhotographyStyle(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Tone</Label>
                <Input value={tone} onChange={(e) => setTone(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Voice</Label>
                <Input value={voice} onChange={(e) => setVoice(e.target.value)} />
              </div>
            </div>

            <div className="grid gap-2">
              <Label>Brand DNA</Label>
              <div className="flex flex-wrap items-center gap-2">
                {dna.map((d) => (
                  <Badge key={d} variant="secondary" className="gap-1 rounded-full">
                    {d}
                    <button
                      type="button"
                      aria-label={`Remove ${d}`}
                      onClick={() => setDna((prev) => prev.filter((x) => x !== d))}
                    >
                      <X className="size-3" />
                    </button>
                  </Badge>
                ))}
                <Input
                  className="h-8 w-40 rounded-full"
                  placeholder="e.g. Warm"
                  value={dnaInput}
                  onChange={(e) => setDnaInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addDna())}
                />
                <Button type="button" size="sm" variant="outline" onClick={addDna}>
                  <Plus className="size-3.5" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label>Things I like</Label>
                <Input value={thingsLike} onChange={(e) => setThingsLike(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Things I don&apos;t like</Label>
                <Input value={thingsDislike} onChange={(e) => setThingsDislike(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Visual elements to avoid</Label>
                <Input value={avoidElements} onChange={(e) => setAvoidElements(e.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label>Words to avoid</Label>
                <Input value={avoidWords} onChange={(e) => setAvoidWords(e.target.value)} />
              </div>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-3">
              <label className="flex items-center gap-3 text-sm">
                <Checkbox checked={avoidNeon} onCheckedChange={(v) => setAvoidNeon(Boolean(v))} />
                Avoid neon
              </label>
              <label className="flex items-center gap-3 text-sm">
                <Checkbox checked={avoidClutter} onCheckedChange={(v) => setAvoidClutter(Boolean(v))} />
                Avoid clutter
              </label>
            </div>

            <div className="flex flex-col gap-5 rounded-xl border border-border p-6">
              <p className="text-sm font-medium text-foreground">AI behaviour</p>
              {SLIDER_FIELDS.map(({ key, label }) => (
                <div key={key} className="grid gap-2">
                  <Label>{label}</Label>
                  <input
                    aria-label={label}
                    type="range"
                    min={1}
                    max={3}
                    step={1}
                    value={sliders[key]}
                    onChange={(e) =>
                      setSliders((prev) => ({ ...prev, [key]: Number(e.target.value) }))
                    }
                    className="w-full accent-primary"
                  />
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {step === 2 ? (
          <section className="mx-auto flex max-w-3xl flex-col gap-8 lg:flex-row lg:gap-12">
            <div className="flex flex-1 flex-col gap-8">
              <div className="flex flex-col gap-2">
                <h1 className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                  Show us your brand
                </h1>
                <p className="text-base leading-7 text-muted-foreground">
                  A few visual references help Maneja create content that feels like you. This
                  step is optional — you can always add more later in Library.
                </p>
              </div>

              <div
                className="flex min-h-44 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-background text-center"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const file = e.dataTransfer.files?.[0];
                  if (file) setPendingFile(file);
                }}
              >
                {pendingFile ? (
                  <p className="px-4 text-sm font-medium text-foreground">{pendingFile.name}</p>
                ) : (
                  <>
                    <Upload className="size-6 text-muted-foreground" />
                    <div className="flex flex-col gap-1">
                      <p className="text-sm font-medium">Drop an image here</p>
                      <p className="text-xs text-muted-foreground">or</p>
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="rounded-lg"
                      onClick={() => inputRef.current?.click()}
                    >
                      Choose file
                    </Button>
                  </>
                )}
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(e) => setPendingFile(e.target.files?.[0] ?? null)}
                />
              </div>

              {pendingFile ? (
                <Card className="gap-4 rounded-xl border-border p-5">
                  <CardContent className="flex items-center gap-4 p-0">
                    <div className="flex size-20 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
                      <ImagePlus className="size-6 text-muted-foreground" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{pendingFile.name}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {(["brand", "products", "lifestyle", "people", "locations", "inspiration"] as ReferenceCategory[]).map(
                          (c) => (
                            <Button
                              key={c}
                              type="button"
                              size="sm"
                              variant={refCategory === c ? "default" : "outline"}
                              className="rounded-full"
                              onClick={() => setRefCategory(c)}
                            >
                              {c}
                            </Button>
                          ),
                        )}
                      </div>
                    </div>
                    <label className="flex items-center gap-3 text-sm text-muted-foreground">
                      Priority
                      <Checkbox checked={refPriority} onCheckedChange={(v) => setRefPriority(Boolean(v))} />
                    </label>
                  </CardContent>
                </Card>
              ) : null}
            </div>

            <aside className="w-full shrink-0 lg:w-72 lg:pt-16">
              <Card className="gap-6 rounded-2xl border-border p-6 shadow-[0px_2px_6px_rgba(27,36,55,0.08)]">
                <Image src="/logo.png" alt="Maneja" width={40} height={40} className="rounded-xl" />
                <p className="font-serif text-lg font-semibold text-foreground">
                  Maneja will use this to
                </p>
                <div className="flex flex-col gap-4">
                  {[
                    "Keep your visual style consistent",
                    "Prioritise the products you care about",
                    "Learn from what you approve",
                  ].map((t) => (
                    <div key={t} className="flex items-start gap-3">
                      <Check className="mt-0.5 size-4 shrink-0 text-primary" />
                      <span className="text-sm leading-6">{t}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </aside>
          </section>
        ) : null}
      </main>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-6">
        <Button variant="ghost" onClick={back} disabled={step === 0 || saving} className="gap-2">
          <ArrowLeft className="size-4" />
          Back
        </Button>
        {step === 0 ? (
          <Button onClick={goToStep2} disabled={saving} className="gap-2">
            {saving ? "Creating…" : "Continue"}
            <ArrowRight className="size-4" />
          </Button>
        ) : step === 1 ? (
          <Button onClick={goToStep3} disabled={saving} className="gap-2">
            {saving ? "Saving…" : "Continue"}
            <ArrowRight className="size-4" />
          </Button>
        ) : (
          <div className="flex gap-3">
            <Button variant="ghost" onClick={() => void finish()} disabled={saving}>
              Skip for now
            </Button>
            <Button onClick={() => void finish()} disabled={saving} className="gap-2">
              {saving ? "Finishing…" : "Go to dashboard"}
              <ArrowRight className="size-4" />
            </Button>
          </div>
        )}
      </footer>
    </div>
  );
}
