import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { CategorySpending } from '../../types';

interface SpendingDonutChartProps {
  data: CategorySpending[];
  title?: string;
}

export const SpendingDonutChart: React.FC<SpendingDonutChartProps> = ({
  data,
  title = "Monthly Category Distribution",
}) => {
  const totalAmount = data.reduce((sum, item) => sum + item.amount, 0);

  return (
    <div className="w-full bg-[#0D1222]/95 border border-slate-700/60 border-t-white/10 rounded-2xl p-3.5 my-1.5 backdrop-blur-md shadow-panel ring-1 ring-inset ring-white/[0.04] transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-800/70">
        <h4 className="text-xs font-bold text-slate-200 tracking-wide flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
          {title}
        </h4>
        <span className="text-[11px] font-mono font-bold text-purple-300 bg-purple-500/15 px-2.5 py-0.5 rounded-full border border-purple-500/30">
          Total: ₹{totalAmount.toLocaleString('en-IN')}
        </span>
      </div>

      {/* Side-by-Side: Donut on Left, Compact Legend & Values on Right */}
      <div className="grid grid-cols-12 gap-3 items-center">
        {/* Left: Recharts Donut */}
        <div className="col-span-5 relative w-full h-[140px] flex items-center justify-center">
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0].payload as CategorySpending;
                    return (
                      <div className="bg-[#141A2D] border border-purple-500/40 px-2.5 py-1 rounded-lg shadow-xl text-xs backdrop-blur-md">
                        <p className="font-semibold text-white">{item.name}</p>
                        <p className="text-purple-300 font-mono text-[10px]">
                          ₹{item.amount.toLocaleString('en-IN')} ({item.percentage}%)
                        </p>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={36}
                outerRadius={58}
                paddingAngle={3}
                dataKey="amount"
                stroke="#0D1222"
                strokeWidth={2}
                isAnimationActive={false} // Prevents headless timing glitch
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.color}
                    className="hover:opacity-80 cursor-pointer"
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          {/* Center Donut Amount Text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-[8px] uppercase font-bold text-slate-400 tracking-wider">
              Total
            </span>
            <span className="text-xs font-extrabold text-white font-mono leading-none mt-0.5">
              ₹{(totalAmount / 1000).toFixed(0)}k
            </span>
          </div>
        </div>

        {/* Right: Category Legend with Segment Progress Bars */}
        <div className="col-span-7 flex flex-col justify-center space-y-1.5 pl-1">
          {data.map((item) => (
            <div key={item.name} className="flex flex-col text-[11px] group">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 truncate">
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-slate-300 truncate font-medium group-hover:text-white transition-colors">
                    {item.name}
                  </span>
                </div>
                <span className="font-mono font-semibold text-slate-200 ml-1">
                  ₹{item.amount.toLocaleString('en-IN')}
                </span>
              </div>
              {/* Category percentage bar */}
              <div className="w-full h-1 bg-slate-800 rounded-full mt-0.5 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${item.percentage}%`,
                    backgroundColor: item.color,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
