import React from 'react';
import "../../styles/dashboard/skills_matched.css";

interface SkillsMatchedProps {
  skills: string[];
}

const SkillsMatched: React.FC<SkillsMatchedProps> = ({ skills }) => {
  return (
    <div className="skills-matched-container">
      <h2 className="skills-matched-title">Skills and Keywords Matched</h2>
      {Array.isArray(skills) && (
        <ul className="skills-matched-list">
          {skills.map((skill, index) => (
            <li key={index} className="skills-matched-item">{skill}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SkillsMatched;