"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, ChevronRight, Info, WandSparkles } from "lucide-react";
import { useBrandContext } from "@/lib/brand-context";
import {
  generateNow,
  listProducts,
  listReferenceImages,
  Product,
  ReferenceImage,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const CONTENT_TYPES = ["Product", "Promotion", "Lifestyle", "Educational", "Engagement", "Announcement"];
const PLATFORMS = ["Instagram post", "Instagram story", "Facebook post", "Facebook story"];

const INERT_ROWS = ["Content objective", "Visual style", "Mood", "Text overlay", "CTA"];

export default function CreatePage() {
  const { brand } = useBrandContext();
  const [promotion, setPromotion] = useState("");
  const [contentType, setContentType] = useState<string | null>(null);
  const [platform, setPlatform] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "submitting" | "queued" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const productsQuery = useQuery({
    queryKey: ["products", brand?.id],
    queryFn: () => listProducts(brand!.id),
    enabled: !!brand,
  });
  const referencesQuery = useQuery({
    queryKey: ["reference-images", brand?.id, "all"],
    queryFn: () => listReferenceImages(brand!.id, "all"),
    enabled: !!brand,
  });
  const products: Product[] = productsQuery.data ?? [];
  const references: ReferenceImage[] = referencesQuery.data ?? [];
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [selectedReference, setSelectedReference] = useState<string | null>(null);

  async function onGenerate() {
    if (!brand || !promotion.trim()) return;
    setStatus("submitting");
    setErrorMessage(null);
    try {
      await generateNow(brand.id, {
        promotion: promotion.trim(),
        content_type: contentType ?? undefined,
        platform: platform ?? undefined,
      });
      setStatus("queued");
    } catch (err) {
      setStatus("error");
      setErrorMessage(err instanceof Error ? err.message : "Failed to queue generation");
    }
  }

  if (!brand) {
    return <p className="text-sm text-muted-foreground">Loading your business…</p>;
  }

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h2 className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
          What would you like to share?
        </h2>
        <p className="text-base text-muted-foreground">
          Give Maneja a direction and it will turn it into polished content for {brand.name}.
        </p>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.85fr)] lg:gap-8">
        <Card className="gap-6 rounded-2xl border-border p-5 shadow-[0px_8px_24px_rgba(27,36,55,0.08)] sm:p-8">
          <CardHeader className="gap-2 p-0">
            <div className="flex items-center gap-2">
              <div className="flex size-8 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <WandSparkles className="size-4" />
              </div>
              <CardTitle className="font-serif text-xl">Quick create</CardTitle>
            </div>
            <CardDescription>
              Start with a simple direction for your next piece of content.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6 p-0">
            <div className="flex flex-col gap-2">
              <Label htmlFor="promotion">What do you want to promote?</Label>
              <Input
                id="promotion"
                placeholder="e.g. our new autumn collection"
                value={promotion}
                onChange={(e) => setPromotion(e.target.value)}
                className="h-11 rounded-lg"
              />
            </div>
            <div className="flex flex-col gap-3">
              <Label>Content type</Label>
              <div className="flex flex-wrap gap-2">
                {CONTENT_TYPES.map((type) => (
                  <Button
                    key={type}
                    type="button"
                    size="sm"
                    variant={contentType === type ? "default" : "outline"}
                    className="rounded-full"
                    onClick={() => setContentType(contentType === type ? null : type)}
                  >
                    {type}
                  </Button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-3">
              <Label>Platform</Label>
              <div className="flex flex-wrap gap-2">
                {PLATFORMS.map((p) => (
                  <Button
                    key={p}
                    type="button"
                    size="sm"
                    variant={platform === p ? "default" : "outline"}
                    className="rounded-full"
                    onClick={() => setPlatform(platform === p ? null : p)}
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col items-start gap-3 p-0 pt-2">
            <Button
              className="h-11 gap-2 rounded-lg px-6"
              disabled={!promotion.trim() || status === "submitting"}
              onClick={onGenerate}
            >
              {status === "submitting" ? "Generating…" : "Generate content"}
              <ArrowRight className="size-4" />
            </Button>
            {status === "queued" ? (
              <p className="text-sm text-primary">
                Queued. New content will appear on your Dashboard once it&apos;s ready.
              </p>
            ) : null}
            {status === "error" ? (
              <p className="text-sm text-destructive">{errorMessage}</p>
            ) : null}
          </CardFooter>
        </Card>

        <Card className="gap-0 overflow-hidden rounded-2xl border-border shadow-[0px_8px_24px_rgba(27,36,55,0.08)]">
          <Accordion type="single" collapsible>
            <AccordionItem value="advanced" className="border-none">
              <AccordionTrigger className="px-5 py-5 hover:no-underline sm:px-6 sm:py-6">
                <div className="flex items-center gap-3">
                  <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <WandSparkles className="size-4" />
                  </div>
                  <div className="flex flex-col gap-1 text-left">
                    <span className="text-base font-semibold text-foreground">Advanced create</span>
                    <span className="text-sm text-muted-foreground">Fine-tune the direction</span>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-5 sm:px-6">
                <div className="flex flex-col">
                  <div className="flex flex-col gap-2 border-t border-border py-4">
                    <span className="text-sm font-medium text-foreground">Product or service</span>
                    <div className="flex flex-wrap gap-2">
                      {products.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          No products yet — add some in Brand Brain.
                        </p>
                      ) : (
                        products.map((p) => (
                          <Button
                            key={p.id}
                            type="button"
                            size="sm"
                            variant={selectedProduct === p.id ? "default" : "outline"}
                            className="rounded-full"
                            onClick={() =>
                              setSelectedProduct(selectedProduct === p.id ? null : p.id)
                            }
                          >
                            {p.name}
                          </Button>
                        ))
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col gap-2 border-t border-border py-4">
                    <span className="text-sm font-medium text-foreground">Reference images</span>
                    <div className="flex flex-wrap gap-2">
                      {references.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          No reference images yet — upload some in Library.
                        </p>
                      ) : (
                        references.slice(0, 8).map((r) => (
                          <Button
                            key={r.id}
                            type="button"
                            size="sm"
                            variant={selectedReference === r.id ? "default" : "outline"}
                            className="rounded-full"
                            onClick={() =>
                              setSelectedReference(selectedReference === r.id ? null : r.id)
                            }
                          >
                            {r.title ?? r.category}
                          </Button>
                        ))
                      )}
                    </div>
                  </div>
                  {INERT_ROWS.map((row) => (
                    <div
                      key={row}
                      className="flex items-center justify-between border-t border-border py-4 text-sm text-muted-foreground"
                    >
                      <span>{row}</span>
                      <ChevronRight className="size-4" />
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>
      </div>

      <div className="flex items-center gap-3 rounded-xl border border-border bg-[#FDF3F1] p-4 text-sm text-muted-foreground">
        <Info className="size-4 shrink-0 text-primary" />
        <span>Your brand preferences and approved content will guide the result.</span>
      </div>
    </div>
  );
}
