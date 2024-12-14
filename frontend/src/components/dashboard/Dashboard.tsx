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
  matched_keywords: string[];
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
  
    // Set equal wider margins for both left and right
    const margin = 20;
    const pageWidth = doc.internal.pageSize.width;
    const contentWidth = pageWidth - 2 * margin; // Adjust width for content
  
    // Get the current date and time
    const currentDate = new Date();
    const formattedDate = currentDate.toLocaleString();
  
    // Add the title with the date and time in parentheses
    doc.setFont("helvetica", "bold");
    doc.text(`Resume Scanner Report (${formattedDate})`, margin, margin + 10);
  
    doc.setFont("helvetica", "normal");
    let yOffset = margin + 20; // Start for Fit Score
  
    // Fit Score
    doc.text(`Fit Score: ${fitScoreData.fit_score}%`, margin, yOffset);
    yOffset += 10; // Increment position for next section
  
    // Matched Keywords Section
    if (fitScoreData.matched_keywords && fitScoreData.matched_keywords.length > 0) {
      doc.setFont("helvetica", "bold");
      doc.text("Matched Keywords:", margin, yOffset);
      yOffset += 10;
  
      doc.setFont("helvetica", "normal");
      fitScoreData.matched_keywords.forEach((keyword, index) => {
        doc.text(`- ${keyword}`, margin, yOffset);
        yOffset += 10;
      });
    }
  
    // Feedback Section
    if (fitScoreData.feedback && fitScoreData.feedback.length > 0) {
      doc.setFont("helvetica", "bold");
      doc.text("Feedback:", margin, yOffset);
      yOffset += 10;
  
      doc.setFont("helvetica", "normal");
      fitScoreData.feedback.forEach((item, index) => {
        // Add spacing and wrap text consistently
        doc.text(`${capitalizeCategory(item.category)}:`, margin, yOffset);
        yOffset += 5;
  
        doc.text(item.text, margin + 5, yOffset, { maxWidth: contentWidth }); // Adjust width for content
        yOffset += 15; // Increment y position after each feedback item for consistency
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
              <SkillsMatched skills={fitScoreData.matched_keywords} />
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
