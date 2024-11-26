import React from "react";
import axios from "axios";
import "../../styles/form/file_input.css"

interface FileInputProps {
  label: string;
}

const FileInput: React.FC<FileInputProps> = ({ label }) => {
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/api/resume-upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      });
      alert(response.data.message);
    } catch (error) {
      console.error(error);
      alert("Failed to upload the resume. Please try again.");
    }
  };

  return (
    <div>
      <label className="input-label">{label}</label>
      <div>
        <input type="file" accept=".pdf,.docx" onChange={handleFileUpload} />
      </div>
    </div>
  );

};
export default FileInput;
