'use client';

import * as React from 'react';
import Link from 'next/link';
import { Bot, Menu, Plus, Zap, ChevronRight, Search } from 'lucide-react';

import { NavAgents } from '@/components/sidebar/nav-agents';
import { NavUserWithTeams } from '@/components/sidebar/nav-user-with-teams';
import { KortixLogo } from '@/components/sidebar/kortix-logo';
import { CTACard } from '@/components/sidebar/cta';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { NewAgentDialog } from '@/components/agents/new-agent-dialog';
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Button } from '@/components/ui/button';
import { useIsMobile } from '@/hooks/use-mobile';
import { cn } from '@/lib/utils';
import { usePathname, useSearchParams } from 'next/navigation';
import posthog from 'posthog-js';
import { useDocumentModalStore } from '@/lib/stores/use-document-modal-store';
import { Dialog, DialogContent, DialogTrigger, DialogTitle } from '@/components/ui/dialog';

function FloatingMobileMenuButton() {
  const { setOpenMobile, openMobile } = useSidebar();
  const isMobile = useIsMobile();

  if (!isMobile || openMobile) return null;

  return (
    <div className="fixed top-6 left-4 z-50">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            onClick={() => setOpenMobile(true)}
            size="icon"
            className="h-12 w-12 rounded-full bg-primary text-primary-foreground shadow-lg hover:bg-primary/90 transition-all duration-200 hover:scale-105 active:scale-95 touch-manipulation"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          Open menu
        </TooltipContent>
      </Tooltip>
    </div>
  );
}

export function SidebarLeft({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { state, setOpen, setOpenMobile } = useSidebar();
  const isMobile = useIsMobile();
  const [user, setUser] = useState<{
    name: string;
    email: string;
    avatar: string;
    isAdmin?: boolean;
  }>({
    name: 'Loading...',
    email: 'loading@example.com',
    avatar: '',
    isAdmin: false,
  });

  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [showNewAgentDialog, setShowNewAgentDialog] = useState(false);
  const [showSearchDialog, setShowSearchDialog] = useState(false);
  const { isOpen: isDocumentModalOpen } = useDocumentModalStore();

  useEffect(() => {
    if (isMobile) {
      setOpenMobile(false);
    }
  }, [pathname, searchParams, isMobile, setOpenMobile]);

  
  useEffect(() => {
    const fetchUserData = async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();
      if (data.user) {
        const { data: roleData } = await supabase
          .from('user_roles')
          .select('role')
          .eq('user_id', data.user.id)
          .in('role', ['admin', 'super_admin']);
        const isAdmin = roleData && roleData.length > 0;
        
        setUser({
          name:
            data.user.user_metadata?.name ||
            data.user.email?.split('@')[0] ||
            'User',
          email: data.user.email || '',
          avatar: data.user.user_metadata?.avatar_url || '',
          isAdmin: isAdmin,
        });
      }
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isDocumentModalOpen) return;
      
      if ((event.metaKey || event.ctrlKey) && event.key === 'b') {
        event.preventDefault();
        setOpen(!state.startsWith('expanded'));
        window.dispatchEvent(
          new CustomEvent('sidebar-left-toggled', {
            detail: { expanded: !state.startsWith('expanded') },
          }),
        );
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state, setOpen, isDocumentModalOpen]);




  return (
    <Sidebar
      collapsible="icon"
      className="border-r-0 bg-background/95 backdrop-blur-sm [&::-webkit-scrollbar]:hidden [-ms-overflow-style:'none'] [scrollbar-width:'none']"
      {...props}
    >
      <SidebarHeader className="px-2 py-2">
        <div className="flex h-[40px] items-center px-1 relative">
          <Link href="/dashboard" className="flex-shrink-0" onClick={() => isMobile && setOpenMobile(false)}>
            <KortixLogo size={24} />
          </Link>
          {state !== 'collapsed' && (
            <div className="ml-2 transition-all duration-200 ease-in-out whitespace-nowrap">
            </div>
          )}
          <div className="ml-auto flex items-center gap-2">
            {state !== 'collapsed' && !isMobile && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <SidebarTrigger className="h-8 w-8" />
                </TooltipTrigger>
                <TooltipContent>Toggle sidebar (CMD+B)</TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent className="[&::-webkit-scrollbar]:hidden [-ms-overflow-style:'none'] [scrollbar-width:'none']">
        <SidebarGroup>
          <Link href="/dashboard">
            <SidebarMenuButton 
              className={cn('touch-manipulation mb-1', {
                'bg-accent text-accent-foreground font-medium': pathname === '/dashboard',
              })} 
              onClick={() => {
                posthog.capture('new_task_clicked');
                if (isMobile) setOpenMobile(false);
              }}
            >
              <Plus className="h-4 w-4 mr-1" />
              <span className="flex items-center justify-between w-full">
                New Mission
              </span>
            </SidebarMenuButton>
          </Link>
          {/* Tasks button temporarily hidden */}
          {/* <Link href="/tasks">
            <SidebarMenuButton 
              className={cn('touch-manipulation mt-1', {
                'bg-accent text-accent-foreground font-medium': pathname === '/tasks',
              })} 
              onClick={() => {
                if (isMobile) setOpenMobile(false);
              }}
            >
              <Zap className="h-4 w-4 mr-1" />
              <span className="flex items-center justify-between w-full">
                Tasks
              </span>
            </SidebarMenuButton>
          </Link> */}
          <SidebarMenu>
            <Collapsible
              defaultOpen={false}
              className="group/collapsible"
            >
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  <SidebarMenuButton
                    tooltip="Personalities"
                    onClick={() => {
                      if (state === 'collapsed') {
                        setOpen(true);
                      }
                    }}
                  >
                    <Bot className="h-4 w-4 mr-1" />
                    <span>Personalities</span>
                    <ChevronRight className="ml-auto transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    <SidebarMenuSubItem data-tour="my-agents">
                      <SidebarMenuSubButton className={cn('pl-3 touch-manipulation', {
                        'bg-accent text-accent-foreground font-medium': pathname === '/agents' && (searchParams.get('tab') === 'my-agents' || searchParams.get('tab') === null),
                      })} asChild>
                        <Link href="/agents?tab=my-agents" onClick={() => isMobile && setOpenMobile(false)}>
                          <span>My Added Personalities</span>
                        </Link>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                    <SidebarMenuSubItem data-tour="new-agent">
                      <SidebarMenuSubButton 
                        onClick={() => {
                          setShowNewAgentDialog(true);
                          if (isMobile) setOpenMobile(false);
                        }}
                        className="cursor-pointer pl-3 touch-manipulation"
                      >
                        <span>Create New Personality</span>
                      </SidebarMenuSubButton>
                    </SidebarMenuSubItem>
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          </SidebarMenu>
          
          {/* Search Button */}
          <Dialog open={showSearchDialog} onOpenChange={setShowSearchDialog}>
            <DialogTrigger asChild>
              <SidebarMenuButton
                className="touch-manipulation mt-1"
                onClick={() => {
                  if (isMobile) setOpenMobile(false);
                }}
              >
                <Search className="h-4 w-4 mr-1" />
                <span>Search</span>
              </SidebarMenuButton>
            </DialogTrigger>
            <DialogContent className="max-w-md mx-auto bg-transparent border-none shadow-none p-0 [&>button]:hidden">
              <DialogTitle className="sr-only">Search Feature Coming Soon</DialogTitle>
              <div className="relative rounded-3xl border border-white/10 bg-[rgba(10,14,22,0.55)] backdrop-blur-2xl shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.06)] overflow-hidden p-8 text-center">
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
                {/* Corner screws with close button on top right */}
                <div className="pointer-events-none" aria-hidden>
                  <div className="absolute left-3 top-3 h-1.5 w-1.5 rounded-full bg-white/30" />
                  <button 
                    onClick={() => setShowSearchDialog(false)}
                    className="absolute right-3 top-3 h-1.5 w-1.5 rounded-full bg-white/30 hover:bg-white/50 transition-colors cursor-pointer pointer-events-auto flex items-center justify-center"
                  >
                    <span className="text-white/80 text-[16px] leading-none">×</span>
                  </button>
                  <div className="absolute left-3 bottom-3 h-1.5 w-1.5 rounded-full bg-white/30" />
                  <div className="absolute right-3 bottom-3 h-1.5 w-1.5 rounded-full bg-white/30" />
                </div>
                
                <div className="relative z-10">
                  <div className="mb-4 flex items-center justify-center">
                    <div className="h-8 w-8 rounded-full bg-white/10 ring-1 ring-white/20 flex items-center justify-center">
                      <Search className="h-4 w-4 text-white/80" />
                    </div>
                  </div>
                  <h3 className="text-lg font-medium text-white/90 mb-2">Feature Coming Soon!</h3>
                  <p className="text-sm text-white/70">
                    Advanced search functionality is currently in development. Stay tuned for updates!
                  </p>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </SidebarGroup>
        <NavAgents />
      </SidebarContent>
      {/* Enterprise demo popup temporarily hidden */}
      {/* {state !== 'collapsed' && (
        <div className="px-3 py-2">
          <CTACard />
        </div>
      )} */}
      <SidebarFooter>
        {state === 'collapsed' && (
          <div className="mt-2 flex justify-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <SidebarTrigger className="h-8 w-8" />
              </TooltipTrigger>
              <TooltipContent>Expand sidebar (CMD+B)</TooltipContent>
            </Tooltip>
          </div>
        )}
        <NavUserWithTeams user={user} />
      </SidebarFooter>
      <SidebarRail />
      <NewAgentDialog 
        open={showNewAgentDialog} 
        onOpenChange={setShowNewAgentDialog}
      />
    </Sidebar>
  );
}

// Export the floating button so it can be used in the layout
export { FloatingMobileMenuButton };
