"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { motion } from "motion/react";
import { siteConfig } from "@/lib/home";
import { ArrowRight } from "lucide-react";

// ==============================
// Glass primitives (same recipe)
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
    <div className={`${baseGlass} ${className}`}>
      {/* Gradient rim */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-3xl"
        style={{
          background:
            "linear-gradient(180deg, rgba(173,216,255,0.18), rgba(255,255,255,0.04) 30%, rgba(150,160,255,0.14) 85%, rgba(255,255,255,0.06))",
          WebkitMask:
            "linear-gradient(#000,#000) content-box, linear-gradient(#000,#000)",
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

function Beam() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 -top-1 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent"
    />
  );
}

export function CTASection() {
  const { ctaSection } = siteConfig;

  return (
    <section id="cta" className="relative flex flex-col items-center justify-center w-full pt-12 pb-16">
      {/* Thin beam separator to echo sections */}
      <Beam />

      {/* Ambient halos */}
      <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-[8%] top-[20%] h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="absolute right-[10%] top-[10%] h-56 w-56 rounded-full bg-indigo-400/10 blur-[72px]" />
      </div>

      <div className="w-full max-w-6xl mx-auto px-6">
        <GlassCard className="relative h-[420px] md:h-[420px] w-full">
          {/* Parallax background image (optional from siteConfig) */}
          {ctaSection?.backgroundImage && (
            <div className="absolute inset-0">
              <motion.div
                className="absolute inset-0"
                initial={{ scale: 1.06, opacity: 0.0 }}
                animate={{ scale: 1.02, opacity: 0.25 }}
                transition={{ duration: 0.8, ease: [0.2, 0, 0.2, 1] }}
              >
                <Image
                  src={ctaSection.backgroundImage}
                  alt="Iris CTA background"
                  className="object-cover object-center"
                  fill
                  priority
                />
              </motion.div>
              <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-black/10 to-transparent" />
            </div>
          )}

          {/* Grid lines (hero style) */}
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div
              className="absolute inset-0 opacity-30"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(255,255,255,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.07) 1px, transparent 1px)",
                backgroundSize: "64px 64px, 64px 64px",
                backgroundPosition: "center",
              }}
            />
            <div
              className="absolute inset-0 opacity-[0.08]"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px)",
                backgroundSize: "8px 8px, 8px 8px",
                backgroundPosition: "center",
              }}
            />
          </div>

          {/* Content */}
          <div className="absolute inset-0 flex flex-col items-center justify-center px-6">
            <motion.h1
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-20% 0% -20% 0%" }}
              transition={{ duration: 0.5 }}
              className="text-center max-w-[18rem] md:max-w-3xl bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent text-4xl md:text-6xl font-semibold tracking-tight"
            >
              {ctaSection.title}
            </motion.h1>

            <div className="absolute bottom-8 flex flex-col items-center justify-center gap-2">
              <Link href={ctaSection.button.href} className="group relative inline-flex">
                {/* button body */}
                <motion.span
                  whileHover={{ y: -1 }}
                  className="relative z-10 bg-white text-black font-semibold text-sm h-10 px-5 rounded-full inline-flex items-center gap-2 shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)]"
                >
                  {ctaSection.button.text}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </motion.span>
                {/* glow ring */}
                <span className="absolute inset-0 rounded-full bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                {/* shine sweep */}
                <span className="pointer-events-none absolute -inset-[1px] rounded-full overflow-hidden">
                  <span className="absolute -left-1/3 top-0 h-full w-1/3 rotate-12 bg-gradient-to-r from-transparent via-white/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </span>
              </Link>

              {ctaSection.subtext && (
                <span className="text-white/80 text-sm text-center">{ctaSection.subtext}</span>
              )}
            </div>
          </div>
        </GlassCard>
      </div>
    </section>
  );
}
