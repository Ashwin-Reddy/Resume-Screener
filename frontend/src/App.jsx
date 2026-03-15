import { useState } from 'react';
import UploadResume from './components/UploadResume';
import JobDescription from './components/JobDescription';
import AnalyzeButton from './components/AnalyzeButton';
import ScoreCard from './components/ScoreCard';
import MissingSkills from './components/MissingSkills';
import ExplanationCard from './components/ExplanationCard';
import { analyzeResume } from './api/resumeApi';

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
      const result = await analyzeResume(file, jobDescription);
      setResult(result);
    } catch (error) {
      console.error('Error analyzing resume:', error);
      alert('Error analyzing resume. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-bg-primary py-12 px-6">
      {/* Main Heading */}
      <div className="text-center mb-16">
        <h1 className="heading-main text-black">
          AI Resume Screener
        </h1>
      </div>

      {!result ? (
        /* Input Form - 3 Column Layout */
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-12 gap-8 items-start">
            {/* LEFT COLUMN - Resume and Job Description */}
            <div className="col-span-4 space-y-8">
              {/* Resume Upload */}
              <div>
                <p className="heading-section text-black mb-4">Resume</p>
                <UploadResume file={file} setFile={setFile} />
              </div>

              {/* Job Description */}
              <div>
                <p className="heading-section text-black mb-4">Job Description</p>
                <JobDescription jobDescription={jobDescription} setJobDescription={setJobDescription} />
              </div>
            </div>

            {/* CENTER COLUMN - Divider and Button */}
            <div className="col-span-1 flex flex-col items-center h-96">
              {/* Vertical Divider */}
              <div className="w-px h-3/4 bg-gray-400"></div>
              {/* Analyze Button */}
              <div className="mt-8">
                <AnalyzeButton onClick={handleAnalyze} loading={loading} />
              </div>
            </div>

            {/* RIGHT COLUMN - Result Cards Placeholder */}
            <div className="col-span-4">
              <div className="space-y-8">
                <div>
                  <p className="heading-section text-black mb-4">Upload and analyze to see results</p>
                  <div className="bg-box-primary rounded-3xl p-8 text-center text-white">
                    <p>Results will appear here</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Results Dashboard */
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-12 gap-8">
            {/* LEFT COLUMN - Resume and Job Description (collapsed in results) */}
            <div className="col-span-4 space-y-8">
              <div>
                <p className="heading-section text-black mb-4">Resume</p>
                <UploadResume file={file} setFile={setFile} />
              </div>

              <div>
                <p className="heading-section text-black mb-4">Job Description</p>
                <JobDescription jobDescription={jobDescription} setJobDescription={setJobDescription} />
              </div>
            </div>

            {/* CENTER COLUMN - Divider and Button */}
            <div className="col-span-1 flex flex-col items-center">
              {/* Vertical Divider */}
              <div className="w-px h-96 bg-gray-400"></div>
              {/* Re-analyze Button */}
              <div className="mt-8">
                <AnalyzeButton onClick={handleAnalyze} loading={loading} />
              </div>
            </div>

            {/* RIGHT COLUMN - Results */}
            <div className="col-span-4 space-y-8">
              {/* Score Card */}
              <div>
                <ScoreCard score={result.match_score} />
              </div>

              {/* Missing Skills Card */}
              <div>
                <MissingSkills skills={result.missing_skills} />
              </div>

              {/* Explanation Card */}
              <div>
                <ExplanationCard explanation={result.explanation} />
              </div>
            </div>
          </div>

          {/* Reset Button */}
          <div className="mt-12 text-center">
            <button
              onClick={() => setResult(null)}
              className="px-8 py-3 bg-btn-primary text-white rounded-full font-inter font-bold hover:bg-opacity-90 transition-all btn-text"
            >
              Analyze Another Resume
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;