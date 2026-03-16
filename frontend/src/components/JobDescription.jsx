const JobDescription = ({ jobDescription, setJobDescription }) => {
  return (
    <div className="bg-box-primary rounded-[32px] p-8 h-full">
      <textarea
        value={jobDescription}
        onChange={(e) => setJobDescription(e.target.value)}
        placeholder="Write the job description here."
        className="w-full h-full bg-transparent text-white placeholder-white resize-none focus:outline-none text-[18px] font-inter"
      />
    </div>
  );
};

export default JobDescription;
