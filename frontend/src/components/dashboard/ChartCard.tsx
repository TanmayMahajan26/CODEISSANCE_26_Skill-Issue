"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, CartesianGrid } from "recharts";

export function ChartCard({ title, data }: { title: string, data: any[] }) {
  // Use fallback data if empty to prevent visual bugs in the UI demo
  const displayData = data?.length > 0 ? data : [
    { name: "No Data", value: 0 }
  ];

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl p-6 card-shadow flex flex-col justify-between h-full border border-white">
      <div className="flex justify-between items-center mb-6">
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      <div className="flex-1 w-full min-h-[150px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={displayData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
            <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6B7280' }} />
            <Tooltip
              contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 20px rgba(0,0,0,0.08)" }}
              cursor={{ fill: '#F3F4F6' }}
            />
            <Bar
              dataKey="value"
              fill="#E2604B"
              radius={[4, 4, 0, 0]}
              barSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
