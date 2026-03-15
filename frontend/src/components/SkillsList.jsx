const SkillsList = ({ title, skills, type }) => {
  const getTagColor = (type) => {
    return type === 'matched' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';
  };

  const skillTags = Array.isArray(skills)
    ? skills
    : Object.values(skills).flat();

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="flex flex-wrap gap-2">
        {skillTags.map((skill, index) => (
          <span
            key={index}
            className={`px-3 py-1 rounded-full text-sm font-medium ${getTagColor(type)}`}
          >
            {skill}
          </span>
        ))}
      </div>
    </div>
  );
};

export default SkillsList;