import { AppShell } from "@/components/maneja/AppShell";
import { BrandProvider } from "@/lib/brand-context";
import { QueryProvider } from "@/lib/query-provider";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryProvider>
      <BrandProvider>
        <AppShell>{children}</AppShell>
      </BrandProvider>
    </QueryProvider>
  );
}

