import { DisclaimerBanner } from "@/components/layout/disclaimer-banner";
import { Footer } from "@/components/layout/footer";
import { MobileSidebar } from "@/components/layout/mobile-sidebar";
import { Navbar } from "@/components/layout/navbar";
import { Sidebar } from "@/components/layout/sidebar";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <DisclaimerBanner />
      <div className="flex flex-1">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center border-b border-border px-4 py-2 lg:hidden">
            <MobileSidebar />
            <span className="text-sm text-muted-foreground">Menu</span>
          </div>
          <main className="flex-1">{children}</main>
        </div>
      </div>
      <Footer />
    </div>
  );
}
