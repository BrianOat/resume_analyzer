import React, { useState, useEffect } from 'react';
import axios from 'axios';
import "../../styles/dashboard/skills_matched.css";

const SkillsMatched = () => {
  const [skills, setSkills] = useState([]);

  // useEffect(() => {
  //   const getSkills = async () => {
  //     try {
  //       const response = await axios.get('/api/skills');
  //       setSkills(response.data.skills);
  //     } catch (error) {
  //       console.error(error);
  //     }
  //   };
  //   getSkills();
  // }, []);

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