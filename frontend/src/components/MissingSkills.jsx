const MissingSkills = ({ skills }) => {
    const list = skills ? Object.values(skills).flat() : [];

    return (
        <div className="bg-box-primary rounded-[32px] p-8 h-full flex flex-col items-center justify-center">
            <div className="space-y-1 text-center">
                {list.map((skill, index) => (
                    <p key={index} className="text-white text-[18px] font-inter leading-relaxed">
                        {skill}
                    </p>
                ))}
            </div>
        </div>
    );
};

export default MissingSkills;
