import ResumeFitScore from './ResumeFitScore';
import SkillsMatched from './SkillsMatched';
import ImprovementSuggestions from './ImprovementSuggestions';
import ResumeView from './ResumeView';
import "../../styles/dashboard/dashboard.css";
import CheckToken from '../CheckToken';


const Dashboard = () => {
  CheckToken();
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
          <ResumeFitScore />
          <SkillsMatched />
          <ImprovementSuggestions />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
