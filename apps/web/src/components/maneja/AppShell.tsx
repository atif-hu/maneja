"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  BriefcaseBusiness,
  CalendarDays,
  Check,
  ChartNoAxesCombined,
  CheckCheck,
  ChevronDown,
  CircleHelp,
  FileImage,
  Layers3,
  LayoutDashboard,
  Library,
  LogOut,
  Menu,
  Palette,
  Plus,
  Settings,
  WandSparkles,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useBrandContext } from "@/lib/brand-context";
import {
  createBrand,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  Notification,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/content", label: "Content", icon: FileImage },
  { href: "/dashboard/create", label: "Create", icon: WandSparkles },
  { href: "/dashboard/library", label: "Library", icon: Library },
  { href: "/dashboard/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/dashboard/campaigns", label: "Campaigns", icon: Layers3 },
  { href: "/dashboard/analytics", label: "Analytics", icon: ChartNoAxesCombined },
  { href: "/dashboard/brand", label: "Brand", icon: Palette },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
] as const;

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/dashboard/content": "Content",
  "/dashboard/create": "Create",
  "/dashboard/library": "Library",
  "/dashboard/calendar": "Calendar",
  "/dashboard/campaigns": "Campaigns",
  "/dashboard/analytics": "Analytics",
  "/dashboard/brand": "Brand",
  "/dashboard/settings": "Settings",
};

const STANDALONE_ROUTES = new Set(["/dashboard/mobile"]);

function initialsFromName(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

function AddBusinessDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { refresh, setActiveBrand } = useBrandContext();
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleOpenChange(next: boolean) {
    if (saving) return;
    if (!next) {
      setName("");
      setError(null);
    }
    onOpenChange(next);
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError("Business name is required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await createBrand({
        name: trimmed,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      await refresh();
      setActiveBrand(created.id);
      handleOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create business");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={onSubmit} className="flex flex-col gap-6">
          <DialogHeader>
            <DialogTitle>Add business</DialogTitle>
            <DialogDescription>
              Creates a separate business with its own brand memory, content and campaigns.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-2">
            <Label htmlFor="new-business-name">Business name</Label>
            <Input
              id="new-business-name"
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Sarah's Studio"
            />
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
          </div>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => handleOpenChange(false)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Creating…" : "Create and switch"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function BusinessSwitcher() {
  const { brand, brands, setActiveBrand, loading } = useBrandContext();
  const [addOpen, setAddOpen] = useState(false);
  const skipFocusReturn = useRef(false);

  if (loading) {
    return (
      <div className="flex h-9 items-center gap-3 rounded-lg px-3 text-sm text-muted-foreground">
        <BriefcaseBusiness className="size-4" />
        Loading businesses…
      </div>
    );
  }

  if (!brand) return null;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-muted-foreground"
          >
            <BriefcaseBusiness className="size-4 shrink-0" />
            <span className="flex-1 truncate text-left">{brand.name}</span>
            <ChevronDown className="size-4 shrink-0" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          className="w-56"
          onCloseAutoFocus={(e) => {
            if (skipFocusReturn.current) {
              e.preventDefault();
              skipFocusReturn.current = false;
            }
          }}
        >
          <DropdownMenuLabel>Switch business</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {brands.map((b) => (
            <DropdownMenuItem key={b.id} onSelect={() => setActiveBrand(b.id)}>
              <span className="flex-1 truncate">{b.name}</span>
              {b.id === brand.id ? <Check className="size-4" /> : null}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={() => {
              skipFocusReturn.current = true;
              setAddOpen(true);
            }}
          >
            <Plus className="size-4" />
            Add business
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <AddBusinessDialog open={addOpen} onOpenChange={setAddOpen} />
    </>
  );
}

function NotificationsBell() {
  const { brand } = useBrandContext();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const queryKey = ["notifications", brand?.id ?? null];

  const { data } = useQuery({
    queryKey,
    queryFn: async () => {
      const list = await listNotifications(true);
      return brand ? list.filter((n) => n.brand_id === brand.id) : list;
    },
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
  });
  const notifications: Notification[] = data ?? [];
  const setNotifications = (updater: (prev: Notification[]) => Notification[]) =>
    queryClient.setQueryData<Notification[]>(queryKey, (prev) => updater(prev ?? []));
  const refresh = () => queryClient.invalidateQueries({ queryKey });

  async function onRead(id: string) {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
    try {
      await markNotificationRead(id);
    } catch {
      void refresh();
    }
  }

  async function onReadAll() {
    setNotifications(() => []);
    try {
      await markAllNotificationsRead();
    } catch {
      void refresh();
    }
  }

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Notifications" className="relative">
          <Bell className="size-4" />
          {notifications.length > 0 ? (
            <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-primary" />
          ) : null}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[min(20rem,calc(100vw-2rem))]">
        <div className="flex items-center justify-between px-2 py-1.5">
          <DropdownMenuLabel className="p-0">Notifications</DropdownMenuLabel>
          {notifications.length > 0 ? (
            <button
              type="button"
              onClick={onReadAll}
              className="flex items-center gap-1 text-xs font-medium text-primary"
            >
              <CheckCheck className="size-3.5" />
              Mark all read
            </button>
          ) : null}
        </div>
        <DropdownMenuSeparator />
        {notifications.length === 0 ? (
          <p className="px-2 py-4 text-center text-sm text-muted-foreground">
            You&apos;re all caught up.
          </p>
        ) : (
          notifications.map((n) => (
            <DropdownMenuItem
              key={n.id}
              className="flex-col items-start gap-0.5 whitespace-normal"
              onSelect={() => onRead(n.id)}
            >
              <span className="text-sm font-medium">{n.title}</span>
              {n.body ? (
                <span className="text-xs text-muted-foreground">{n.body}</span>
              ) : null}
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const title = PAGE_TITLES[pathname] ?? "Dashboard";
  const [userName, setUserName] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState("");
  const [navOpen, setNavOpen] = useState(false);

  useEffect(() => {
    setNavOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!navOpen) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setNavOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [navOpen]);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      const user = data.session?.user;
      if (user) {
        const fullName =
          (user.user_metadata?.full_name as string | undefined)?.trim() ||
          user.email?.split("@")[0] ||
          "Account";
        setUserName(fullName);
        setUserEmail(user.email ?? "");
      }
    });
  }, []);

  if (STANDALONE_ROUTES.has(pathname)) {
    return <>{children}</>;
  }

  async function signOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  const displayName = userName ?? "Loading…";

  return (
    <div className="flex h-dvh w-full overflow-hidden bg-background text-foreground">
      <div className="mx-auto flex h-full w-full max-w-[1440px]">
        {navOpen ? (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-40 bg-charcoal/40 md:hidden"
            onClick={() => setNavOpen(false)}
          />
        ) : null}
        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-72 max-w-[85vw] flex-col gap-1 overflow-y-auto border-r border-border bg-sidebar p-6 shadow-xl transition-transform duration-200 md:static md:z-auto md:w-60 md:max-w-none md:shrink-0 md:translate-x-0 md:shadow-none ${
            navOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <Link href="/dashboard" className="flex items-center gap-2 border-b border-border pb-6">
            <Image src="/logo.png" alt="Maneja" width={34} height={34} className="rounded-lg" />
            <span className="bg-gradient-to-r from-[#E8798F] to-[#A855A0] bg-clip-text text-xl font-bold tracking-tight text-transparent">
  Maneja
</span>

          </Link>

          <nav className="flex flex-1 flex-col gap-1 pt-6" aria-label="Main navigation">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <Link key={href} href={href}>
                  <Button
                    variant={active ? "secondary" : "ghost"}
                    className={
                      active
                        ? "w-full justify-start gap-3 bg-sidebar-accent text-sidebar-accent-foreground"
                        : "w-full justify-start gap-3 text-muted-foreground"
                    }
                  >
                    <Icon className="size-4" />
                    {label}
                  </Button>
                </Link>
              );
            })}
          </nav>

          <div className="flex flex-col gap-1 border-t border-border pt-6">
            <BusinessSwitcher />
            <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground">
              <CircleHelp className="size-4" />
              Help
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground">
                  <Avatar className="size-6">
                    <AvatarFallback>{userName ? initialsFromName(userName) : "…"}</AvatarFallback>
                  </Avatar>
                  <span className="flex-1 truncate text-left">{displayName}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuLabel className="truncate">{displayName}</DropdownMenuLabel>
                {userEmail ? (
                  <p className="truncate px-2 pb-1.5 text-xs text-muted-foreground">{userEmail}</p>
                ) : null}
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onSelect={signOut}>
                  <LogOut className="size-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col bg-[#fffaf7]">
          <header className="flex h-16 shrink-0 items-center gap-3 border-b border-border bg-background px-4 md:h-20 md:px-8">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Open navigation"
              aria-expanded={navOpen}
              className="md:hidden"
              onClick={() => setNavOpen(true)}
            >
              <Menu className="size-5" />
            </Button>
            <h1 className="min-w-0 flex-1 truncate text-lg font-semibold text-foreground">{title}</h1>
            <div className="flex shrink-0 items-center gap-2">
              <NotificationsBell />
            </div>
          </header>
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">{children}</div>
        </div>
      </div>
    </div>
  );
}

export function EmptyPage({ message = "This page is coming soon." }: { message?: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
      {message}
    </div>
  );
}

export function ComingSoonCard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-background p-6 text-center sm:p-12">
      <h2 className="font-serif text-2xl font-semibold text-foreground">{title}</h2>
      <p className="max-w-md text-sm text-muted-foreground">{description}</p>
      <Badge variant="secondary" className="mt-2">
        Coming in a later phase
      </Badge>
    </div>
  );
}
