// File: src/components/ui/StatCard.jsx
import React from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react'; 

const StatCard = ({ title, value, change, isPositive }) => {
  const changeColor = isPositive ? 'text-green-600' : 'text-red-600';
  const Icon = isPositive ? ArrowUp : ArrowDown;

  return (
    // 💥 Styling Utama Kartu 💥
    <div className="bg-white p-5 rounded-xl shadow-lg border border-gray-100 transition-shadow hover:shadow-xl">
      <div className="text-sm font-medium text-gray-500">{title}</div>
      <div className="mt-1 text-3xl font-bold text-gray-900">{value}</div>
      <div className="flex items-center mt-2">
        <Icon size={16} className={`mr-1 ${changeColor}`} />
        <span className={`text-sm font-semibold ${changeColor}`}>{change}</span>
      </div>
    </div>
  );
};

export default StatCard;