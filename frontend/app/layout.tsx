import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Manak-SpecEngine | Bureau of Indian Standards AI Recommendation & Compliance Engine",
  description: "Enterprise-grade AI recommendation and compliance verification engine for Indian Standards (BIS) and statutory Quality Control Orders (QCOs) in public procurement.",
  keywords: ["BIS", "Indian Standards", "GeM", "QCO", "Public Procurement", "CPWD", "IS 2062", "IS 1786"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
