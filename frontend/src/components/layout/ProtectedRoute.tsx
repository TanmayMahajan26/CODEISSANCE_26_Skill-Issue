"use client";

import { useAuthStore } from "@/stores/auth";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, token } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!token && pathname !== "/login") {
      router.push("/login");
    }
  }, [token, pathname, router]);

  if (!token && pathname !== "/login") {
    return (
      <div className="w-full h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-gray-400" size={40} />
      </div>
    );
  }

  return <>{children}</>;
}
