import { Navbar } from "@/components/home/sections/navbar";
import SiteBackdrop from "@/components/ui/backgrounds/SiteBackdrop";

export default function HomeLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    // Force dark theme styling for homepage so it looks great in both app themes
    <div className="dark">
      <div className="relative min-h-dvh isolate overflow-hidden bg-background text-foreground">
        {/* Global hero-style backdrop for the entire page */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <SiteBackdrop />
        </div>

        {/* Optional vertical rails (subtle, hide on small screens) */}
        <div className="hidden md:block w-px h-full border-l border-white/10 fixed top-0 left-6 z-10" />
        <div className="hidden md:block w-px h-full border-r border-white/10 fixed top-0 right-6 z-10" />

        {/* Foreground content */}
        <div className="relative z-10">
          <Navbar />
          {children}
        </div>
      </div>
    </div>
  );
}
