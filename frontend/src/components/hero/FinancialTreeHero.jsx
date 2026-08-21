import React, { useEffect, useRef, useState } from 'react';
import { Landmark, TrendingUp, PieChart, ShieldCheck, CheckCircle2 } from 'lucide-react';

export function FinancialTreeHero({ onExplore }) {
  const canvasRef = useRef(null);
  const [activeBranch, setActiveBranch] = useState(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio || 600);
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio || 500);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio || 600;
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio || 500;
    };
    window.addEventListener('resize', handleResize);

    // Particle ecosystem: Gold coins and data tokens flowing from the 4 sources into the Golden Tree
    const particles = [];
    const sourcePoints = [
      { x: width * 0.18, y: height * 0.28, label: 'Banking', color: '#10B981' },
      { x: width * 0.38, y: height * 0.16, label: 'Equity', color: '#3B82F6' },
      { x: width * 0.62, y: height * 0.16, label: 'Mutual Funds', color: '#F59E0B' },
      { x: width * 0.82, y: height * 0.28, label: 'Insurance', color: '#059669' },
    ];
    const trunkCenter = { x: width * 0.5, y: height * 0.62 };

    class ValueParticle {
      constructor() {
        this.reset();
      }

      reset() {
        this.sourceIndex = Math.floor(Math.random() * 4);
        const src = sourcePoints[this.sourceIndex];
        this.x = src.x + (Math.random() * 20 - 10);
        this.y = src.y + (Math.random() * 20 - 10);
        this.targetX = trunkCenter.x + (Math.random() * 24 - 12);
        this.targetY = trunkCenter.y + (Math.random() * 40 - 20);
        this.progress = 0;
        this.speed = 0.006 + Math.random() * 0.008;
        this.size = 2.5 + Math.random() * 3;
        this.isCoin = Math.random() > 0.4;
        this.opacity = 0.2 + Math.random() * 0.7;
        this.color = this.isCoin ? '#F59E0B' : '#10B981';
      }

      update() {
        this.progress += this.speed;
        if (this.progress >= 1) {
          this.reset();
        }
      }

      draw() {
        const t = this.progress;
        // Bezier curve flow toward trunk
        const src = sourcePoints[this.sourceIndex];
        const controlX = (src.x + this.targetX) / 2 + (this.sourceIndex < 2 ? -25 : 25);
        const controlY = src.y + (this.targetY - src.y) * 0.65;

        const currentX = (1 - t) * (1 - t) * src.x + 2 * (1 - t) * t * controlX + t * t * this.targetX;
        const currentY = (1 - t) * (1 - t) * src.y + 2 * (1 - t) * t * controlY + t * t * this.targetY;

        ctx.save();
        ctx.globalAlpha = Math.sin(t * Math.PI) * this.opacity;

        if (this.isCoin) {
          // Subtle Gold Token / Coin
          ctx.beginPath();
          ctx.arc(currentX, currentY, this.size, 0, Math.PI * 2);
          ctx.fillStyle = '#FBBF24';
          ctx.fill();
          ctx.lineWidth = 1;
          ctx.strokeStyle = '#D97706';
          ctx.stroke();

          // Small ₹ symbol if large enough
          if (this.size > 4) {
            ctx.fillStyle = '#78350F';
            ctx.font = `${this.size}px sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('₹', currentX, currentY);
          }
        } else {
          // Data Token
          ctx.beginPath();
          ctx.arc(currentX, currentY, this.size * 0.8, 0, Math.PI * 2);
          ctx.fillStyle = '#34D399';
          ctx.fill();
        }
        ctx.restore();
      }
    }

    for (let i = 0; i < 40; i++) {
      const p = new ValueParticle();
      p.progress = Math.random();
      particles.push(p);
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw subtle connecting branch lines (flow conduits)
      sourcePoints.forEach((src, idx) => {
        const controlX = (src.x + trunkCenter.x) / 2 + (idx < 2 ? -25 : 25);
        const controlY = src.y + (trunkCenter.y - src.y) * 0.65;

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.quadraticCurveTo(controlX, controlY, trunkCenter.x, trunkCenter.y);
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.15)';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([4, 6]);
        ctx.stroke();
        ctx.setLineDash([]);
      });

      // Update & draw particles
      particles.forEach((p) => {
        p.update();
        p.draw();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="relative w-full max-w-5xl mx-auto flex flex-col items-center justify-center select-none">
      {/* Background Soft Glow */}
      <div className="absolute -top-12 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Floating Relationship Growth Card (Top Right) */}
      <div className="absolute top-2 right-4 md:right-12 z-20 bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl p-4 shadow-card hover:shadow-card-hover transition-all duration-300 transform hover:-translate-y-1 max-w-[210px]">
        <div className="flex items-center justify-between text-xs text-slate-500 font-medium mb-1">
          <span>Relationship Growth</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        </div>
        <div className="text-2xl font-bold text-slate-900 tracking-tight flex items-baseline gap-1">
          +24.8%
          <span className="text-[11px] font-medium text-emerald-600">▲</span>
        </div>
        <div className="text-[11px] text-slate-400 mt-0.5">vs last quarter</div>

        {/* Clean Mini Sparkline SVG */}
        <div className="mt-2 pt-2 border-t border-slate-100">
          <svg viewBox="0 0 120 28" className="w-full h-7 overflow-visible">
            <defs>
              <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#10B981" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M 0 22 Q 25 20, 45 14 T 80 10 T 115 3 L 115 28 L 0 28 Z"
              fill="url(#growthGradient)"
            />
            <path
              d="M 0 22 Q 25 20, 45 14 T 80 10 T 115 3"
              fill="none"
              stroke="#059669"
              strokeWidth="2.2"
              strokeLinecap="round"
            />
            <circle cx="115" cy="3" r="3" fill="#059669" />
          </svg>
        </div>
      </div>

      {/* Main Canvas & Interactive Visual Tree */}
      <div className="relative w-full h-[380px] md:h-[460px] flex items-center justify-center">
        {/* Animated Particle Canvas */}
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full pointer-events-none z-10"
        />

        {/* 4 Financial Domain Source Nodes */}
        <div className="absolute inset-0 flex items-start justify-between px-2 md:px-10 pt-4 z-20 pointer-events-auto">
          {/* 1. Banking */}
          <div
            onMouseEnter={() => setActiveBranch('banking')}
            onMouseLeave={() => setActiveBranch(null)}
            className="flex flex-col items-center group cursor-pointer transition-all duration-300"
          >
            <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-white border border-slate-200/90 shadow-card flex items-center justify-center group-hover:scale-105 group-hover:border-emerald-500 group-hover:shadow-emerald-glow transition-all">
              <Landmark className="w-6 h-6 text-emerald-600 group-hover:scale-110 transition-transform" />
            </div>
            <span className="mt-2 text-xs md:text-sm font-semibold text-slate-800 tracking-tight">Banking</span>
            <span className="text-[11px] text-slate-400 font-medium">2.4M Records</span>
          </div>

          {/* 2. Equity */}
          <div
            onMouseEnter={() => setActiveBranch('equity')}
            onMouseLeave={() => setActiveBranch(null)}
            className="flex flex-col items-center group cursor-pointer transition-all duration-300"
          >
            <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-white border border-slate-200/90 shadow-card flex items-center justify-center group-hover:scale-105 group-hover:border-blue-500 group-hover:shadow-card-hover transition-all">
              <TrendingUp className="w-6 h-6 text-blue-600 group-hover:scale-110 transition-transform" />
            </div>
            <span className="mt-2 text-xs md:text-sm font-semibold text-slate-800 tracking-tight">Equity</span>
            <span className="text-[11px] text-slate-400 font-medium">1.8M Records</span>
          </div>

          {/* 3. Mutual Funds */}
          <div
            onMouseEnter={() => setActiveBranch('mf')}
            onMouseLeave={() => setActiveBranch(null)}
            className="flex flex-col items-center group cursor-pointer transition-all duration-300"
          >
            <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-white border border-slate-200/90 shadow-card flex items-center justify-center group-hover:scale-105 group-hover:border-amber-500 group-hover:shadow-card-hover transition-all">
              <PieChart className="w-6 h-6 text-amber-500 group-hover:scale-110 transition-transform" />
            </div>
            <span className="mt-2 text-xs md:text-sm font-semibold text-slate-800 tracking-tight">Mutual Funds</span>
            <span className="text-[11px] text-slate-400 font-medium">1.2M Records</span>
          </div>

          {/* 4. Insurance */}
          <div
            onMouseEnter={() => setActiveBranch('insurance')}
            onMouseLeave={() => setActiveBranch(null)}
            className="flex flex-col items-center group cursor-pointer transition-all duration-300"
          >
            <div className="w-12 h-12 md:w-14 md:h-14 rounded-2xl bg-white border border-slate-200/90 shadow-card flex items-center justify-center group-hover:scale-105 group-hover:border-emerald-500 group-hover:shadow-card-hover transition-all">
              <ShieldCheck className="w-6 h-6 text-emerald-700 group-hover:scale-110 transition-transform" />
            </div>
            <span className="mt-2 text-xs md:text-sm font-semibold text-slate-800 tracking-tight">Insurance</span>
            <span className="text-[11px] text-slate-400 font-medium">900K Records</span>
          </div>
        </div>

        {/* Central Financial Plant / Golden Customer Tree Graphic */}
        <div className="relative z-10 flex flex-col items-center justify-center mt-12">
          {/* Subtle Growth Tree SVG */}
          <svg width="220" height="240" viewBox="0 0 220 240" fill="none" className="filter drop-shadow-sm">
            {/* Trunk */}
            <path
              d="M110 200 C110 160, 95 130, 90 90 C95 120, 110 150, 110 200 Z"
              fill="#065F46"
            />
            <path
              d="M110 200 C110 150, 125 120, 130 90 C125 130, 110 160, 110 200 Z"
              fill="#047857"
            />
            <path
              d="M106 200 L114 200 L112 110 L108 110 Z"
              fill="#064E3B"
            />

            {/* Leaves & Branches */}
            <g className="animate-pulse-subtle">
              {/* Top Central Leaf */}
              <path d="M110 40 C95 55, 95 80, 110 95 C125 80, 125 55, 110 40 Z" fill="#10B981" />
              <path d="M110 40 C102 55, 105 80, 110 95" stroke="#059669" strokeWidth="1.5" />

              {/* Left Main Leaf */}
              <path d="M85 70 C65 72, 60 95, 80 105 C95 98, 98 80, 85 70 Z" fill="#34D399" />
              {/* Right Main Leaf */}
              <path d="M135 70 C155 72, 160 95, 140 105 C125 98, 122 80, 135 70 Z" fill="#059669" />

              {/* Left Higher Leaf */}
              <path d="M92 50 C76 48, 72 65, 88 74 C100 68, 102 56, 92 50 Z" fill="#6EE7B7" />
              {/* Right Higher Leaf */}
              <path d="M128 50 C144 48, 148 65, 132 74 C120 68, 118 56, 128 50 Z" fill="#10B981" />
            </g>

            {/* Golden Value Fruits / Badges on the tree */}
            <circle cx="110" cy="65" r="9" fill="#FBBF24" stroke="#D97706" strokeWidth="1.5" />
            <text x="110" y="69" fontSize="10" fontWeight="bold" fill="#78350F" textAnchor="middle">₹</text>

            <circle cx="78" cy="85" r="7.5" fill="#FBBF24" stroke="#D97706" strokeWidth="1.5" />
            <text x="78" y="89" fontSize="9" fontWeight="bold" fill="#78350F" textAnchor="middle">₹</text>

            <circle cx="142" cy="85" r="7.5" fill="#FBBF24" stroke="#D97706" strokeWidth="1.5" />
            <text x="142" y="89" fontSize="9" fontWeight="bold" fill="#78350F" textAnchor="middle">₹</text>

            {/* Stable Ceramic Foundation Pot */}
            <ellipse cx="110" cy="195" rx="55" ry="12" fill="#E2E8F0" />
            <path
              d="M60 195 L72 230 C74 236, 146 236, 148 230 L160 195 Z"
              fill="#FFFFFF"
              stroke="#CBD5E1"
              strokeWidth="1.5"
            />
            {/* Soil */}
            <ellipse cx="110" cy="196" rx="46" ry="7" fill="#334155" />

            {/* Pile of Gold Coins around base */}
            <ellipse cx="90" cy="228" rx="14" ry="5" fill="#F59E0B" stroke="#D97706" strokeWidth="1" />
            <ellipse cx="130" cy="230" rx="15" ry="5.5" fill="#FBBF24" stroke="#D97706" strokeWidth="1" />
            <ellipse cx="110" cy="232" rx="16" ry="6" fill="#F59E0B" stroke="#B45309" strokeWidth="1" />
          </svg>

          {/* Golden Customer Unified Identity Pill */}
          <div className="mt-2 bg-navy-900 text-white px-5 py-2.5 rounded-full shadow-card flex items-center gap-2.5 border border-slate-700/60 transition-transform hover:scale-105">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-xs md:text-sm font-semibold tracking-wide">
              Unified Golden Customer: <span className="text-emerald-400 font-mono">GOLD-000101</span>
            </span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-1" />
          </div>
        </div>
      </div>
    </div>
  );
}
