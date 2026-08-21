export function HeroSection() {
  const currentDate = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <div className="flex justify-between items-center bg-white p-6 rounded-3xl card-shadow">
      <div>
        <p className="text-gray-500 text-sm font-medium">{currentDate}</p>
        <h2 className="text-3xl font-semibold text-gray-900 mt-1">Hey, Need help? 👋</h2>
      </div>
      <button className="accent-coral text-white px-6 py-3 rounded-2xl font-medium shadow-lg hover:opacity-90 transition-opacity">
        Just ask me anything!
      </button>
    </div>
  );
}
