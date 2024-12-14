import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ResumeFitScore from './ResumeFitScore';
import SkillsMatched from './SkillsMatched';
import ImprovementSuggestions from './ImprovementSuggestions';
import ResumeView from './ResumeView';
import FeedbackFilter from './FeedbackFilter';
import CheckToken from '../CheckToken';
import "../../styles/dashboard/dashboard.css";

interface FitScoreData {
  fit_score: number;
  matched_keywords: string[];
  suggestions: string[];
}

interface ErrorData {
  error: string;
}

const Dashboard = () => {
  const [fitScoreData, setFitScoreData] = useState<FitScoreData | ErrorData | null>(null);
  console.log(localStorage)

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
              <FeedbackFilter suggestions={fitScoreData.suggestions} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;