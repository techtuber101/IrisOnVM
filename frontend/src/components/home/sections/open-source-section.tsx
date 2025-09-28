"use client";

import React from "react";
import { SectionHeader } from "@/components/home/section-header";
import { motion } from "motion/react";
import { Eye, Brain, Rocket, LineChart, ArrowRight } from "lucide-react";

// ==============================
// Glass primitives
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
      {/* Rim */}
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
      {/* Streak */}
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
      {children}
    </div>
  );
}

// ==============================
// Section
// ==============================
export function OpenSourceSection() {
  return (
    <section
      id="vision"
      className="relative flex flex-col items-center justify-center w-full pb-24"
    >
      <div className="w-full max-w-6xl mx-auto px-6">
        <SectionHeader>
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-center bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent">
            Iris’s Vision
          </h2>
          <p className="text-center text-white/70 font-medium text-balance">
            Iris turns bold ideas into living systems — executing vision into reality through
            perception, intelligence, and action. From observing the world to delivering measurable
            outcomes, Iris is the bridge between imagination and execution.
          </p>
        </SectionHeader>

        {/* Vision pipeline */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-4 gap-6">
          <motion.div
            whileHover={{ y: -3 }}
            className="relative flex flex-col items-center text-center"
          >
            <GlassCard className="p-6 flex flex-col items-center gap-3">
              <Eye className="h-8 w-8 text-cyan-300" />
              <h3 className="font-medium">Vision</h3>
              <p className="text-sm text-white/70">
                Perceive the world with clarity. Capture signals, patterns, and opportunities.
              </p>
            </GlassCard>
            <ArrowRight className="hidden md:block absolute -right-5 top-1/2 text-white/40" />
          </motion.div>

          <motion.div
            whileHover={{ y: -3 }}
            className="relative flex flex-col items-center text-center"
          >
            <GlassCard className="p-6 flex flex-col items-center gap-3">
              <Brain className="h-8 w-8 text-indigo-300" />
              <h3 className="font-medium">Plan</h3>
              <p className="text-sm text-white/70">
                Convert insights into strategies. Model scenarios and chart paths forward.
              </p>
            </GlassCard>
            <ArrowRight className="hidden md:block absolute -right-5 top-1/2 text-white/40" />
          </motion.div>

          <motion.div
            whileHover={{ y: -3 }}
            className="relative flex flex-col items-center text-center"
          >
            <GlassCard className="p-6 flex flex-col items-center gap-3">
              <Rocket className="h-8 w-8 text-purple-300" />
              <h3 className="font-medium">Execute</h3>
              <p className="text-sm text-white/70">
                Deploy autonomous agents that act with precision, speed, and adaptability.
              </p>
            </GlassCard>
            <ArrowRight className="hidden md:block absolute -right-5 top-1/2 text-white/40" />
          </motion.div>

          <motion.div
            whileHover={{ y: -3 }}
            className="relative flex flex-col items-center text-center"
          >
            <GlassCard className="p-6 flex flex-col items-center gap-3">
              <LineChart className="h-8 w-8 text-green-300" />
              <h3 className="font-medium">Reality</h3>
              <p className="text-sm text-white/70">
                Deliver outcomes that matter — measurable impact, continuous learning, and trust.
              </p>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
