import ProgressBar from '../shared/ProgressBar';
import "../../styles/dashboard/resume_fit_score.css";
import { useState } from 'react';
import axios from 'axios';

const ResumeFitScore = () => {
  const [fitScore, setFitScore] = useState(0);

  // useEffect(() => {
  //   const getFitScore = async () => {
  //     try {
  //       const response = await axios.get(`/api/fit-score`);
  //       setFitScore(response.data.fitScore);
  //     } catch (error) {
  //       console.error(error);
  //     }
  //   };
  //   getFitScore();
  // }, []);

  return (
    <div className="resume-fit-score-container">
      <h2 className="resume-fit-score-title">Resume Fit Score</h2>
      <div className="resume-fit-score-content">
        <ProgressBar value={fitScore} />
        <span className="resume-fit-score-percentage">{fitScore}%</span>
      </div>
    </div>
  );
};

export default ResumeFitScore;