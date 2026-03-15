import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const ScoreCard = ({ score }) => {
    const getScoreColor = () => {
        if (score < 40) return '#EF4444'; // red
        if (score < 70) return '#FBBF24'; // yellow
        return '#10B981'; // green
    };

    const getScoreGradient = () => {
        if (score < 40) return '#DC2626'; // darker red for background
        if (score < 70) return '#F59E0B'; // darker yellow for background
        return '#059669'; // darker green for background
    };

    const data = [
        { name: 'score', value: score },
        { name: 'remaining', value: 100 - score },
    ];

    return (
        <div className="bg-box-primary rounded-3xl p-8 flex flex-col items-center justify-center min-h-48">
            <p className="heading-section text-white mb-6">Score</p>
            <div className="w-40 h-40 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={70}
                            startAngle={90}
                            endAngle={-270}
                            dataKey="value"
                            stroke="none"
                        >
                            <Cell fill={getScoreColor()} />
                            <Cell fill="rgba(255, 255, 255, 0.1)" />
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute text-center">
                    <p className="text-white text-4xl font-bold">{score}%</p>
                </div>
            </div>
        </div>
    );
};

export default ScoreCard;
