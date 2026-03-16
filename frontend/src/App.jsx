import { useState } from 'react';
import UploadResume from './components/UploadResume';
import JobDescription from './components/JobDescription';
import AnalyzeButton from './components/AnalyzeButton';
import ScoreCard from './components/ScoreCard';
import MissingSkills from './components/MissingSkills';
import ExplanationCard from './components/ExplanationCard';
import axios from 'axios';

function App() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!file || !jobDescription.trim()) {
      alert('Please upload a resume and enter a job description.');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("resume_file", file);
      formData.append("job_description", jobDescription);

      const response = await axios.post(
        "http://127.0.0.1:8000/analyze-resume",
        formData
      );

      setResult(response.data);
    } catch (error) {
      console.error('Error analyzing resume:', error);
      alert('Error analyzing resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary py-12 px-8 font-inter">
      {/* Main Heading */}
      <div className="text-center mb-10">
        <h1 className="heading-main text-black">
          AI Resume Screener
        </h1>
      </div>

      <div className="flex justify-center items-stretch gap-8 max-w-[1440px] mx-auto h-[600px]">
        {/* LEFT COLUMN - Resume and Job Description */}
        <div className="flex-[0.8] flex flex-col gap-8">
          <div className="flex-1 flex flex-col">
            <h2 className="heading-section text-black text-center mb-4">Resume</h2>
            <UploadResume file={file} setFile={setFile} />
          </div>

          <div className="flex-1 flex flex-col">
            <h2 className="heading-section text-black text-center mb-4">Job Description</h2>
            <JobDescription jobDescription={jobDescription} setJobDescription={setJobDescription} />
          </div>
        </div>

        {/* CENTER COLUMN - Divider and Analyze Button */}
        <div className="w-24 relative flex flex-col items-center justify-center">
            {/* Vertical line through the center */}
            <div className="absolute top-10 bottom-0 w-px bg-[#8BA4B1]"></div>
            {/* Analyze Button */}
            <div className="relative z-10 bg-bg-primary py-4">
              <AnalyzeButton onClick={handleAnalyze} loading={loading} />
            </div>
        </div>

        {/* RIGHT COLUMN - Results */}
        <div className="flex-1 flex gap-8">
          {/* Left side of right column */}
          <div className="w-[30%] flex flex-col gap-8">
            <div className="flex flex-col h-[180px]">
              <h2 className="heading-section text-black text-center mb-4">Score</h2>
              <ScoreCard score={result?.match_score} />
            </div>

            <div className="flex-1 flex flex-col">
              <h2 className="heading-section text-black text-center mb-4">Missing skills</h2>
              <MissingSkills skills={result?.missing_skills} />
            </div>
          </div>

          {/* Right side of right column */}
          <div className="flex-1 flex flex-col">
            <h2 className="heading-section text-black text-center mb-4">Explanation</h2>
            <ExplanationCard explanation={result?.explanation} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;