const MissingSkills = ({ skills }) => {
    const formatSkills = () => {
        if (!skills || typeof skills !== 'object') {
            return [];
        }

        const allSkills = [];
        if (typeof skills === 'object') {
            Object.values(skills).forEach((category) => {
                if (Array.isArray(category)) {
                    allSkills.push(...category);
                }
            });
        }
        return allSkills;
    };

    const skillsList = formatSkills();

    return (
        <div className="bg-box-primary rounded-3xl p-8 min-h-48">
            <p className="heading-section text-white mb-6">Missing Skills</p>
            <div className="space-y-3">
                {skillsList.length > 0 ? (
                    skillsList.map((skill, index) => (
                        <p key={index} className="text-white text-base font-inter">
                            {skill}
                        </p>
                    ))
                ) : (
                    <p className="text-white text-base font-inter">No missing skills identified</p>
                )}
            </div>
        </div>
    );
};

export default MissingSkills;
