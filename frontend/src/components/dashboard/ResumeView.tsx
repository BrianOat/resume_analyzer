import React from 'react';
import { Viewer } from '@react-pdf-viewer/core';
import { Worker } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import "../../styles/dashboard/resume_view.css";

const ResumeView: React.FC = () => {
  return (
    <div className="resume-view-container">
      <h2 className="resume-view-title">Resume Preview</h2>
      <div className="resume-view-content">
        <Worker workerUrl="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js">
          <Viewer
            fileUrl="/resume.pdf"
            // No default layout plugin, just the basic viewer to hide toolbar
          />
        </Worker>
      </div>
    </div>
  );
};

export default ResumeView;
