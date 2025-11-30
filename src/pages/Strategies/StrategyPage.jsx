import React, { useState } from 'react';
import { Play, Square, Settings } from 'lucide-react';

const strategiesData = [
  { id: 1, name: 'Grid Trading', description: 'Places buy/sell orders at intervals.', status: 'Active', color: 'bg-green-100 text-green-700' },
  { id: 2, name: 'Mean Reversal', description: 'Bollinger Bands & RSI logic.', status: 'Stopped', color: 'bg-gray-100 text-gray-700' },
  { id: 3, name: 'Momentum Breakout', description: 'Trend following on breakout.', status: 'Stopped', color: 'bg-gray-100 text-gray-700' },
  { id: 4, name: 'MTA (Multi-Timeframe)', description: 'D1/H4/H1 Hierarchical analysis.', status: 'Active', color: 'bg-green-100 text-green-700' },
];

const StrategyPage = () => {
  // State dummy untuk simulasi toggle status
  const [strategies, setStrategies] = useState(strategiesData);

  const toggleStrategy = (id) => {
    setStrategies(strategies.map(strat => 
      strat.id === id 
        ? { ...strat, status: strat.status === 'Active' ? 'Stopped' : 'Active', color: strat.status === 'Active' ? 'bg-gray-100 text-gray-700' : 'bg-green-100 text-green-700' }
        : strat
    ));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Strategy Control</h1>
        <p className="text-gray-500">Manage and monitor your algorithmic trading bots.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {strategies.map((strat) => (
          <div key={strat.id} className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold">{strat.name}</h3>
                <span className={`px-2 py-1 rounded text-xs font-bold ${strat.color}`}>
                  {strat.status}
                </span>
              </div>
              <p className="text-gray-500 mb-6">{strat.description}</p>
            </div>
            
            <div className="flex gap-3 mt-auto">
              <button 
                onClick={() => toggleStrategy(strat.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors ${
                  strat.status === 'Active' 
                    ? 'bg-red-50 text-red-600 hover:bg-red-100' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {strat.status === 'Active' ? <><Square size={18}/> Stop</> : <><Play size={18}/> Start</>}
              </button>
              
              <button className="p-2 text-gray-400 hover:bg-gray-50 rounded-lg border border-gray-200">
                <Settings size={20} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StrategyPage;