import { ThemeProvider } from '@/components/home/theme-provider';
import { siteConfig } from '@/lib/site';
import type { Metadata, Viewport } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { Toaster } from '@/components/ui/sonner';
import { GoogleAnalytics } from '@next/third-parties/google';
import Script from 'next/script';
import { PostHogIdentify } from '@/components/posthog-identify';
import { ErrorBoundary } from '@/components/error-boundary';
import { setupGlobalErrorHandlers } from '@/lib/debug-errors';
import '@/lib/polyfills'; // Load polyfills early

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const viewport: Viewport = {
  themeColor: 'black',
};

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: siteConfig.name,
    template: `%s - ${siteConfig.name}`,
  },
  description:
    'Kortix is a fully open source AI assistant that helps you accomplish real-world tasks with ease. Through natural conversation, Kortix becomes your digital companion for research, data analysis, and everyday challenges.',
  keywords: [
    'AI',
    'artificial intelligence',
    'browser automation',
    'web scraping',
    'file management',
    'AI assistant',
    'open source',
    'research',
    'data analysis',
  ],
  authors: [{ name: 'Kortix Team', url: 'https://suna.so' }],
  creator:
    'Kortix Team',
  publisher:
    'Kortix Team',
  category: 'Technology',
  applicationName: 'Iris',
  formatDetection: {
    telephone: false,
    email: false,
    address: false,
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
  openGraph: {
    title: 'Iris - Open Source Generalist AI Worker',
    description:
      'Iris is a fully open source AI assistant that helps you accomplish real-world tasks with ease through natural conversation.',
    url: siteConfig.url,
    siteName: 'Iris',
    images: [
      {
        url: '/banner.png',
        width: 1200,
        height: 630,
        alt: 'Iris - Open Source Generalist AI Worker',
        type: 'image/png',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Iris - Open Source Generalist AI Worker',
    description:
      'Iris is a fully open source AI assistant that helps you accomplish real-world tasks with ease through natural conversation.',
    creator: '@kortixai',
    site: '@kortixai',
    images: [
      {
        url: '/banner.png',
        width: 1200,
        height: 630,
        alt: 'Iris - Open Source Generalist AI Worker',
      },
    ],
  },
  icons: {
    icon: [{ url: '/iris-symbol.png', sizes: 'any' }],
    shortcut: '/iris-symbol.png',
  },
  // manifest: "/manifest.json",
  alternates: {
    canonical: siteConfig.url,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Google Tag Manager */}
        <Script id="google-tag-manager" strategy="afterInteractive">
          {`(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
          new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
          j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
          'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
          })(window,document,'script','dataLayer','GTM-PCHSN4M2');`}
        </Script>
        <Script async src="https://cdn.tolt.io/tolt.js" data-tolt={process.env.NEXT_PUBLIC_TOLT_REFERRAL_ID}></Script>
        <Script id="setup-error-handlers" strategy="beforeInteractive">
          {`
            // Setup global error handlers
            window.addEventListener('unhandledrejection', (event) => {
              console.group('🚨 Unhandled Promise Rejection');
              console.error('Reason:', event.reason);
              console.error('Promise:', event.promise);
              console.groupEnd();
              event.preventDefault();
            });

            window.addEventListener('error', (event) => {
              console.group('🚨 Uncaught Error');
              console.error('Message:', event.message);
              console.error('Source:', event.filename);
              console.error('Line:', event.lineno);
              console.error('Column:', event.colno);
              console.error('Error:', event.error);
              console.groupEnd();
            });
          `}
        </Script>
      </head>

      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased font-sans bg-background`}
        suppressHydrationWarning
      >
        <noscript>
          <iframe
            src="https://www.googletagmanager.com/ns.html?id=GTM-PCHSN4M2"
            height="0"
            width="0"
            style={{ display: 'none', visibility: 'hidden' }}
          />
        </noscript>
        {/* End Google Tag Manager (noscript) */}

        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <ErrorBoundary>
            <Providers>
              {children}
              <Toaster />
            </Providers>
            <GoogleAnalytics gaId="G-6ETJFB3PT3" />
            <PostHogIdentify />
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}
