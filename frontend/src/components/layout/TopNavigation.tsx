"use client";

import { Plus, Search } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { useRouter, usePathname } from "next/navigation";

export function TopNavigation() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  // Determine a nice title based on the path
  let title = "Financial";
  let subtitle = "Dashboard";

  if (pathname.includes("/customers")) {
    title = "Customer";
    subtitle = "360 View";
  } else if (pathname.includes("/opportunities")) {
    title = "Next Best";
    subtitle = "Opportunities";
  } else if (pathname.includes("/review")) {
    title = "Identity";
    subtitle = "Review Queue";
  } else if (pathname.includes("/config")) {
    title = "System";
    subtitle = "Configuration";
  } else if (pathname.includes("/audit")) {
    title = "Audit";
    subtitle = "Logs";
  }

  return (
    <header className="flex justify-between items-center w-full shrink-0">
      {/* Logo Area */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-black text-white rounded-full flex items-center justify-center font-bold text-xl tracking-tighter">
          KV
        </div>
        <div>
          <h1 className="font-semibold text-gray-900 leading-tight">{title}</h1>
          <p className="text-gray-400 text-sm">{subtitle}</p>
        </div>
      </div>
      
      {/* User & Search */}
      <div className="flex items-center gap-6">
        <button className="w-10 h-10 rounded-full border border-gray-200 flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-colors">
          <Plus size={16} strokeWidth={2} />
        </button>
        <button 
          onClick={() => { logout(); router.push('/login'); }}
          className="text-xs font-semibold text-gray-500 hover:text-[#E2604B] transition-colors uppercase tracking-wider"
        >
          Logout
        </button>
        
        <div className="flex items-center gap-3 pr-6 border-r border-gray-200">
          {/* We use a placeholder avatar based on role or a default image */}
          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-sm font-bold text-gray-600">
            {user?.username ? user.username.substring(0, 2).toUpperCase() : "U"}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">{user?.username || "Guest"}</p>
            <p className="text-xs text-gray-500">{user?.role || "Viewer"}</p>
          </div>
        </div>
        
        <div className="relative">
          <Search size={16} strokeWidth={2} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            className="pl-10 pr-4 py-2 bg-transparent border-none focus:ring-0 text-sm w-64 placeholder-gray-400 focus:outline-none" 
            placeholder="Start searching here..." 
            type="text" 
          />
        </div>
      </div>
    </header>
  );
}
