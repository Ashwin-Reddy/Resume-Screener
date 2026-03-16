const AnalyzeButton = ({ onClick, loading }) => {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`px-8 py-2 rounded-full font-inter font-extrabold text-[20px] transition-all btn-text whitespace-nowrap ${loading
          ? 'bg-gray-400 cursor-not-allowed text-white'
          : 'bg-btn-primary hover:bg-opacity-90 active:bg-opacity-80 text-white'
        }`}
    >
      {loading ? (
        <div className="flex items-center justify-center gap-2 text-[20px]">
          <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Analyzing...
        </div>
      ) : (
        'Analyze'
      )}
    </button>
  );
};

export default AnalyzeButton;