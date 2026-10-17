"use client";

import { useEffect, useState } from "react";
import { useBrandContext } from "@/lib/brand-context";
import { updateBrand } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const { brand, refresh } = useBrandContext();
  const [name, setName] = useState("");
  const [timezone, setTimezone] = useState("");
  const [dailyRunAt, setDailyRunAt] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    if (!brand) return;
    setName(brand.name);
    setTimezone(brand.timezone);
    setDailyRunAt(brand.daily_run_at.slice(0, 5));
  }, [brand]);

  async function save() {
    if (!brand) return;
    setSaving(true);
    try {
      await updateBrand(brand.id, { name, timezone, daily_run_at: dailyRunAt });
      await refresh();
      setSavedAt(Date.now());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  }

  if (!brand) {
    return <p className="text-sm text-muted-foreground">Loading your business…</p>;
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight text-foreground">
          Business settings
        </h1>
        <p className="text-sm text-muted-foreground">
          Core scheduling details for {brand.name}. Brand identity lives in Brand Brain.
        </p>
      </div>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <Card className="gap-6 rounded-xl border-border p-6">
        <CardHeader className="gap-1 p-0">
          <CardTitle className="font-serif">Schedule</CardTitle>
          <CardDescription>When Maneja generates daily concepts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 p-0">
          <div className="grid gap-2">
            <Label>Business name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Timezone</Label>
            <Input value={timezone} onChange={(e) => setTimezone(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Daily run time</Label>
            <Input
              type="time"
              value={dailyRunAt}
              onChange={(e) => setDailyRunAt(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Status</span>
            <Badge variant="secondary">{brand.status}</Badge>
          </div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-end gap-3">
        {savedAt ? <span className="text-sm text-muted-foreground">Saved</span> : null}
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </div>
  );
}
