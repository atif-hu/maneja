"use client";

import { useQuery } from "@tanstack/react-query";
import { useBrandContext } from "@/lib/brand-context";
import { listImages } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const CONCEPT_LABEL: Record<string, string> = {
  product: "Product",
  lifestyle: "Lifestyle",
  engagement: "Engagement",
};

export default function ContentPage() {
  const { brand } = useBrandContext();
  const query = useQuery({
    queryKey: ["images", brand?.id, "approved"],
    queryFn: () => listImages(brand!.id, "approved"),
    enabled: !!brand,
  });
  const images = query.data ?? [];
  const error = query.error
    ? query.error instanceof Error
      ? query.error.message
      : "Failed to load approved content"
    : null;

  if (!brand) {
    return <p className="text-sm text-muted-foreground">Loading your business…</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">
          Approved content
        </h1>
        <p className="text-sm text-muted-foreground">
          Everything approved for {brand.name}, ready to publish or schedule.
        </p>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      {images.length === 0 ? (
        <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted-foreground">
          No approved content yet — approve today&apos;s concepts from the Dashboard.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4 xl:grid-cols-4">
          {images.map((img) => {
            const concept = img.concept_type ?? img.content_idea?.concept_type ?? null;
            return (
              <Card key={img.id} className="gap-0 overflow-hidden rounded-xl border-border py-0">
                <div className="relative aspect-square bg-muted">
                  {img.signed_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={img.signed_url} alt="" className="size-full object-cover" />
                  ) : null}
                </div>
                <CardContent className="flex flex-col gap-2 p-4">
                  {concept ? (
                    <Badge variant="secondary" className="w-fit">
                      {CONCEPT_LABEL[concept] ?? concept}
                    </Badge>
                  ) : null}
                  <p className="text-sm text-muted-foreground">
                    {img.content_idea?.headline ?? img.prompt}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
