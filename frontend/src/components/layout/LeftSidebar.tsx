"use client";

import { LayoutDashboard, Users, Briefcase, Settings, FileText, Network, ClipboardCheck, MessageSquare } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/auth";

const NAV_ITEMS = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard", allowedRoles: ["ADMIN", "MANAGER", "RM"] },
  { href: "/customers", icon: Users, label: "Customers", allowedRoles: ["ADMIN", "MANAGER", "RM"] },
  { href: "/identity-graph", icon: Network, label: "Graph", allowedRoles: ["ADMIN", "MANAGER", "RM"] },
  { href: "/opportunities", icon: Briefcase, label: "Opportunities", allowedRoles: ["ADMIN", "MANAGER", "RM"] },
  { href: "/review", icon: ClipboardCheck, label: "Review", allowedRoles: ["ADMIN", "MANAGER"] },
  { href: "/ask", icon: MessageSquare, label: "Ask AI", allowedRoles: ["ADMIN", "MANAGER", "RM"] },
  { href: "/demo", icon: LayoutDashboard, label: "Demo", allowedRoles: ["ADMIN"] },
  { href: "/config", icon: Settings, label: "Config", allowedRoles: ["ADMIN"] },
  { href: "/audit", icon: FileText, label: "Audit", allowedRoles: ["ADMIN"] },
];

export function LeftSidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();

  return (
    <aside className="w-20 border-r border-gray-100 flex flex-col items-center py-8 gap-1 z-10 bg-white shrink-0">
      <div className="w-11 h-11 bg-black text-white rounded-full flex items-center justify-center font-bold text-lg mb-6 tracking-tighter">
        KV
      </div>
      
      <div className="flex-1 flex flex-col gap-1 items-center w-full px-2">
        {NAV_ITEMS.map(({ href, icon: Icon, label, allowedRoles }) => {
          if (user?.role && !allowedRoles.includes(user.role)) return null;

          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`w-full flex flex-col items-center gap-1 py-2.5 rounded-xl transition-all text-center
                ${isActive 
                  ? "bg-orange-50 text-[#E2604B]" 
                  : "text-gray-400 hover:bg-gray-50 hover:text-gray-600"
                }`}
            >
              <Icon size={18} strokeWidth={isActive ? 2.5 : 1.8} />
              <span className="text-[10px] font-medium leading-tight">{label}</span>
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
