import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const ScoreCard = ({ score }) => {
    const displayScoreNum = score !== undefined && score !== null ? Number(score) : 0;
    const displayScoreStr = displayScoreNum.toFixed(1);
    
    const data = [
        { name: 'score', value: displayScoreNum },
        { name: 'remaining', value: 100 - displayScoreNum },
    ];

    return (
        <div className="bg-box-primary rounded-[32px] p-4 flex flex-col items-center justify-center h-full">
            <div className="w-[100px] h-[100px] relative flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={35}
                            outerRadius={45}
                            startAngle={90}
                            endAngle={-270}
                            dataKey="value"
                            stroke="none"
                        >
                            <Cell fill="#FF0000" />
                            <Cell fill="#D1D5DB" />
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute text-center flex items-center justify-center inset-0">
                    <p className="text-white text-[16px] font-inter">{displayScoreStr}%</p>
                </div>
            </div>
        </div>
    );
};

export default ScoreCard;
