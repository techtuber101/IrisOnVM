"use client";

import React, { useState } from "react";
import { SectionHeader } from "@/components/home/section-header";
import { siteConfig } from "@/lib/home";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "motion/react";
import Link from "next/link";

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
      {children}
    </div>
  );
}

// ==============================
// Billing Toggle Component
// ==============================
function BillingToggle({ 
  isYearly, 
  onToggle 
}: { 
  isYearly: boolean; 
  onToggle: (yearly: boolean) => void; 
}) {
  return (
    <div className="flex items-center justify-center mb-8">
      <div className="relative rounded-full border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] p-1">
        {/* Gradient rim */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-full"
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
          className="pointer-events-none absolute inset-x-0 top-0 h-8"
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
        
        <div className="relative flex">
          <button
            onClick={() => onToggle(false)}
            className={cn(
              "relative px-6 py-2 text-sm font-medium rounded-full transition-all duration-300",
              !isYearly 
                ? "text-black bg-white shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)]" 
                : "text-white/70 hover:text-white"
            )}
          >
            Monthly
          </button>
          <button
            onClick={() => onToggle(true)}
            className={cn(
              "relative px-6 py-2 text-sm font-medium rounded-full transition-all duration-300",
              isYearly 
                ? "text-black bg-white shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)]" 
                : "text-white/70 hover:text-white"
            )}
          >
            Yearly
            <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
              Save 17%
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ==============================
// Helpers
// ==============================
function getTierMeta(tierName: string) {
  const name = tierName.toLowerCase();
  if (name.includes("free")) {
    return { showCoins: true, coins: "Free Forever", isEnterprise: false };
  }
  if (name.includes("air")) {
    return { showCoins: true, coins: "10,000 coins/month", isEnterprise: false };
  }
  if (name.includes("pro")) {
    return { showCoins: true, coins: "25,000 coins/month", isEnterprise: false };
  }
  if (name.includes("ultra")) {
    return { showCoins: true, coins: "50,000 coins/month", isEnterprise: false };
  }
  if (name.includes("enterprise")) {
    return { showCoins: false, coins: "", isEnterprise: true };
  }
  return { showCoins: true, coins: "1500 iris daily coins", isEnterprise: false };
}

const PriceDisplay = ({ price }: { price: string }) => (
  <motion.span
    key={price}
    className="text-4xl font-semibold bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent"
    initial={{ opacity: 0, x: 10, filter: "blur(5px)" }}
    animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
    transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
  >
    {price}
  </motion.span>
);

// ==============================
// Comparison Table Component
// ==============================
function ComparisonTable() {
  const features = [
    { name: "Pricing", free: "₹0", air: "₹1,000", pro: "₹2,500", ultra: "₹3,000", enterprise: "Custom", hasInfo: false },
    { name: "Daily Coins", free: "1,000", air: "1,200", pro: "1,500", ultra: "2,000", enterprise: "Unlimited", hasInfo: true },
    { name: "Monthly Coin Reserve", free: "0", air: "10,000", pro: "25,000", ultra: "50,000", enterprise: "Unlimited", hasInfo: true },
    { name: "Chats/Tasks", free: "Unlimited", air: "Unlimited", pro: "Unlimited", ultra: "Unlimited", enterprise: "Unlimited", hasInfo: false },
    { name: "Iris Integrations", free: "3", air: "25", pro: "Unlimited", ultra: "Unlimited", enterprise: "Unlimited", hasInfo: true },
    { name: "Support", free: "Community", air: "Priority", pro: "24/7", ultra: "24/7 Priority", enterprise: "Dedicated", hasInfo: false },
    { name: "Early Access", free: false, air: false, pro: true, ultra: true, enterprise: true, hasInfo: false },
  ];

  const CheckIcon = () => (
    <div className="w-5 h-5 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center">
      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
      </svg>
    </div>
  );

  const CrossIcon = () => (
    <div className="w-5 h-5 rounded-full bg-gradient-to-r from-red-500/20 to-red-600/20 border border-red-500/30 flex items-center justify-center">
      <svg className="w-3 h-3 text-red-400" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
      </svg>
    </div>
  );

  const InfoIcon = ({ featureName }: { featureName: string }) => (
    <div className="relative group">
      <div className="w-4 h-4 rounded-full bg-white/20 border border-white/30 flex items-center justify-center cursor-help">
        <svg className="w-2.5 h-2.5 text-white/70" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
        </svg>
      </div>
      
      {/* Tooltip */}
      <div className="absolute left-full top-1/2 transform -translate-y-1/2 ml-2 w-64 p-4 rounded-2xl border border-white/10 bg-[rgba(10,14,22,0.95)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-[100]">
        {/* Gradient rim */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 rounded-2xl"
          style={{
            background:
              "linear-gradient(180deg, rgba(173,216,255,0.18), rgba(255,255,255,0.04) 30%, rgba(150,160,255,0.14) 85%, rgba(255,255,255,0.06))",
            WebkitMask: "linear-gradient(#000,#000) content-box, linear-gradient(#000,#000)",
            WebkitMaskComposite: "xor" as any,
            maskComposite: "exclude",
            padding: 1,
            borderRadius: 16,
          }}
        />
        {/* Specular streak */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-16"
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
        
        <div className="relative z-10">
          <h4 className="text-sm font-semibold text-white/90 mb-2">{featureName}</h4>
          <p className="text-xs text-white/70 leading-relaxed">
            {featureName === "Daily Coins" 
              ? "Daily Coins are coins you get every single day which get refreshed every day. No stacking on daily coins."
              : featureName === "Monthly Coin Reserve"
              ? "Monthly Coin Reserve are coins you get at the start of each month that accumulate and can be used throughout the month. These coins stack and don't expire until the month ends."
              : "Iris lets you connect and integrate with over 100 third-party apps & services that you use on a daily basis, to let Iris unlock productivity for you in unimaginable ways."
            }
          </p>
        </div>
        
        {/* Arrow */}
        <div className="absolute right-full top-1/2 transform -translate-y-1/2 w-0 h-0 border-t-4 border-b-4 border-r-4 border-transparent border-r-white/10"></div>
      </div>
    </div>
  );

  return (
    <div className="w-full max-w-7xl mx-auto px-6 mt-16">
      <h3 className="text-2xl font-semibold text-center mb-8 bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent">
        Compare All Features
      </h3>
      
      <GlassCard className="overflow-visible">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/10">
                <th className="text-left p-6 font-semibold text-white/90">Features</th>
                <th className="text-center p-6 font-semibold text-white/90">Free</th>
                <th className="text-center p-6 font-semibold text-white/90">Iris Air</th>
                <th className="text-center p-6 font-semibold text-white/90">Iris Pro</th>
                <th className="text-center p-6 font-semibold text-white/90">Iris Ultra</th>
                <th className="text-center p-6 font-semibold text-white/90">Enterprise</th>
              </tr>
            </thead>
            <tbody>
              {features.map((feature, index) => (
                <motion.tr
                  key={feature.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                          <td className="p-6 font-medium text-white/80">
                            <div className="flex items-center gap-2">
                              <span>{feature.name}</span>
                              {feature.hasInfo && <InfoIcon featureName={feature.name} />}
                            </div>
                          </td>
                  <td className="p-6 text-center text-white/70">
                    {typeof feature.free === 'boolean' ? (
                      <div className="flex justify-center items-center">
                        {feature.free ? <CheckIcon /> : <CrossIcon />}
                      </div>
                    ) : (
                      <span className="text-white/70">{feature.free}</span>
                    )}
                  </td>
                  <td className="p-6 text-center text-white/70">
                    {typeof feature.air === 'boolean' ? (
                      <div className="flex justify-center items-center">
                        {feature.air ? <CheckIcon /> : <CrossIcon />}
                      </div>
                    ) : (
                      <span className="text-white/70">{feature.air}</span>
                    )}
                  </td>
                  <td className="p-6 text-center text-white/70">
                    {typeof feature.pro === 'boolean' ? (
                      <div className="flex justify-center items-center">
                        {feature.pro ? <CheckIcon /> : <CrossIcon />}
                      </div>
                    ) : (
                      <span className="text-white/70">{feature.pro}</span>
                    )}
                  </td>
                  <td className="p-6 text-center text-white/70">
                    {typeof feature.ultra === 'boolean' ? (
                      <div className="flex justify-center items-center">
                        {feature.ultra ? <CheckIcon /> : <CrossIcon />}
                      </div>
                    ) : (
                      <span className="text-white/70">{feature.ultra}</span>
                    )}
                  </td>
                  <td className="p-6 text-center text-white/70">
                    {typeof feature.enterprise === 'boolean' ? (
                      <div className="flex justify-center items-center">
                        {feature.enterprise ? <CheckIcon /> : <CrossIcon />}
                      </div>
                    ) : (
                      <span className="text-white/70">{feature.enterprise}</span>
                    )}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </GlassCard>
    </div>
  );
}

// ==============================
// Component
// ==============================
export function PricingSection() {
  const [isYearly, setIsYearly] = useState(false);

  return (
    <section
      id="pricing"
      className="relative w-full flex flex-col items-center justify-center gap-10 pb-20"
    >
      <SectionHeader>
        <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-center bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent">
          Choose Your Iris Experience
        </h2>
        <p className="text-center text-white/70 font-medium text-balance">
          Intelligence in ways you've never imagined.
        </p>
      </SectionHeader>

      {/* Billing Toggle */}
      <BillingToggle isYearly={isYearly} onToggle={setIsYearly} />

              {/* Pricing grid - 4 columns */}
              <div className="grid min-[650px]:grid-cols-2 min-[1000px]:grid-cols-4 gap-5 w-full max-w-7xl mx-auto px-6">
        {siteConfig.cloudPricingItems.filter(tier => !tier.name.toLowerCase().includes('enterprise')).map((tier) => {
          const meta = getTierMeta(tier.name);
          const isEnterprise = meta.isEnterprise;

          // Get the correct price based on billing period
          const displayPrice = isYearly ? tier.yearlyPrice : tier.price;
          const originalPrice = isYearly && tier.originalYearlyPrice ? tier.originalYearlyPrice : null;

          // Normalize button text: "Hire Iris" -> "Get Now"
          const rawBtn = tier.buttonText || "";
          const buttonText = rawBtn.toLowerCase() === "hire iris" ? "Get Now" : rawBtn || "Get Now";

          // Build CTA link: prefer Stripe priceId if you route through /checkout, else default to /auth
          const ctaHref = tier.stripePriceId
            ? `/checkout?priceId=${encodeURIComponent(isYearly ? tier.yearlyStripePriceId || tier.stripePriceId : tier.stripePriceId)}`
            : "/auth";

          return (
            <GlassCard
              key={tier.name}
              className={cn(
                "flex flex-col relative h-fit min-[650px]:h-full transition-transform hover:-translate-y-0.5"
              )}
            >
              {/* Header / Price */}
              <div className="p-5 flex flex-col gap-3 flex-1">
                <p className="text-sm flex items-center">
                  <span className="bg-clip-text text-transparent bg-gradient-to-b from-white to-white/70">
                    {tier.name}
                  </span>
                  {tier.isPopular && (
                    <span className="ml-2 inline-flex items-center h-6 px-2 rounded-full text-xs font-medium text-white bg-white/10 ring-1 ring-white/20">
                      Popular
                    </span>
                  )}
                </p>

                <div className="flex items-baseline mt-1 flex-wrap gap-1">
                  <AnimatePresence mode="wait">
                    <PriceDisplay key={displayPrice} price={displayPrice || tier.price} />
                  </AnimatePresence>
                  {originalPrice && (
                    <span className="text-sm text-white/50 line-through">
                      {originalPrice}
                    </span>
                  )}
                  <span className="text-white/70 text-sm">
                    {tier.price !== "₹0" ? (isYearly ? "/year" : "/month") : ""}
                  </span>
                </div>

                <p className="text-sm text-white/70">{tier.description}</p>

                {/* Coins / Enterprise badge - Always show a badge for consistent spacing */}
                <div className="h-6 flex items-center">
                  {meta.showCoins && (
                    <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-2.5 py-0.5 text-xs font-semibold text-white w-fit">
                      {meta.coins}
                    </div>
                  )}
                  {isEnterprise && (
                    <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-2.5 py-0.5 text-xs font-semibold text-white/80 w-fit">
                      Contact sales
                    </div>
                  )}
                </div>
              </div>

              {/* CTA */}
              <div className="px-5 pb-5 mt-auto">
                {isEnterprise ? (
                  <Link
                    href="/contact"
                    className={cn(
                      "h-10 w-full flex items-center justify-center text-sm tracking-wide rounded-full px-4 transition-all active:scale-[0.99]",
                      "bg-white text-black shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)] hover:bg-white/90"
                    )}
                  >
                    Contact sales
                  </Link>
                ) : (
                  <Link
                    href={ctaHref}
                    className={cn(
                      "h-10 w-full flex items-center justify-center text-sm tracking-wide rounded-full px-4 transition-all active:scale-[0.99]",
                      "bg-white text-black shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)] hover:bg-white/90"
                    )}
                  >
                    {buttonText || "Get Now"}
                  </Link>
                )}
              </div>

            </GlassCard>
          );
        })}
      </div>

      {/* Enterprise Card */}
      <div className="w-full max-w-lg mx-auto px-6 mt-4">
        <GlassCard className="p-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-sm font-semibold bg-gradient-to-b from-white to-white/70 bg-clip-text text-transparent">
                Enterprise
              </h3>
              <p className="text-xs text-white/70 mt-0.5">
                Custom solutions for large organizations
              </p>
            </div>
            <Link
              href="/contact"
              className={cn(
                "h-8 px-4 flex items-center justify-center text-xs tracking-wide rounded-full transition-all active:scale-[0.99] flex-shrink-0",
                "bg-white text-black shadow-[0_10px_20px_-12px_rgba(255,255,255,0.6)] hover:bg-white/90"
              )}
            >
              Contact Sales
            </Link>
          </div>
        </GlassCard>
      </div>

      {/* Comparison Table */}
      <ComparisonTable />
    </section>
  );
}
