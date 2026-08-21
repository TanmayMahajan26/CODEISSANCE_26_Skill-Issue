import { ReactNode } from "react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

interface StatCardProps {
  title: string;
  amount: string;
  trend: "up" | "down";
  percentage: string;
  icon?: ReactNode;
  highlight?: boolean;
}

export function StatCard({ title, amount, trend, percentage, icon, highlight = false }: StatCardProps) {
  return (
    <div className={`rounded-3xl p-5 card-shadow flex flex-col justify-between h-full ${highlight ? 'accent-coral text-white' : 'bg-white'}`}>
      <div className="flex justify-between items-start">
        <p className={`text-sm font-medium ${highlight ? 'text-white/80' : 'text-gray-500'}`}>
          {title}
        </p>
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${highlight ? 'bg-white/20' : 'bg-gray-50 text-gray-600'}`}>
          {icon}
        </div>
      </div>
      
      <div>
        <h3 className={`text-3xl font-bold tracking-tight ${highlight ? 'text-white' : 'text-gray-900'}`}>
          {amount}
        </h3>
        <div className="flex items-center gap-2 mt-2">
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            trend === "up" 
              ? highlight ? 'bg-white/20 text-white' : 'bg-green-50 text-green-600'
              : highlight ? 'bg-white/20 text-white' : 'bg-red-50 text-red-600'
          }`}>
            {trend === "up" ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            <span>{percentage}</span>
          </div>
          <span className={`text-xs ${highlight ? 'text-white/80' : 'text-gray-400'}`}>vs last month</span>
        </div>
      </div>
    </div>
  );
}
