"use client";

import React, { useMemo, useState } from "react";
import { SectionHeader } from "@/components/home/section-header";
import { siteConfig } from "@/lib/home";
import { cn } from "@/lib/utils";
import { motion } from "motion/react";
import { ArrowRight } from "lucide-react";

interface UseCase {
  id: string;
  title: string;
  description: string;
  category: string;
  featured: boolean;
  icon: React.ReactNode;
  image: string;
  url: string;
}

// ==============================
// Glass primitives (match Hero)
// ==============================
const baseGlass =
  "relative rounded-3xl border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden";

function GlassCard({
  className = "",
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn(baseGlass, className)}>
      {/* Gradient rim */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-3xl"
        style={{
          background:
            "linear-gradient(180deg, rgba(173,216,255,0.18), rgba(255,255,255,0.04) 30%, rgba(150,160,255,0.14) 85%, rgba(255,255,255,0.06))",
          WebkitMask: "linear-gradient(#000,#000) content-box, linear-gradient(#000,#000)",
          WebkitMaskComposite: "xor" as any,
          maskComposite: "exclude",
          padding: 1,
          borderRadius: 24,
        }}
      />
      {/* Specular streak */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-24"
        style={{
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.22), rgba(255,255,255,0.06) 45%, rgba(255,255,255,0) 100%)",
          filter: "blur(6px)",
          mixBlendMode: "screen",
        }}
      />
      {/* Fine noise */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          backgroundImage:
            "url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2260%22 height=%2260%22><filter id=%22n%22><feTurbulence type=%22fractalNoise%22 baseFrequency=%220.8%22 numOctaves=%224%22/><feColorMatrix type=%22saturate%22 values=%220%22/><feComponentTransfer><feFuncA type=%22table%22 tableValues=%220 0.03%22/></feComponentTransfer></filter><rect width=%22100%%22 height=%22100%%22 filter=%22url(%23n)%22 /></svg>')",
          backgroundSize: "100px 100px",
          mixBlendMode: "overlay",
        }}
      />
      {/* Corner screws */}
      <div className="pointer-events-none" aria-hidden>
        <div className="absolute left-3 top-3 h-1.5 w-1.5 rounded-full bg-white/30" />
        <div className="absolute right-3 top-3 h-1.5 w-1.5 rounded-full bg-white/30" />
        <div className="absolute left-3 bottom-3 h-1.5 w-1.5 rounded-full bg-white/30" />
        <div className="absolute right-3 bottom-3 h-1.5 w-1.5 rounded-full bg-white/30" />
      </div>
      {children}
    </div>
  );
}

// ==============================
// Small UI bits
// ==============================
function Chip({
  active,
  children,
  onClick,
}: {
  active?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative rounded-2xl px-3.5 py-1.5 text-sm transition",
        "border border-white/10 bg-white/5 hover:bg-white/10",
        active && "bg-white/15 ring-1 ring-white/20"
      )}
    >
      <span className="bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent">
        {children}
      </span>
      {active && (
        <span className="absolute inset-x-6 -bottom-px h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
      )}
    </button>
  );
}

function FeaturedHalo() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute -inset-6 rounded-[2rem] opacity-40 blur-2xl"
      style={{
        background:
          "radial-gradient(120% 80% at 50% -10%, rgba(120,160,255,0.25), rgba(120,160,255,0.1) 40%, rgba(255,255,255,0) 70%)",
      }}
    />
  );
}

// ==============================
// Main component
// ==============================
export function UseCasesSection() {
  // Featured list (limit 8)
  const featuredUseCases: UseCase[] = useMemo(
    () =>
      (siteConfig.useCases || [])
        .filter((u: UseCase) => u.featured)
        .slice(0, 8),
    []
  );

  // Build categories from featured + All
  const categories = useMemo(() => {
    const set = new Set<string>(["All"]);
    featuredUseCases.forEach((u) => set.add(u.category));
    return Array.from(set);
  }, [featuredUseCases]);

  const [selected, setSelected] = useState<string>("All");
  const filtered = useMemo(
    () =>
      selected === "All"
        ? featuredUseCases
        : featuredUseCases.filter((u) => u.category === selected),
    [featuredUseCases, selected]
  );

  return (
    <section
      id="use-cases"
      className="relative w-full flex flex-col items-center justify-center gap-10 pb-20"
    >
      {/* Subtle backdrop line under the section for separation */}
      <div className="pointer-events-none absolute inset-x-0 -top-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

      <SectionHeader>
        <h2 className="bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent text-3xl md:text-4xl font-semibold tracking-tight text-center text-balance">
          See Iris in action
        </h2>
        <p className="text-center text-balance font-medium text-white/70">
          Explore real-world examples of how Iris completes complex tasks autonomously
        </p>
      </SectionHeader>

      {/* Category chips */}
      {categories.length > 1 && (
        <div className="flex flex-wrap items-center justify-center gap-2 px-6">
          {categories.map((cat) => (
            <Chip
              key={cat}
              active={selected === cat}
              onClick={() => setSelected(cat)}
            >
              {cat}
            </Chip>
          ))}
        </div>
      )}

      {/* Grid */}
      <div className="relative w-full">
        <motion.div
          initial="hidden"
          animate="show"
          variants={{
            hidden: { opacity: 0, y: 8 },
            show: {
              opacity: 1,
              y: 0,
              transition: { staggerChildren: 0.06, duration: 0.35, ease: "easeOut" },
            },
          }}
          className="grid min-[650px]:grid-cols-2 min-[1000px]:grid-cols-3 min-[1320px]:grid-cols-4 gap-5 w-full max-w-6xl mx-auto px-6"
        >
          {filtered.map((useCase) => (
            <motion.div
              key={useCase.id}
              variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
              whileHover={{ y: -2 }}
              className="relative"
            >
              {useCase.featured && <FeaturedHalo />}

              <GlassCard className={cn(
                "group h-full transition-transform will-change-transform",
                "hover:translate-y-[-2px]"
              )}>
                {/* Header */}
                <div className="p-5 flex flex-col gap-3">
                  <div className="flex items-center gap-3">
                    <div className="rounded-full bg-white/8 ring-1 ring-white/15 p-2">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        className="text-white/80"
                      >
                        {useCase.icon}
                      </svg>
                    </div>
                    <h3 className="text-base md:text-lg font-medium line-clamp-1 bg-clip-text text-transparent bg-gradient-to-b from-white to-white/70">
                      {useCase.title}
                    </h3>
                  </div>

                  <p className="text-sm text-white/70 leading-relaxed line-clamp-3">
                    {useCase.description}
                  </p>
                </div>

                {/* Media */}
                <div className="mt-auto">
                  <div className="relative aspect-[16/9] w-full overflow-hidden">
                    {/* LQIP blur layer */}
                    <div className="absolute inset-0 bg-white/5 blur-xl opacity-60 transition-opacity duration-500 group-hover:opacity-40" />
                    <img
                      src={
                        useCase.image ||
                        `https://placehold.co/800x450/0b1220/9aa4b2?text=Iris+${encodeURIComponent(
                          useCase.title
                        )}`
                      }
                      alt={`Iris ${useCase.title}`}
                      loading="lazy"
                      className={cn(
                        "relative z-10 h-full w-full object-cover",
                        "scale-[1.01] transition-transform duration-500 group-hover:scale-[1.03]"
                      )}
                    />
                    {/* Gradient overlay + CTA */}
                    <a
                      href={useCase.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(
                        "absolute inset-0 z-20 flex items-end justify-between gap-3 p-4",
                        "bg-gradient-to-t from-black/55 via-black/10 to-transparent opacity-0",
                        "transition-opacity duration-300 group-hover:opacity-100"
                      )}
                    >
                      <span className="inline-flex items-center gap-2 text-sm text-white font-medium">
                        Watch replay
                        <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                      </span>
                      <span className="rounded-full border border-white/20 bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-white/80">
                        {useCase.category}
                      </span>
                    </a>
                  </div>

                  {/* Separator line */}
                  <div className="h-px w-full bg-gradient-to-r from-transparent via-white/15 to-transparent" />
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </motion.div>

        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <p className="text-white/60">No use cases available yet.</p>
          </div>
        )}
      </div>
    </section>
  );
}
