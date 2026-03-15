import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const MatchScoreChart = ({ score }) => {
  const data = [
    { name: 'Match', value: score },
    { name: 'Gap', value: 100 - score },
  ];

  const getColor = (score) => {
    if (score < 40) return '#ef4444'; // red
    if (score < 70) return '#f59e0b'; // yellow
    return '#10b981'; // green
  };

  const COLORS = [getColor(score), '#e5e7eb'];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Match Score</h3>
      <div className="relative">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={0}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-3xl font-bold" style={{ color: getColor(score) }}>
              {score}%
            </div>
            <div className="text-sm text-gray-600">Match</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchScoreChart;