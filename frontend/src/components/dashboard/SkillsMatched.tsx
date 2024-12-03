import React from 'react';
import "../../styles/dashboard/skills_matched.css";

const SkillsMatched = () => {
  const skills = ['React', 'JavaScript', 'Tailwind CSS', 'TypeScript']; // Example data

  return (
    <div className="skills-matched-container">
      <h2 className="skills-matched-title">Skills and Keywords Matched</h2>
      <ul className="skills-matched-list">
        {skills.map((skill, index) => (
          <li key={index} className="skills-matched-item">{skill}</li>
        ))}
      </ul>
    </div>
  );
};

export default SkillsMatched;
