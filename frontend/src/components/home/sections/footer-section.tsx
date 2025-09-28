"use client";

import { FlickeringGrid } from "@/components/home/ui/flickering-grid";
import { useMediaQuery } from "@/hooks/use-media-query";
import { siteConfig } from "@/lib/home";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Twitter, Linkedin, Mail } from "lucide-react";

export function FooterSection() {
  const tablet = useMediaQuery("(max-width: 1024px)");

  return (
    <footer id="footer" className="w-full relative overflow-hidden">
      {/* Main footer content */}
      <div className="relative z-10 bg-background/95 backdrop-blur-sm border-t border-border/50">
        <div className="max-w-7xl mx-auto px-6 py-16">
          {/* Top section - Logo and tagline */}
          <div className="text-center mb-12">
            <Link href="/" className="inline-block mb-6">
              <Image
                src="/iris-logo.png"
                alt="Iris Logo"
                width={140}
                height={28}
                priority
                unoptimized
                className="mx-auto"
              />
            </Link>
            <p className="text-2xl md:text-3xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              <span className="font-thin text-3xl md:text-4xl text-primary" style={{ fontFamily: 'Dancing Script, Brush Script MT, cursive, serif', fontWeight: 300 }}>
                Feel The Future
              </span>
              <br />
              <span className="text-sm text-primary font-medium">Vision → Plan → Analyze → Execute</span>
            </p>
          </div>

          {/* Links grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
            {siteConfig.footerLinks.map((column, columnIndex) => (
              <div key={columnIndex} className="space-y-4">
                <h3 className="text-sm font-semibold text-foreground uppercase tracking-wider">
                  {column.title}
                </h3>
                <ul className="space-y-3">
                  {column.links.map((link) => (
                    <li key={link.id}>
                      <Link 
                        href={link.url}
                        className="text-muted-foreground hover:text-primary transition-colors duration-200 text-sm group flex items-center gap-2"
                      >
                        {link.title}
                        <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Bottom section - Social links and copyright */}
          <div className="border-t border-border/50 pt-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              {/* Social links */}
              <div className="flex items-center gap-6">
                <a 
                  href="https://x.com/irisai" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors duration-200 group"
                  aria-label="X (Twitter)"
                >
                  <Twitter className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors duration-200" />
                </a>
                <a 
                  href="https://www.linkedin.com/company/irisai" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors duration-200 group"
                  aria-label="LinkedIn"
                >
                  <Linkedin className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors duration-200" />
                </a>
                <a 
                  href="mailto:hello@iris.ai" 
                  className="p-2 rounded-lg bg-muted/50 hover:bg-muted transition-colors duration-200 group"
                  aria-label="Email"
                >
                  <Mail className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors duration-200" />
                </a>
              </div>

              {/* Copyright */}
              <div className="text-sm text-muted-foreground">
                © 2024 Iris AI. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Animated background */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-transparent" />
        <FlickeringGrid
          text={tablet ? "Iris Iris Iris" : "Iris Iris Iris"}
          fontSize={tablet ? 60 : 80}
          className="h-full w-full opacity-20"
          squareSize={1.5}
          gridGap={tablet ? 1.5 : 2}
          color="var(--primary)"
          maxOpacity={0.15}
          flickerChance={0.05}
        />
      </div>
    </footer>
  );
}
