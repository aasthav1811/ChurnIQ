import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ChurnIQ — Retention Intelligence",
  description: "Predict churn, explain why, act fast.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen">{children}</body>
    </html>
  );
}