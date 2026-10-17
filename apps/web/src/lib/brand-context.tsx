"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Brand, listBrands } from "@/lib/api";

export const LAST_BRAND_KEY = "maneja:last-brand-id";

type BrandContextValue = {
  brand: Brand | null;
  brands: Brand[];
  loading: boolean;
  error: string | null;
  setActiveBrand: (brandId: string) => void;
  refresh: () => Promise<void>;
};

const BrandContext = createContext<BrandContextValue | undefined>(undefined);

export function BrandProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [activeId, setActiveId] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["brands"],
    queryFn: listBrands,
    staleTime: 5 * 60_000,
  });
  const brands = useMemo(() => query.data ?? [], [query.data]);
  const loading = query.isLoading;
  const error = query.error
    ? query.error instanceof Error
      ? query.error.message
      : "Failed to load businesses"
    : null;

  useEffect(() => {
    if (!query.data) return;
    if (query.data.length === 0) {
      router.push("/onboarding");
      return;
    }
    const stored =
      typeof window !== "undefined" ? window.localStorage.getItem(LAST_BRAND_KEY) : null;
    const match = stored ? query.data.find((b) => b.id === stored) : undefined;
    setActiveId((current) => {
      if (current && query.data.some((b) => b.id === current)) return current;
      return (match ?? query.data[0]).id;
    });
  }, [query.data, router]);

  const load = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: ["brands"] });
  }, [queryClient]);

  const setActiveBrand = useCallback((brandId: string) => {
    setActiveId(brandId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LAST_BRAND_KEY, brandId);
    }
  }, []);

  const brand = useMemo(
    () => brands.find((b) => b.id === activeId) ?? null,
    [brands, activeId],
  );

  const value = useMemo(
    () => ({ brand, brands, loading, error, setActiveBrand, refresh: load }),
    [brand, brands, loading, error, setActiveBrand, load],
  );

  return <BrandContext.Provider value={value}>{children}</BrandContext.Provider>;
}

export function useBrandContext() {
  const ctx = useContext(BrandContext);
  if (!ctx) throw new Error("useBrandContext must be used within a BrandProvider");
  return ctx;
}
