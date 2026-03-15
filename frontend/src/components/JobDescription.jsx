const JobDescription = ({ jobDescription, setJobDescription }) => {
  return (
    <div className="bg-box-primary rounded-3xl p-8 min-h-64">
      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        placeholder="Write the job description here."
        className="w-full h-full p-4 bg-box-primary text-white placeholder-gray-300 resize-none focus:outline-none text-base"
        style={{ minHeight: '200px' }}
      />
    </div>
  );
};

export default JobDescription;
