"use client";

import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";

const noShellRoutes = ["/onboarding", "/login"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideShell = noShellRoutes.some((r) => pathname.startsWith(r));

  if (hideShell) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#F7F7F4]">
      <Sidebar />
      <main className="flex-1 overflow-y-auto animate-fade-in">{children}</main>
    </div>
  );
}
