"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import AgentStatus from "./AgentStatus";
import { useAuth } from "./AuthProvider";

const navItems = [
  { href: "/", label: "Dashboard", icon: "D" },
  { href: "/people", label: "People", icon: "P" },
  { href: "/messages", label: "Messages", icon: "M" },
  { href: "/targets", label: "Targets", icon: "T" },
  { href: "/settings", label: "Settings", icon: "S" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-gray-800 bg-gray-950">
      <div className="flex h-14 items-center gap-2 border-b border-gray-800 px-4">
        <span className="text-lg font-bold tracking-tight text-indigo-400">
          NEXUS
        </span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                active
                  ? "bg-indigo-600/20 text-indigo-400"
                  : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
              }`}
            >
              <span className="flex h-6 w-6 items-center justify-center rounded bg-gray-800 text-xs font-bold">
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-gray-800 p-4">
        <AgentStatus />
      </div>
      {user && (
        <div className="border-t border-gray-800 p-4">
          <p className="truncate text-xs text-gray-500">{user.email}</p>
          <button
            onClick={logout}
            className="mt-2 w-full rounded px-3 py-1.5 text-xs text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
          >
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}
