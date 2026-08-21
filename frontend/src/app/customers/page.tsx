"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { Search, ChevronRight, User, Mail, Phone } from "lucide-react";
import Link from "next/link";

export default function CustomersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  
  // In a real app we might pass search queries to backend, 
  // but let's fetch all and filter in UI for now if backend doesn't support search param easily
  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers"],
    queryFn: async () => {
      const res = await api.get("/resolution/golden-records");
      return res.data;
    }
  });

  const filteredCustomers = customers?.filter((c: any) => 
    (c.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    String(c.id).includes(searchTerm)
  ) || [];

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Customer Search</h2>
          <p className="text-gray-500 text-sm mt-1">Find and view golden records</p>
        </div>
        <div className="relative w-96">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-gray-50 border-none rounded-2xl focus:ring-2 focus:ring-[#E2604B] text-sm"
            placeholder="Search by name or ID..."
          />
        </div>
      </div>

      <div className="flex-1 bg-white rounded-3xl p-2 card-shadow overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E2604B]"></div>
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                <th className="p-4 pl-6">Customer Name</th>
                <th className="p-4">Golden ID</th>
                <th className="p-4">Contact Info</th>
                <th className="p-4">Business KPIs</th>
                <th className="p-4">Confidence</th>
                <th className="p-4">Sources</th>
                <th className="p-4"></th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((c: any) => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors group cursor-pointer">
                  <td className="p-4 pl-6">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-500">
                        <User size={18} />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-900">{c.name || "Unknown Customer"}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 font-mono text-xs text-gray-500">G-00{c.id}</td>
                  <td className="p-4">
                    <div className="flex flex-col gap-1 text-xs text-gray-600">
                      {c.email && <div className="flex items-center gap-1"><Mail size={12}/>{c.email}</div>}
                      {c.mobile && <div className="flex items-center gap-1"><Phone size={12}/>{c.mobile}</div>}
                      {!c.email && !c.mobile && <span className="text-gray-400">—</span>}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-col gap-1">
                      <span className="font-semibold text-gray-900">₹{(c.total_relationship_value || 0).toLocaleString()}</span>
                      <span className="text-xs text-gray-500 truncate max-w-[150px]" title={(c.products_held || []).join(", ")}>
                        {(c.products_held || []).join(", ") || "No Products"}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="px-3 py-1 bg-green-50 text-green-700 rounded-full text-xs font-bold">
                      {Math.round((c.match_confidence || 0.95) * 100)}%
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex -space-x-2">
                      {[...Array(c.source_record_count || 2)].map((_, i) => (
                        <div key={i} className="w-8 h-8 rounded-full bg-blue-100 border-2 border-white flex items-center justify-center text-xs font-bold text-blue-800">
                          S{i+1}
                        </div>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 text-right pr-6">
                    <Link href={`/customers/${c.id}`}>
                      <button className="text-[#E2604B] font-medium text-sm flex items-center justify-end w-full gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        View 360 <ChevronRight size={16} />
                      </button>
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredCustomers.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-gray-500">
                    No customers found matching your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
