import { useRef } from 'react';

const UploadResume = ({ file, setFile }) => {
  const fileInputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'application/pdf') {
      setFile(droppedFile);
    } else {
      alert('Please upload a PDF file.');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      alert('Please upload a PDF file.');
    }
  };

  const handleClick = () => {
    fileInputRef.current.click();
  };

  return (
    <div
      className="bg-box-primary rounded-3xl p-12 text-center cursor-pointer hover:shadow-xl transition-shadow min-h-64 flex flex-col items-center justify-center"
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onClick={handleClick}
    >
      <button
        className="bg-btn-primary text-white px-8 py-3 rounded-full font-inter font-bold text-lg mb-4 hover:bg-opacity-90 transition-all btn-text"
        onClick={(e) => {
          e.stopPropagation();
          handleClick();
        }}
      >
        Select PDF Files
      </button>

      {file && (
        <div className="mb-4 text-center">
          <p className="text-white text-sm font-semibold">✓ {file.name}</p>
        </div>
      )}

      <p className="text-white text-base">
        or Drop PDF files Here
      </p>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        accept=".pdf"
        className="hidden"
      />
    </div>
  );
};

export default UploadResume;
