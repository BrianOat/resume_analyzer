import React, { useState } from "react";
import axios from "axios";
import "../../styles/form/file_input.css";

interface FileInputProps {
  label: string;
}

const FileInput: React.FC<FileInputProps> = ({ label }) => {
  const [isLoading, setIsLoading] = useState<boolean>(false); // Track loading state
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null); // Track uploaded file name

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setIsLoading(true); // Show spinner
    setUploadedFileName(null); // Reset file name

    try {
      const response = await axios.post("http://localhost:8000/api/resume-upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setUploadedFileName(file.name); // Save uploaded file name
      alert(response.data.message); // Show success message
    } catch (error) {
      console.error(error);
      alert("Failed to upload the resume. Please try again.");
    } finally {
      setIsLoading(false); // Hide spinner
    }
  };

  return (
    <div className="input-container">
      <label className="input-label">{label}</label>
      {isLoading ? (
        <div className="spinner-container">
          <div className="spinner"></div>
          <p>Uploading... Please Wait.</p>
        </div>
      ) : (
        <div>
          <input type="file" accept=".pdf,.docx" onChange={handleFileUpload} />
          {uploadedFileName && (
            <p className="uploaded-file-name">Uploaded: {uploadedFileName}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default FileInput;
