"use client";

import { LeftSidebar } from "./LeftSidebar";
import { TopNavigation } from "./TopNavigation";
import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { ProtectedRoute } from "./ProtectedRoute";

export function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Don't show layout on login page
  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <ProtectedRoute>
      <main className="w-full h-screen flex overflow-hidden relative bg-white">
        <LeftSidebar />
        <section className="flex-1 p-10 flex flex-col gap-8 overflow-y-auto bg-gray-50/50">
          <TopNavigation />
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
              className="flex-1 flex flex-col"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </section>
      </main>
    </ProtectedRoute>
  );
}
