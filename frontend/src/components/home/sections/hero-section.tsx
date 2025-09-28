"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string };

// -----------------------------
// Local storage for tiny chat
// -----------------------------
function useLocalMessages(storageKey: string, initial: ChatMessage[]) {
  const [messages, setMessages] = useState<ChatMessage[]>(initial);

  useEffect(() => {
    try {
      const raw = typeof window !== "undefined" && window.localStorage.getItem(storageKey);
      if (raw) setMessages(JSON.parse(raw));
    } catch {}
  }, [storageKey]);

  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(storageKey, JSON.stringify(messages));
      }
    } catch {}
  }, [messages, storageKey]);

  return { messages, setMessages } as const;
}

// -----------------------------
// Glass primitives (match site)
// -----------------------------
const baseGlass =
  "relative rounded-3xl border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden";

function GlassCard({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={`${baseGlass} ${className}`}>
      {/* Gradient rim (subtle) */}
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
            "url('data:image/svg+xml;utf8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'60\' height=\'60\'><filter id=\'n\'><feTurbulence type=\'fractalNoise\' baseFrequency=\'0.8\' numOctaves=\'4\'/><feColorMatrix type=\'saturate\' values=\'0\'/><feComponentTransfer><feFuncA type=\'table\' tableValues=\'0 0.03\'/></feComponentTransfer></filter><rect width=\'100%\' height=\'100%\' filter=\'url(%23n)\' /></svg>')",
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

function ChatBubble({ messages, onSend, samplePrompts }: { messages: ChatMessage[]; onSend: (text: string) => void; samplePrompts: string[] }) {
  const [text, setText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showPrompts, setShowPrompts] = useState(true);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const t = text.trim();
    if (!t) return;
    setText("");
    setShowPrompts(false);
    onSend(t);
  };

  const handlePromptClick = (prompt: string) => {
    setText(prompt);
    setShowPrompts(false);
    onSend(prompt);
  };

  const handleInputFocus = () => {
    setIsTyping(true);
  };

  const handleInputBlur = () => {
    if (!text.trim()) {
      setIsTyping(false);
    }
  };

  return (
    <div className="relative">
      {/* Main chat container with integrated input */}
      <div
        ref={listRef}
        className={`relative min-h-[22vh] max-h-[38vh] overflow-y-auto rounded-2xl border border-white/10 bg-[rgba(7,10,17,0.95)] p-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)] transition-all duration-300 ${
          isTyping ? 'ring-1 ring-white/20' : ''
        }`}
      >
        {/* Messages */}
        {messages.map((m) => (
          <div key={m.id} className="mb-2 flex">
            <div
              className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed ring-1 shadow-[0_10px_20px_-10px_rgba(0,0,0,0.6)] ${
                m.role === "user" ? "ml-auto bg-white/10 ring-white/15" : "bg-white/5 ring-white/10"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}

        {/* Sample prompts */}
        {showPrompts && messages.length === 1 && (
          <div className="mt-4 space-y-2">
            <p className="text-xs text-white/50 mb-3">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {samplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handlePromptClick(prompt)}
                  className="px-3 py-1.5 text-xs rounded-full bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:border-white/20 transition-all duration-200"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Integrated input area */}
        <div className="sticky bottom-0 mt-4 pt-3 border-t border-white/5">
          <form onSubmit={submit} className="flex items-center gap-2">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                aria-label="Ask Iris"
                placeholder="Ask Iris anything…"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
                className="w-full h-11 rounded-2xl border border-white/15 bg-white/5 px-4 text-sm placeholder:text-white/40 outline-none ring-0 backdrop-blur-sm focus:border-white/25 focus:bg-white/8 transition-all duration-200"
              />
            </div>
            <button
              type="submit"
              disabled={!text.trim()}
              className="h-11 rounded-2xl border border-white/20 bg-white/10 px-4 text-sm text-white/90 transition-all duration-200 hover:border-white/30 hover:bg-white/15 active:translate-y-[1px] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// -----------------------------
// Main component
// -----------------------------
type HeroProps = {
  title?: string;
  product?: string;
  subhead?: string;
  irisTitle?: string;
  storageKey?: string;
  /** Optional: override the destination after capturing pending prompt */
  returnUrl?: string; // default "/dashboard"
};

const PENDING_PROMPT_KEY = "pendingAgentPrompt";

const HeroSection: React.FC<HeroProps> = ({
  title = "Iris",
  product = "Introducing",
  subhead = "The world's best agentic AI",
  irisTitle = "Iris",
  storageKey = "iris.chat",
  returnUrl = "/dashboard",
}) => {
  const seed: ChatMessage[] = useMemo(
    () => [{ id: "seed-assistant", role: "assistant", content: "Hi there! I'm Iris, your AI assistant. I can help you build websites, create apps, write and send emails, analyze data, create all kinds of documents, and much more. What would you like to accomplish today?" }],
    []
  );

  const samplePrompts = [
    "Send me a summary of my emails this morning",
    "Create an executive report",
    "Create a website for my cooking brand",
    
    "Fix code issues and raise a pull request"
  ];

  const { messages, setMessages } = useLocalMessages(storageKey, seed);
  const router = useRouter();
  const { user } = useAuth();

  const handleSend = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(PENDING_PROMPT_KEY, trimmed);
      }
      const to = user ? returnUrl : `/auth?mode=signin&returnUrl=${encodeURIComponent(returnUrl)}`;
      router.push(to);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <section id="hero" className="relative min-h-[92vh] w-full overflow-hidden pt-[140px] text-white">
      {/* very soft local halo to keep hero focus without duplicating the global spotlight */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 -top-10 h-72 blur-3xl opacity-40"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 0%, rgba(120,160,255,0.18), rgba(120,160,255,0.06) 55%, transparent 85%)",
          mixBlendMode: "screen",
        }}
      />

      {/* Content container */}
      <div className="relative mx-auto flex h-full max-w-6xl flex-col items-center justify-center px-6 py-24">
        {/* Eyebrow */}
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mb-2 text-sm/6 text-white/70"
        >
          {product}
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="bg-gradient-to-b from-white to-white/70 bg-clip-text text-center text-7xl font-semibold tracking-tight text-transparent md:text-8xl"
        >
          {title}
        </motion.h1>

        {/* Subhead */}
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mt-4 max-w-2xl text-balance text-center text-lg text-white/70"
        >
          {subhead}
        </motion.p>

        {/* Card stack */}
        <div className="relative mt-12 w-full max-w-6xl">
          {/* Left placeholder card */}
          <motion.div
            initial={{ opacity: 0, x: -40, rotate: -6 }}
            animate={{ opacity: 1, x: 0, rotate: -6 }}
            transition={{ duration: 0.6, delay: 0.35 }}
            whileHover={{ 
              y: -12, 
              scale: 1.02,
              zIndex: 50,
              transition: { duration: 0.4, ease: "easeOut" }
            }}
            className="absolute left-[-4%] top-8 hidden w-[42%] -rotate-6 p-6 md:block pointer-events-auto cursor-pointer group"
          >
            <GlassCard className="transition-all duration-400 group-hover:shadow-[0_20px_60px_-8px_rgba(0,0,0,0.8)] group-hover:ring-1 group-hover:ring-blue-400/20 group-hover:opacity-95">
              <div className="p-6">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-white/10 ring-1 ring-white/15" />
                  <div className="h-3 w-28 rounded bg-white/10" />
        </div>
                <PlaceholderCard direction="left" />
        </div>
            </GlassCard>
          </motion.div>

          {/* Right placeholder card */}
          <motion.div
            initial={{ opacity: 0, x: 40, rotate: 6 }}
            animate={{ opacity: 1, x: 0, rotate: 6 }}
            transition={{ duration: 0.6, delay: 0.38 }}
            whileHover={{ 
              y: -12, 
              scale: 1.02,
              zIndex: 50,
              transition: { duration: 0.4, ease: "easeOut" }
            }}
            className="absolute right-[-4%] top-8 hidden w-[42%] rotate-6 p-6 md:block pointer-events-auto cursor-pointer group"
          >
            <GlassCard className="transition-all duration-400 group-hover:shadow-[0_20px_60px_-8px_rgba(0,0,0,0.8)] group-hover:ring-1 group-hover:ring-green-400/20 group-hover:opacity-95">
              <div className="p-6">
                <div className="mb-4 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-white/10 ring-1 ring-white/15" />
                  <div className="h-3 w-28 rounded bg-white/10" />
          </div>
                <PlaceholderCard direction="right" />
              </div>
            </GlassCard>
          </motion.div>

          {/* Center interactive chat card */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.45 }}
            className="relative z-10 mx-auto w-[92%] p-0 md:w-[58%]"
          >
            <GlassCard>
              <div className="p-6 md:p-7">
                <header className="mb-4 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-full bg-white/10 ring-1 ring-white/20 flex items-center justify-center">
                    <img 
                      src="/iris-symbol.png" 
                      alt="Iris Logo" 
                      className="h-4 w-4 brightness-0 invert"
                    />
            </div>
                  <h3 className="text-sm font-medium text-white/80">Iris</h3>
                </header>
                <ChatBubble messages={messages} onSend={handleSend} samplePrompts={samplePrompts} />
          </div>
            </GlassCard>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

function PlaceholderCard({ direction }: { direction: "left" | "right" }) {
  if (direction === "left") {
    return (
      <div className="pointer-events-none select-none opacity-90">
        {/* Vision Card - Real Content */}
        <div className="mb-4 flex items-center gap-2">
          <div className="h-6 w-6 rounded-full bg-gradient-to-br from-blue-400/20 to-purple-400/20 ring-1 ring-blue-400/30 flex items-center justify-center">
            <svg className="w-3 h-3 text-blue-300" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="text-sm font-medium text-blue-300/80">Vision</span>
        </div>
        
        <div className="space-y-3">
          <div className="p-3 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 ring-1 ring-blue-400/20">
            <div className="text-xs text-blue-200/70 font-medium mb-1">Understanding You</div>
            <div className="text-xs text-blue-300/60">I see your vision, and the end goal that you wish to achieve.</div>
          </div>
          <div className="p-3 rounded-lg bg-gradient-to-r from-blue-500/10 to-purple-500/10 ring-1 ring-blue-400/20">
            <div className="text-xs text-blue-200/70 font-medium mb-1">Strategic Autonomous Planning</div>
            <div className="text-xs text-blue-300/60"> Creating a comprehensive to-do list to execute this vision</div>
          </div>
        </div>
        
        <div className="mt-4 flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-blue-400/60 animate-pulse" />
          <span className="text-xs text-blue-300/70 font-medium">Vision → Plan</span>
        </div>
      </div>
    );
  }

  return (
    <div className="pointer-events-none select-none opacity-90">
      {/* Execute Card - Real Content */}
      <div className="mb-4 flex items-center gap-2">
        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-green-400/20 to-emerald-400/20 ring-1 ring-green-400/30 flex items-center justify-center">
          <svg className="w-3 h-3 text-green-300" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="text-sm font-medium text-green-300/80">Execute</span>
      </div>
      
      <div className="space-y-3">
        <div className="p-3 rounded-lg bg-gradient-to-r from-green-500/10 to-emerald-500/10 ring-1 ring-green-400/20">
          <div className="text-xs text-green-200/70 font-medium mb-1">Rigorous Analysis</div>
          <div className="text-xs text-green-300/60">I will deep analyze the market to provide best possible insights.</div>
        </div>
        <div className="p-3 rounded-lg bg-gradient-to-r from-green-500/10 to-emerald-500/10 ring-1 ring-green-400/20">
          <div className="text-xs text-green-200/70 font-medium mb-1">Autonomous, Seamless Execution</div>
          <div className="text-xs text-green-300/60">I have completed every single task, delivering results.</div>
        </div>
      </div>
      
      <div className="mt-4 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-green-400/60 animate-pulse" />
        <span className="text-xs text-green-300/70 font-medium">Analyze → Execute</span>
      </div>
    </div>
  );
}

export default HeroSection;
export { HeroSection };
