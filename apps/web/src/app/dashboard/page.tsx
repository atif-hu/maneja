"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Check, Sparkles, X } from "lucide-react";
import { useBrandContext } from "@/lib/brand-context";
import {
  approveImage,
  getBrandStats,
  listImages,
  rejectImage,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePreviewModal } from "@/components/ImagePreviewModal";

export default function DashboardPage() {
  const router = useRouter();
  const { brand, loading: brandLoading } = useBrandContext();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [previewId, setPreviewId] = useState<string | null>(null);

  const dateLabel = useMemo(
    () =>
      new Intl.DateTimeFormat("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
      }).format(new Date()),
    [],
  );

  const pendingQuery = useQuery({
    queryKey: ["images", brand?.id, "pending_review"],
    queryFn: () => listImages(brand!.id, "pending_review"),
    enabled: !!brand,
  });
  const statsQuery = useQuery({
    queryKey: ["stats", brand?.id],
    queryFn: () => getBrandStats(brand!.id),
    enabled: !!brand,
  });
  const images = pendingQuery.data ?? [];
  const stats = statsQuery.data ?? null;
  const loading = pendingQuery.isLoading || statsQuery.isLoading;
  const loadError = pendingQuery.error ?? statsQuery.error;

  useEffect(() => {
    if (!previewId) return;
    function onKey(e: KeyboardEvent) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      e.preventDefault();
      const step = e.key === "ArrowRight" ? 1 : -1;
      const current = images.findIndex((img) => img.id === previewId);
      for (let i = current + step; i >= 0 && i < images.length; i += step) {
        const candidate = images[i];
        if (candidate.signed_url && rejectingId !== candidate.id) {
          setPreviewId(candidate.id);
          return;
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [previewId, images, rejectingId]);
  const error =
    actionError ??
    (loadError
      ? loadError instanceof Error
        ? loadError.message
        : "Failed to load today's content"
      : null);

  const refresh = async () => {
    setActionError(null);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["images", brand?.id] }),
      queryClient.invalidateQueries({ queryKey: ["stats", brand?.id] }),
    ]);
  };

  async function act(id: string, kind: "approve" | "reject", withNote?: string) {
    setBusy(id);
    try {
      if (kind === "approve") await approveImage(id);
      else await rejectImage(id, withNote);
      setRejectingId(null);
      setNote("");
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(null);
    }
  }

  async function approveSelected() {
    const ids = Object.entries(selected)
      .filter(([, v]) => v)
      .map(([id]) => id);
    if (ids.length === 0) return;
    setBusy("bulk");
    try {
      await Promise.all(ids.map((id) => approveImage(id)));
      setSelected({});
      await refresh();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Bulk approve failed");
    } finally {
      setBusy(null);
    }
  }

  function toggle(id: string) {
    setSelected((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  const selectedCount = Object.values(selected).filter(Boolean).length;

  if (brandLoading) {
    return <p className="text-sm text-muted-foreground">Loading your business…</p>;
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-2">
        <p className="text-sm font-medium text-primary">{dateLabel}</p>
        <h3 className="font-serif text-lg font-semibold tracking-tight text-foreground sm:text-xl">
          Maneja has prepared today&apos;s content for {brand?.name ?? "your brand"}.
        </h3>
      </section>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <section className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="font-serif text-xl font-semibold text-foreground">Today&apos;s content</h3>
            {!loading && (
              <Badge variant="secondary" className="font-normal">
                {images.length} pending review
              </Badge>
            )}
          </div>
          {selectedCount > 0 ? (
            <Button variant="outline" size="sm" disabled={busy === "bulk"} onClick={approveSelected}>
              Approve selected ({selectedCount})
            </Button>
          ) : null}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Card
                key={i}
                className="gap-0 overflow-hidden rounded-xl border-border py-0 shadow-[0px_8px_20px_rgba(27,36,55,0.06)]"
              >
                <Skeleton className="h-56 w-full rounded-none" />
                <CardContent className="flex flex-col gap-3 p-4">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-5/6" />
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-9 flex-1" />
                    <Skeleton className="h-9 w-16" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : images.length === 0 ? (
          <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted-foreground">
            Nothing pending review right now. Check back after the next run, or use Create to
            generate content on demand.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {images.map((img) => {
              const headline = img.content_idea?.headline ?? img.prompt;
              const rationale = img.content_idea?.rationale;
              const createdDate = new Date(img.created_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              });
              return (
                <Card
                  key={img.id}
                  className="gap-0 overflow-hidden rounded-xl border-border py-0 shadow-[0px_8px_20px_rgba(27,36,55,0.06)]"
                >
                  <div
                    className={`relative h-56 bg-muted ${img.signed_url ? "cursor-pointer" : ""}`}
                    onClick={() => img.signed_url && rejectingId !== img.id && setPreviewId(img.id)}
                  >
                    {img.signed_url ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={img.signed_url} alt={headline} className="size-full object-cover" />
                    ) : null}
                    <div
                      className="absolute left-4 top-4 flex size-5 items-center justify-center rounded-full bg-background/90"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Checkbox
                        className="rounded-full"
                        aria-label={`Select ${headline}`}
                        checked={Boolean(selected[img.id])}
                        onCheckedChange={() => toggle(img.id)}
                      />
                    </div>
                  </div>
                  <CardContent className="flex flex-1 flex-col gap-3 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex flex-col gap-1">
                        <h4 className="font-serif font-semibold text-foreground">{headline}</h4>
                      </div>
                    </div>
                    {rationale ? (
                      <div className="flex flex-col gap-1">
                        <p className={`text-sm text-muted-foreground ${expanded[img.id] ? "" : "line-clamp-2"}`}>
                          {rationale}
                        </p>
                        <button
                          type="button"
                          className="w-fit cursor-pointer text-sm font-bold text-foreground underline underline-offset-2"
                          onClick={() => setExpanded((prev) => ({ ...prev, [img.id]: !prev[img.id] }))}
                        >
                          {expanded[img.id] ? "Read less" : "Read more"}
                        </button>
                      </div>
                    ) : null}
                    <p className="text-xs text-muted-foreground">Generated {createdDate}</p>

                    {rejectingId === img.id ? (
                      <div className="flex flex-col gap-2">
                        <Textarea
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          placeholder="What should change next time? This feeds future generation."
                          rows={3}
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="destructive"
                            disabled={busy === img.id}
                            onClick={() => void act(img.id, "reject", note)}
                          >
                            Confirm reject
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setRejectingId(null);
                              setNote("");
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-auto flex flex-col gap-2">
                        {img.signed_url && (
                          <ImagePreviewModal
                            imageUrl={img.signed_url}
                            title={headline}
                            date={createdDate}
                            open={previewId === img.id}
                            onOpenChange={(next) => setPreviewId(next ? img.id : null)}
                          />
                        )}
                        <div className="flex items-center gap-2">
                          <Button
                            size="sm"
                            className="flex-1 gap-1"
                            disabled={busy === img.id}
                            onClick={() => void act(img.id, "approve")}
                          >
                            <Check className="size-4" />
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy === img.id}
                            onClick={() => setRejectingId(img.id)}
                          >
                            <X className="size-4" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </section>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: "Pending review", value: stats?.pending_review },
          { label: "Approved this week", value: stats?.approved_this_week, onClick: () => router.push("/dashboard/content") },
          { label: "Rejected this week", value: stats?.rejected_this_week },
          { label: "Reference images", value: stats?.total_reference_images, onClick: () => router.push("/dashboard/library") },
        ].map((stat, i) => (
          <Card
            key={i}
            className={`rounded-xl border-border p-4 shadow-none ${stat.onClick ? "cursor-pointer hover:bg-secondary/40 transition-colors" : ""}`}
            onClick={stat.onClick}
          >
            <CardContent className="flex flex-col gap-2 p-0">
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              {loading ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                <p className="font-serif text-2xl font-semibold text-foreground">
                  {stat.value ?? "—"}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </section>

      <div className="flex items-start gap-3 rounded-xl border border-border bg-secondary/40 p-4 sm:p-6">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
          <Sparkles className="size-5" />
        </div>
        <p className="text-sm leading-6 text-foreground">
          Approve with no note when a concept is on target, or reject with a note when it
          isn&apos;t — Maneja uses that feedback to steer tomorrow&apos;s concepts.
        </p>
      </div>
    </div>
  );
}
