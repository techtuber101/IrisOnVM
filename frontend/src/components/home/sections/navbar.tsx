"use client";

import { Icons } from "@/components/home/icons";
import { NavMenu } from "@/components/home/nav-menu";
import { siteConfig } from "@/lib/home";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";
import { AnimatePresence, motion, useScroll } from "motion/react";
import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";

const INITIAL_WIDTH = "70rem";
const MAX_WIDTH = "800px";

const overlayVariants = { hidden: { opacity: 0 }, visible: { opacity: 1 }, exit: { opacity: 0 } };
const drawerVariants = {
  hidden: { opacity: 0, y: 100 },
  visible: { opacity: 1, y: 0, rotate: 0, transition: { type: "spring", damping: 15, stiffness: 200, staggerChildren: 0.03 } },
  exit: { opacity: 0, y: 100, transition: { duration: 0.1 } },
};
const drawerMenuContainerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1 } };
const drawerMenuVariants = { hidden: { opacity: 0 }, visible: { opacity: 1 } };

export function Navbar() {
  const { scrollY } = useScroll();
  const [hasScrolled, setHasScrolled] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("hero");
  const [mounted, setMounted] = useState(false);
  const { user } = useAuth();

  useEffect(() => setMounted(true), []);

  // Highlight current section
  useEffect(() => {
    const handleScroll = () => {
      const sections = siteConfig.nav.links.map((item) => item.href.substring(1));
      for (const section of sections) {
        const el = document.getElementById(section);
        if (!el) continue;
        const rect = el.getBoundingClientRect();
        if (rect.top <= 150 && rect.bottom >= 150) {
          setActiveSection(section);
          break;
        }
      }
    };
    window.addEventListener("scroll", handleScroll);
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Toggle glass on scroll
  useEffect(() => {
    const unsub = scrollY.on("change", (latest) => setHasScrolled(latest > 10));
    return unsub;
  }, [scrollY]);

  const toggleDrawer = () => setIsDrawerOpen((p) => !p);
  const handleOverlayClick = () => setIsDrawerOpen(false);

  const logoSrc = "/iris-logo.png";

  return (
    <header
      className={cn(
        // CENTERED, FLOATING “PILL” CONTAINER
        "fixed top-4 left-1/2 -translate-x-1/2 z-50 transition-all duration-300"
      )}
      // ensure the centered container doesn't get clipped on tiny screens
      style={{ width: "min(100vw - 1rem, 80rem)" }}
    >
      {/* Animate the container width as you scroll (keeps it centered) */}
      <motion.div
        className="mx-auto"
        initial={{ width: INITIAL_WIDTH }}
        animate={{ width: hasScrolled ? MAX_WIDTH : INITIAL_WIDTH }}
        transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      >
        <div
          className={cn(
            // The pill itself
            "rounded-full transition-all duration-300",
            hasScrolled
              // scrolled: glassy pill
              ? "border border-border bg-background/70 backdrop-blur-md shadow-lg px-2"
              // top: totally transparent — no bg, no border, no blur, no shadow
              : "border-transparent bg-transparent backdrop-blur-0 shadow-none px-7"
          )}
        >
          <div className="flex h-[56px] items-center justify-between px-4 md:px-6">
            {/* Left: Logo */}
            <Link href="/" className="flex items-center gap-3">
              <Image src={logoSrc} alt="Iris Logo" width={140} height={22} priority />
            </Link>

            {/* Center: Menu */}
            <NavMenu />

            {/* Right: Actions */}
            <div className="flex flex-row items-center gap-1 md:gap-3 shrink-0">
              <div className="hidden md:flex items-center space-x-3">
                {user ? (
                  <Link
                    className="group relative inline-flex"
                    href="/dashboard"
                  >
                    <motion.div
                      whileHover={{ y: -1 }}
                      className="relative rounded-full border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden"
                    >
                      {/* Gradient rim */}
                      <div
                        aria-hidden
                        className="pointer-events-none absolute inset-0 rounded-full"
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
                        className="pointer-events-none absolute inset-x-0 top-0 h-6"
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
                      {/* Subtle glow pulse */}
                      <div className="pointer-events-none absolute inset-0 rounded-full bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
                      {/* Button content */}
                      <span className="relative z-10 text-white font-normal text-sm h-8 px-4 rounded-full inline-flex items-center gap-2">
                        Dashboard
                      </span>
                    </motion.div>
                  </Link>
                ) : (
                  <Link
                    className="group relative inline-flex"
                    href="/auth"
                  >
                    <motion.div
                      whileHover={{ y: -1 }}
                      className="relative rounded-full border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden"
                    >
                      {/* Gradient rim */}
                      <div
                        aria-hidden
                        className="pointer-events-none absolute inset-0 rounded-full"
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
                        className="pointer-events-none absolute inset-x-0 top-0 h-6"
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
                      {/* Subtle glow pulse */}
                      <div className="pointer-events-none absolute inset-0 rounded-full bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
                      {/* Button content */}
                      <span className="relative z-10 text-white font-normal text-sm h-8 px-4 rounded-full inline-flex items-center gap-2">
                        Get Started
                      </span>
                    </motion.div>
                  </Link>
                )}
              </div>
              <button
                className="md:hidden border border-border size-8 rounded-md cursor-pointer flex items-center justify-center"
                onClick={toggleDrawer}
              >
                {isDrawerOpen ? <X className="size-5" /> : <Menu className="size-5" />}
              </button>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {isDrawerOpen && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/50 backdrop-blur-sm"
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={overlayVariants}
              transition={{ duration: 0.2 }}
              onClick={handleOverlayClick}
            />
            <motion.div
              className="fixed inset-x-0 w-[95%] mx-auto bottom-3 bg-background border border-border p-4 rounded-xl shadow-lg"
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={drawerVariants}
            >
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <Link href="/" className="flex items-center gap-3">
                    <Image src={logoSrc} alt="Iris Logo" width={120} height={22} priority />
                    <span className="font-medium text-primary text-sm">Iris</span>
                  </Link>
                  <button onClick={toggleDrawer} className="border border-border rounded-md p-1 cursor-pointer">
                    <X className="size-5" />
                  </button>
                </div>

                <motion.ul className="flex flex-col text-sm mb-4 border border-border rounded-md" variants={drawerMenuContainerVariants}>
                  <AnimatePresence>
                    {siteConfig.nav.links.map((item) => (
                      <motion.li key={item.id} className="p-2.5 border-b border-border last:border-b-0" variants={drawerMenuVariants}>
                        <a
                          href={item.href}
                          onClick={(e) => {
                            e.preventDefault();
                            const el = document.getElementById(item.href.substring(1));
                            el?.scrollIntoView({ behavior: "smooth" });
                            setIsDrawerOpen(false);
                          }}
                          className={cn(
                            "underline-offset-4 hover:text-primary/80 transition-colors",
                            activeSection === item.href.substring(1) ? "text-primary font-medium" : "text-primary/60"
                          )}
                        >
                          {item.name}
                        </a>
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </motion.ul>

                <div className="flex flex-col gap-2">
                  {user ? (
                    <Link
                      href="/dashboard"
                      className="group relative inline-flex w-full"
                    >
                      <motion.div
                        whileHover={{ y: -1 }}
                        className="relative w-full rounded-full border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden"
                      >
                        {/* Gradient rim */}
                        <div
                          aria-hidden
                          className="pointer-events-none absolute inset-0 rounded-full"
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
                          className="pointer-events-none absolute inset-x-0 top-0 h-6"
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
                        {/* Subtle glow pulse */}
                        <div className="pointer-events-none absolute inset-0 rounded-full bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
                        {/* Button content */}
                        <span className="relative z-10 text-white font-normal text-sm h-8 px-4 rounded-full inline-flex items-center justify-center gap-2 w-full">
                          Dashboard
                        </span>
                      </motion.div>
                    </Link>
                  ) : (
                    <Link
                      href="/auth"
                      className="group relative inline-flex w-full"
                    >
                      <motion.div
                        whileHover={{ y: -1 }}
                        className="relative w-full rounded-full border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden"
                      >
                        {/* Gradient rim */}
                        <div
                          aria-hidden
                          className="pointer-events-none absolute inset-0 rounded-full"
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
                          className="pointer-events-none absolute inset-x-0 top-0 h-6"
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
                        {/* Subtle glow pulse */}
                        <div className="pointer-events-none absolute inset-0 rounded-full bg-white/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
                        {/* Button content */}
                        <span className="relative z-10 text-white font-normal text-sm h-8 px-4 rounded-full inline-flex items-center justify-center gap-2 w-full">
                          Get Started
                        </span>
                      </motion.div>
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </header>
  );
}
