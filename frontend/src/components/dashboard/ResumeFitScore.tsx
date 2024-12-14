import ProgressBar from '../shared/ProgressBar';
import "../../styles/dashboard/resume_fit_score.css";

interface ResumeFitScoreProps {
  fitScore: number;
}

const ResumeFitScore: React.FC<ResumeFitScoreProps> = ({ fitScore }) => {
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