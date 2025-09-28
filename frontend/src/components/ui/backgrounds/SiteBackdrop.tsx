"use client";
import React from "react";

/**
 * Global backdrop used across the whole marketing site.
 * - Deep navy base comes from --background (#070b13) via globals.css
 * - Blue-tinted grid lines & cool stars
 * - Same top spotlight recipe as the Hero (so it blends perfectly)
 */

function TopSpotlight() {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 -top-[15vh] h-[80vh]"
    >
      <div
        className="mx-auto h-full w-[60%]"
        style={{
          // ⤵︎ Slightly brighter blue spotlight for more impact
          background:
            "radial-gradient(ellipse at 50% 0%, rgba(60,100,200,0.35), rgba(70,110,210,0.20) 35%, rgba(80,120,220,0.12) 55%, rgba(255,255,255,0) 75%)",
          maskImage:
            "radial-gradient(ellipse at 50% 0%, rgba(0,0,0,1) 40%, rgba(0,0,0,0.6) 65%, rgba(0,0,0,0) 80%)",
          WebkitMaskImage:
            "radial-gradient(ellipse at 50% 0%, rgba(0,0,0,1) 40%, rgba(0,0,0,0.6) 65%, rgba(0,0,0,0) 80%)",
          filter: "blur(8px)",
          mixBlendMode: "screen",
        }}
      />
    </div>
  );
}

function GridOverlay() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      {/* Coarse grid (64px) — blue-tinted lines */}
      <div
        className="absolute inset-0 opacity-35"
        style={{
          backgroundImage:
            "linear-gradient(rgba(140,170,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(140,170,255,0.10) 1px, transparent 1px)",
          backgroundSize: "64px 64px, 64px 64px",
          backgroundPosition: "center",
        }}
      />
      {/* Fine grid (8px) — slightly brighter blue tint */}
      <div
        className="absolute inset-0 opacity-[0.12]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(110,150,255,0.14) 1px, transparent 1px), linear-gradient(90deg, rgba(110,150,255,0.14) 1px, transparent 1px)",
          backgroundSize: "8px 8px, 8px 8px",
          backgroundPosition: "center",
        }}
      />
    </div>
  );
}

function Stars() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0">
      <div
        className="absolute inset-0"
        style={{
          // Cool white/indigo stars so it matches the hero palette
          backgroundImage:
            "radial-gradient(2px 2px at 20% 30%, rgba(210,220,255,0.50) 35%, transparent 36%), \
             radial-gradient(1.5px 1.5px at 70% 20%, rgba(160,190,255,0.38) 35%, transparent 36%), \
             radial-gradient(1.8px 1.8px at 40% 70%, rgba(170,180,255,0.34) 35%, transparent 36%), \
             radial-gradient(1.2px 1.2px at 80% 60%, rgba(210,220,255,0.45) 35%, transparent 36%)",
          opacity: 0.35,
        }}
      />
    </div>
  );
}

export default function SiteBackdrop() {
  return (
    <>
      <Stars />
      <GridOverlay />
      <TopSpotlight />
    </>
  );
}