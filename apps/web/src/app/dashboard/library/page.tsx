"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, HeartPulse, ImagePlus, Star, Trash2, Upload } from "lucide-react";
import { useBrandContext } from "@/lib/brand-context";
import {
  deleteReferenceImage,
  listReferenceImages,
  ReferenceCategory,
  ReferenceImage,
  updateReferenceImage,
  uploadReferenceImage,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ImagePreviewModal } from "@/components/ImagePreviewModal";

const CATEGORIES: { value: ReferenceCategory | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "products", label: "Products" },
  { value: "brand", label: "Brand" },
  { value: "lifestyle", label: "Lifestyle" },
  { value: "people", label: "People" },
  { value: "locations", label: "Locations" },
  { value: "inspiration", label: "Inspiration" },
];

export default function LibraryPage() {
  const { brand } = useBrandContext();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<ReferenceCategory | "all">("all");
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const query = useQuery({
    queryKey: ["reference-images", brand?.id, filter],
    queryFn: () => listReferenceImages(brand!.id, filter),
    enabled: !!brand,
  });
  const images = query.data ?? [];
  const loading = query.isLoading;
  const error =
    actionError ??
    (query.error
      ? query.error instanceof Error
        ? query.error.message
        : "Failed to load library"
      : null);

  const setImages = (updater: (prev: ReferenceImage[]) => ReferenceImage[]) =>
    queryClient.setQueryData<ReferenceImage[]>(
      ["reference-images", brand?.id, filter],
      (prev) => updater(prev ?? []),
    );

  const refresh = async () => {
    setActionError(null);
    await queryClient.invalidateQueries({ queryKey: ["reference-images", brand?.id] });
    await queryClient.invalidateQueries({ queryKey: ["stats", brand?.id] });
  };

  async function handleFiles(files: FileList | null) {
    if (!brand || !files || files.length === 0) return;
    setUploading(true);
    try {
      for (const file of Array.from(files)) {
        await uploadReferenceImage(brand.id, {
          file,
          category: filter === "all" ? "brand" : filter,
          title: file.name.replace(/\.[^/.]+$/, ""),
        });
      }
      await refresh();
      setActionError(null);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragOver(false);
    void handleFiles(e.dataTransfer.files);
  }

  function onFileInput(e: ChangeEvent<HTMLInputElement>) {
    void handleFiles(e.target.files);
    e.target.value = "";
  }

  async function togglePriority(img: ReferenceImage) {
    if (!brand) return;
    setImages((prev) =>
      prev.map((i) => (i.id === img.id ? { ...i, is_priority: !i.is_priority } : i)),
    );
    try {
      await updateReferenceImage(brand.id, img.id, { is_priority: !img.is_priority });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to update priority");
      void refresh();
    }
  }

  async function remove(img: ReferenceImage) {
    if (!brand) return;
    setImages((prev) => prev.filter((i) => i.id !== img.id));
    try {
      await deleteReferenceImage(brand.id, img.id);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Failed to delete image");
      void refresh();
    }
  }

  const addedThisWeek = images.filter((img) => {
    const uploaded = new Date(img.uploaded_at).getTime();
    return Date.now() - uploaded < 7 * 24 * 60 * 60 * 1000;
  }).length;

  if (!brand) {
    return <p className="text-sm text-muted-foreground">Loading your business…</p>;
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">
            Brand Library
          </h1>
          <p className="text-sm text-muted-foreground">
            Your visual references help Maneja create content that feels like {brand.name}.
          </p>
        </div>
        <Button className="gap-2" disabled={uploading} onClick={() => inputRef.current?.click()}>
          <Upload className="size-4" />
          {uploading ? "Uploading…" : "Upload images"}
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          className="hidden"
          onChange={onFileInput}
        />
      </header>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <div className="flex flex-col gap-8 lg:flex-row">
        <section className="min-w-0 flex-1">
          <div className="flex flex-col gap-6">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={onDrop}
              className={`flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-6 text-center transition-colors sm:p-10 ${
                dragOver ? "border-primary bg-secondary/40" : "border-border bg-[#fffaf8]"
              }`}
            >
              <div className="flex size-12 items-center justify-center rounded-full border border-border bg-background">
                <ImagePlus className="size-6 text-muted-foreground" />
              </div>
              <h2 className="font-serif text-xl font-semibold text-foreground">Drop images here</h2>
              <p className="text-sm text-muted-foreground">
                or{" "}
                <button
                  type="button"
                  className="font-medium text-primary underline underline-offset-4"
                  onClick={() => inputRef.current?.click()}
                >
                  Choose files
                </button>
              </p>
              <p className="text-xs text-muted-foreground">JPG, PNG or WEBP · up to 20MB</p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {CATEGORIES.map((c) => (
                <Button
                  key={c.value}
                  size="sm"
                  variant={filter === c.value ? "default" : "outline"}
                  className="rounded-full"
                  onClick={() => setFilter(c.value)}
                >
                  {c.label}
                </Button>
              ))}
            </div>

            {loading ? (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4 xl:grid-cols-4">
                {[...Array(8)].map((_, i) => (
                  <Card key={i} className="gap-0 overflow-hidden rounded-xl border-border py-0">
                    <Skeleton className="aspect-square w-full rounded-none" />
                    <CardContent className="flex flex-col gap-2 p-4">
                      <Skeleton className="h-6 w-20" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-3/4" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : images.length === 0 ? (
              <div className="flex min-h-40 items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted-foreground">
                No reference images in this category yet.
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-3 md:grid-cols-3 md:gap-4 xl:grid-cols-4">
                {images.map((img) => {
                  const uploadedDate = new Date(img.uploaded_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  });
                  return (
                    <Card key={img.id} className="gap-0 overflow-hidden rounded-xl border-border py-0">
                      <div className="relative aspect-square bg-muted">
                        {img.signed_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={img.signed_url}
                            alt={img.title ?? "Reference image"}
                            className="size-full object-cover"
                          />
                        ) : null}
                        <button
                          type="button"
                          aria-label={img.is_priority ? "Unmark priority" : "Mark priority"}
                          onClick={() => void togglePriority(img)}
                          className="absolute right-2 top-2 rounded-full bg-background/90 p-2"
                        >
                          <Star
                            className={`size-4 ${img.is_priority ? "fill-primary text-primary" : "text-muted-foreground"}`}
                          />
                        </button>
                        <button
                          type="button"
                          aria-label="Delete image"
                          onClick={() => void remove(img)}
                          className="absolute left-2 top-2 rounded-full bg-background/90 p-2"
                        >
                          <Trash2 className="size-4 text-destructive" />
                        </button>
                      </div>
                      <CardContent className="flex flex-col gap-2 p-4">
                        <div className="flex items-center justify-between">
                          <Badge variant="secondary">{img.category}</Badge>
                          <span className="text-xs text-muted-foreground">
                            Used {img.usage_count} times
                          </span>
                        </div>
                        <p className="font-medium text-foreground">{img.title ?? "Untitled"}</p>
                        <p className="text-xs text-muted-foreground">
                          Uploaded {uploadedDate}
                        </p>
                        {img.signed_url && (
                          <ImagePreviewModal
                            imageUrl={img.signed_url}
                            title={img.title || "Reference image"}
                            date={uploadedDate}
                          />
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </section>

        <aside className="w-full lg:w-72 lg:shrink-0">
          <Card className="gap-6 rounded-xl border-border p-6">
            <CardHeader className="gap-2 p-0">
              <div className="flex items-center justify-between">
                <CardTitle className="font-serif text-lg">Library health</CardTitle>
                <HeartPulse className="size-5 text-primary" />
              </div>
              <CardDescription>A quick view of your reference coverage.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-5 p-0">
              <div className="flex items-end justify-between border-b border-border pb-4">
                <span className="text-sm text-muted-foreground">Images</span>
                <span className="font-serif text-2xl font-semibold text-foreground">
                  {images.length}
                </span>
              </div>
              <div className="flex items-end justify-between border-b border-border pb-4">
                <span className="text-sm text-muted-foreground">Added this week</span>
                <span className="font-serif text-2xl font-semibold text-foreground">
                  {addedThisWeek}
                </span>
              </div>
              <div className="flex gap-3 rounded-lg bg-[#fff3f3] p-4">
                <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-primary" />
                <p className="text-sm leading-5 text-foreground">
                  {images.length > 0
                    ? "Keep uploading across categories to widen Maneja's reference pool."
                    : "Upload your first reference image to start building brand memory."}
                </p>
              </div>
            </CardContent>
          </Card>
        </aside>
      </div>
    </div>
  );
}
