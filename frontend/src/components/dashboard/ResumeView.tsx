import React, { useEffect, useState } from "react";
import { Viewer } from '@react-pdf-viewer/core';
import { Worker } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import "../../styles/dashboard/resume_view.css";

const ResumeView: React.FC = () => {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    // Retrieve the PDF file from localStorage
    const savedPdf = localStorage.getItem("resumePdf");
    if (savedPdf) {
      setPdfUrl(savedPdf); // Set the Base64 URL for the PDF
    }
  }, []);

  return (
    <div className="resume-view-container">
      <h2 className="resume-view-title">Resume Preview</h2>
      <div className="resume-view-content">
        {pdfUrl ? (
          <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js">
            <Viewer fileUrl={pdfUrl} />
          </Worker>
        ) : (
          <p>No resume available to display.</p>
        )}
      </div>
    </div>
  );
};

export default ResumeView;
