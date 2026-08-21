"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StatCard } from "@/components/dashboard/StatCard";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { Wallet, Users, Link2, Briefcase, ClipboardCheck, Database, Shield, AlertTriangle, Activity } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await api.get("/dashboard/stats");
      return res.data;
    }
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-8 rounded-3xl text-white relative overflow-hidden">
        <div className="absolute -top-10 -right-10 w-60 h-60 bg-[#E2604B] opacity-10 rounded-full blur-3xl"></div>
        <div className="relative z-10">
          <p className="text-gray-400 text-sm font-medium">{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" })}</p>
          <h2 className="text-3xl font-bold mt-1">Welcome back, {user?.name || "User"}</h2>
          <p className="text-gray-400 mt-2 text-sm">{user?.role === "RM" ? "Your Customer Portfolio & Next-Best-Opportunities" : user?.role === "MANAGER" ? "Team Performance & Pipeline Review" : "System Overview & Identity Resolution Engine"}</p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E2604B]"></div>
        </div>
      ) : (
        <>
          {user?.role === "ADMIN" && <AdminDashboard stats={stats} />}
          {user?.role === "MANAGER" && <ManagerDashboard stats={stats} />}
          {user?.role === "RM" && <RMDashboard stats={stats} />}
        </>
      )}
    </div>
  );
}

function AdminDashboard({ stats }: { stats: any }) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="Source Records" amount={stats?.overview?.total_source_records?.toLocaleString() || "0"} trend="up" percentage="Ingested" icon={<Database size={18} />} />
          <StatCard title="Golden Records" amount={stats?.overview?.total_golden_records?.toLocaleString() || "0"} trend="up" percentage="Stitched" icon={<Users size={18} />} highlight={true} />
          <StatCard title="Identity Edges" amount={stats?.overview?.total_identity_edges?.toLocaleString() || "0"} trend="up" percentage="Links Found" icon={<Link2 size={18} />} />
          <StatCard title="Opportunities" amount={stats?.overview?.total_opportunities?.toLocaleString() || "0"} trend="up" percentage="Generated" icon={<Briefcase size={18} />} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-3xl card-shadow">
          <div className="flex items-center gap-2 mb-2">
            <Wallet size={18} className="text-gray-400" />
            <p className="text-sm font-medium text-gray-500">Total Relationship Value</p>
          </div>
          <h3 className="text-3xl font-bold text-gray-900">₹{(stats?.overview?.total_relationship_value || 0).toLocaleString()}</h3>
          <p className="text-xs text-gray-400 mt-1">Aggregated across all golden records</p>
        </div>
        
        <Link href="/review" className="bg-amber-50 border border-amber-100 p-6 rounded-3xl flex items-center gap-4 hover:border-amber-300 transition-colors group">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 flex items-center justify-center"><ClipboardCheck size={24} className="text-amber-600" /></div>
          <div>
            <p className="text-sm font-medium text-amber-800">Pending Reviews</p>
            <p className="text-2xl font-bold text-amber-900">{stats?.overview?.pending_reviews || 0}</p>
            <p className="text-xs text-amber-600 group-hover:underline">Click to review →</p>
          </div>
        </Link>

        <Link href="/identity-graph" className="bg-indigo-50 border border-indigo-100 p-6 rounded-3xl flex items-center gap-4 hover:border-indigo-300 transition-colors group">
          <div className="w-12 h-12 rounded-2xl bg-indigo-100 flex items-center justify-center"><Shield size={24} className="text-indigo-600" /></div>
          <div>
            <p className="text-sm font-medium text-indigo-800">Identity Graph</p>
            <p className="text-2xl font-bold text-indigo-900">{stats?.overview?.total_identity_edges || 0} edges</p>
            <p className="text-xs text-indigo-600 group-hover:underline">Visualize →</p>
          </div>
        </Link>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-72">
        <ChartCard title="Match Phase Distribution" data={stats?.edge_breakdown ? Object.entries(stats.edge_breakdown).map(([k, v]) => ({ name: k, value: v })) : []} />
        <ChartCard title="Opportunity Products" data={stats?.opportunity_by_product ? Object.entries(stats.opportunity_by_product).map(([k, v]) => ({ name: k.replace("_", " "), value: v })) : []} />
      </div>
    </>
  );
}

function ManagerDashboard({ stats }: { stats: any }) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="Team Customers" amount={stats?.overview?.total_golden_records?.toLocaleString() || "0"} trend="up" percentage="Assigned" icon={<Users size={18} />} highlight={true} />
          <StatCard title="Team Portfolio" amount={`₹${(stats?.overview?.total_relationship_value || 0).toLocaleString()}`} trend="up" percentage="Total AUM" icon={<Wallet size={18} />} />
          <StatCard title="Team Opportunities" amount={stats?.overview?.total_opportunities?.toLocaleString() || "0"} trend="up" percentage="Pipeline" icon={<Briefcase size={18} />} />
          <StatCard title="Pending Reviews" amount={stats?.overview?.pending_reviews?.toLocaleString() || "0"} trend="none" percentage="Action required" icon={<ClipboardCheck size={18} />} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link href="/review" className="bg-amber-50 border border-amber-100 p-6 rounded-3xl flex items-center gap-4 hover:border-amber-300 transition-colors group">
          <div className="w-12 h-12 rounded-2xl bg-amber-100 flex items-center justify-center"><ClipboardCheck size={24} className="text-amber-600" /></div>
          <div>
            <p className="text-sm font-medium text-amber-800">Team Queue</p>
            <p className="text-2xl font-bold text-amber-900">{stats?.overview?.pending_reviews || 0} items</p>
            <p className="text-xs text-amber-600 group-hover:underline">Review Now →</p>
          </div>
        </Link>
        <Link href="/opportunities" className="bg-blue-50 border border-blue-100 p-6 rounded-3xl flex items-center gap-4 hover:border-blue-300 transition-colors group">
          <div className="w-12 h-12 rounded-2xl bg-blue-100 flex items-center justify-center"><Briefcase size={24} className="text-blue-600" /></div>
          <div>
            <p className="text-sm font-medium text-blue-800">Team Funnel</p>
            <p className="text-2xl font-bold text-blue-900">{stats?.overview?.total_opportunities || 0} active</p>
            <p className="text-xs text-blue-600 group-hover:underline">View Pipeline →</p>
          </div>
        </Link>
        <Link href="/customers" className="bg-green-50 border border-green-100 p-6 rounded-3xl flex items-center gap-4 hover:border-green-300 transition-colors group">
          <div className="w-12 h-12 rounded-2xl bg-green-100 flex items-center justify-center"><Users size={24} className="text-green-600" /></div>
          <div>
            <p className="text-sm font-medium text-green-800">Team Clients</p>
            <p className="text-2xl font-bold text-green-900">{stats?.overview?.total_golden_records || 0} clients</p>
            <p className="text-xs text-green-600 group-hover:underline">View All →</p>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-72">
        <ChartCard title="Team Opportunity Funnel" data={stats?.opportunity_by_status ? Object.entries(stats.opportunity_by_status).map(([k, v]) => ({ name: k.replace("_", " "), value: v })) : []} />
        <ChartCard title="Team Products" data={stats?.opportunity_by_product ? Object.entries(stats.opportunity_by_product).map(([k, v]) => ({ name: k.replace("_", " "), value: v })) : []} />
      </div>
    </>
  );
}

function RMDashboard({ stats }: { stats: any }) {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        <div className="md:col-span-12 grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard title="My Customers" amount={stats?.overview?.total_golden_records?.toLocaleString() || "0"} trend="up" percentage="Assigned" icon={<Users size={18} />} highlight={true} />
          <StatCard title="My Portfolio" amount={`₹${(stats?.overview?.total_relationship_value || 0).toLocaleString()}`} trend="up" percentage="Total TRV" icon={<Wallet size={18} />} />
          <StatCard title="My Opportunities" amount={stats?.overview?.total_opportunities?.toLocaleString() || "0"} trend="up" percentage="To follow up" icon={<Briefcase size={18} />} />
          <StatCard title="Recent Activity" amount={stats?.overview?.total_identity_edges?.toLocaleString() || "0"} trend="up" percentage="Interactions" icon={<Activity size={18} />} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Link href="/opportunities" className="bg-blue-50 border border-blue-100 p-8 rounded-3xl flex items-center gap-6 hover:border-blue-300 transition-colors group">
          <div className="w-16 h-16 rounded-2xl bg-blue-100 flex items-center justify-center"><Briefcase size={32} className="text-blue-600" /></div>
          <div>
            <p className="text-lg font-medium text-blue-800">Action Follow-ups</p>
            <p className="text-4xl font-bold text-blue-900 mt-1">{stats?.overview?.total_opportunities || 0}</p>
            <p className="text-sm text-blue-600 mt-2 font-medium group-hover:underline">Start engaging your assigned leads →</p>
          </div>
        </Link>
        <Link href="/customers" className="bg-green-50 border border-green-100 p-8 rounded-3xl flex items-center gap-6 hover:border-green-300 transition-colors group">
          <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center"><Users size={32} className="text-green-600" /></div>
          <div>
            <p className="text-lg font-medium text-green-800">Client Portfolio</p>
            <p className="text-4xl font-bold text-green-900 mt-1">{stats?.overview?.total_golden_records || 0}</p>
            <p className="text-sm text-green-600 mt-2 font-medium group-hover:underline">Review your 360° client views →</p>
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-72">
        <ChartCard title="My Pipeline Status" data={stats?.opportunity_by_status ? Object.entries(stats.opportunity_by_status).map(([k, v]) => ({ name: k, value: v })) : []} />
        <ChartCard title="My Opportunity Types" data={stats?.opportunity_by_product ? Object.entries(stats.opportunity_by_product).map(([k, v]) => ({ name: k.replace("_", " "), value: v })) : []} />
      </div>
    </>
  );
}
