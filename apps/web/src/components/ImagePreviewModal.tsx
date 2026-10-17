"use client";

import { useState } from "react";
import { Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";

interface ImagePreviewModalProps {
  imageUrl: string;
  title?: string;
  date?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function ImagePreviewModal({
  imageUrl,
  title,
  date,
  open: openProp,
  onOpenChange,
}: ImagePreviewModalProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = openProp ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;

  return (
    <>
      <Button
        size="sm"
        variant="outline"
        className="gap-1"
        onClick={() => setOpen(true)}
      >
        <Eye className="size-4" />
        Preview
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-h-[calc(100vh-4rem)] max-w-lg overflow-y-auto">
          <DialogTitle>{title || "Image preview"}</DialogTitle>
          {date && <DialogDescription>{date}</DialogDescription>}
          <div className="flex flex-col gap-4">
            <img
              src={imageUrl}
              alt={title || "Preview"}
              className="max-h-[calc(100vh-12rem)] w-full rounded-lg object-contain"
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
