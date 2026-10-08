import type { Metadata } from "next";
import "./globals.css";
import SiteShell from "./components/SiteShell";
export const metadata: Metadata = { title: "Arena | Tournament Intelligence", description: "Game tournament management and data structures learning dashboard" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
 return <html lang="en"><body><SiteShell>{children}</SiteShell></body></html>;
}
