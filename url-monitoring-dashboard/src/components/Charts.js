// src/components/Charts.js
import React from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import useStore from '../store/useStore';
import { motion } from 'framer-motion';

function Charts() {
  const { data } = useStore();

  const statusCounts = React.useMemo(() => {
    const counts = {};
    data.forEach((item) => {
      counts[item.status] = (counts[item.status] || 0) + 1;
    });
    return Object.entries(counts).map(([status, count]) => ({ status, count }));
  }, [data]);

  const COLORS = ['#FFBB28', '#FF8042', '#00C49F', '#0088FE', '#FF6384'];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col md:flex-row gap-8"
    >
      <div className="w-full md:w-1/2 h-96">
        <ResponsiveContainer>
          <BarChart data={statusCounts}>
            <XAxis dataKey="status" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#1A73E8" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="w-full md:w-1/2 h-96">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={statusCounts}
              dataKey="count"
              nameKey="status"
              outerRadius={80}
              fill="#82ca9d"
              label
            >
              {statusCounts.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}

export default Charts;
