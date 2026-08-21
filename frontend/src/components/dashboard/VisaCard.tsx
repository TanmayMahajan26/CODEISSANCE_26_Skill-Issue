import { Plus } from "lucide-react";

export function VisaCard() {
  return (
    <div className="bg-gray-900 rounded-3xl p-6 text-white card-shadow flex flex-col justify-between min-h-[220px]">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-gray-400 text-sm font-medium">Linked Account</p>
          <div className="flex items-center gap-3 mt-2">
            <div className="w-10 h-6 bg-white/20 rounded flex items-center justify-center">
              <span className="text-xs font-bold text-white">VISA</span>
            </div>
            <p className="text-xl font-semibold tracking-wide">**** 8274</p>
          </div>
        </div>
        <div className="w-12 h-12 bg-gray-800 rounded-full flex items-center justify-center">
          <div className="w-3 h-3 bg-green-400 rounded-full"></div>
        </div>
      </div>
      
      <div className="flex gap-4 mt-6">
        <button className="flex-1 bg-white text-gray-900 py-3 rounded-2xl font-semibold text-sm hover:bg-gray-100 transition-colors">
          Manage
        </button>
        <button className="w-12 h-12 bg-gray-800 rounded-2xl flex items-center justify-center hover:bg-gray-700 transition-colors">
          <Plus size={20} />
        </button>
      </div>
    </div>
  );
}
