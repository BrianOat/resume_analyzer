import React, { useState, useEffect } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import ResumeFitScore from './ResumeFitScore';
import SkillsMatched from './SkillsMatched';
import ResumeView from './ResumeView';
import FeedbackFilter from './FeedbackFilter';
import CheckToken from '../CheckToken';
import "../../styles/dashboard/dashboard.css";

// Define the structure for fit score data
interface FitScoreData {
  fit_score: number;
  matched_skills: string[];
  feedback: { category: string, text: string }[]; // Include feedback data
}

interface ErrorData {
  error: string;
}

const Dashboard = () => {
  const [fitScoreData, setFitScoreData] = useState<FitScoreData | ErrorData | null>(null);
  console.log(localStorage);

  useEffect(() => {
    const getFitScoreData = async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/fit-score');
        setFitScoreData(response.data);
        localStorage.setItem('fitScoreData', JSON.stringify(response.data));
        console.log('Fetched fit score data:', response.data);
      } catch (error: any) {
        if (error.response && error.response.status === 422) {
          setFitScoreData({ error: 'Please go to the input tab and submit your resume and job description' });
        } else if (error.response && error.response.data) {
          setFitScoreData({ error: error.response.data.error as string });
          console.log('Fetched fit score data:', error.response);
        } else {
          setFitScoreData({ error: 'An unknown error occurred' });
        }
      }
    };
    getFitScoreData();
  }, []);

  CheckToken();

  if (fitScoreData && 'error' in fitScoreData) {
    return <div>Error: {fitScoreData.error}</div>;
  } else if (!fitScoreData) {
    return <div>Loading...</div>;
  }

  // Generate PDF
  const generatePDF = () => {
    const doc = new jsPDF();
    const margin = 20; // Equal margins
    const pageWidth = 210;
    const pageHeight = 297;
    const contentWidth = pageWidth - 2 * margin;
  
    let yOffset = margin; // Y position tracker
  
    const addPageIfNeeded = () => {
      if (yOffset > pageHeight - margin) {
        doc.addPage();
        yOffset = margin; // Reset Y position for the new page
      }
    };
  
    // Get current date and time
    const currentDate = new Date();
    const formattedDate = currentDate.toLocaleString();
  
    // Title
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12); // Reduced font size
    doc.text(`Resume Scanner Report (${formattedDate})`, margin, yOffset);
    yOffset += 10;
    addPageIfNeeded();
  
    // Fit Score
    doc.setFont("helvetica", "normal");
    doc.text(`Fit Score: ${fitScoreData.fit_score}%`, margin, yOffset);
    yOffset += 10;
    addPageIfNeeded();
  
    // Matched Keywords
    if (fitScoreData.matched_skills?.length > 0) {
      doc.setFont("helvetica", "bold");
      doc.text("Matched Keywords:", margin, yOffset);
      yOffset += 6;
  
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10); // Smaller font size
      fitScoreData.matched_skills.forEach((keyword) => {
        addPageIfNeeded();
        doc.text(`- ${keyword}`, margin, yOffset);
        yOffset += 6;
      });
      yOffset += 1;
    }
  
    // Feedback Section
    if (fitScoreData.feedback?.length > 0) {
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text("Feedback:", margin, yOffset);
      yOffset += 6;
  
      doc.setFont("helvetica", "normal");
      doc.setFontSize(10);
      fitScoreData.feedback.forEach((item) => {
        addPageIfNeeded();
        doc.text(`${capitalizeCategory(item.category)}:`, margin, yOffset);
        yOffset += 6;
  
        const splitText = doc.splitTextToSize(item.text, contentWidth); // Auto-wrap text
        splitText.forEach((line: string) => {
          addPageIfNeeded();
          doc.text(line, margin + 5, yOffset);
          yOffset += 6;
        });
      });
    }
  
    // Save the PDF
    doc.save("Resume_Scanner_Report.pdf");
  };
  
  // Capitalize category for feedback
  const capitalizeCategory = (category: string) => {
    return category.charAt(0).toUpperCase() + category.slice(1);
  };

  return (
    <div className="dashboard-container">
      {/* Grid Layout */}
      <div className="dashboard-grid">
        {/* Left Side - PDF Viewer */}
        <div className="dashboard-pdf-viewer">
          <ResumeView />
        </div>

        {/* Right Side - Analysis Results */}
        <div className="dashboard-analysis-results">
          <h1 className="dashboard-header">Resume Analysis Results</h1>
          {fitScoreData && 'fit_score' in fitScoreData && (
            <>
              <ResumeFitScore fitScore={fitScoreData.fit_score} />
              <SkillsMatched skills={fitScoreData.matched_skills} />
              <FeedbackFilter feedback={fitScoreData.feedback} />
              <button onClick={generatePDF} className="download-report-btn">
                Download PDF Report
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
