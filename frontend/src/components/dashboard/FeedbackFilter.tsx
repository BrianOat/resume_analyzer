import React, { useState, useEffect } from 'react';
import "../../styles/dashboard/feedback_filter.css";

interface FeedbackFilterProps {
  suggestions: string[];
}

const FeedbackFilter: React.FC<FeedbackFilterProps> = ({ suggestions }) => {
  const [filter, setFilter] = useState<string>('all');
  const [filteredFeedback, setFilteredFeedback] = useState<string[]>([]);

  useEffect(() => {
    if (Array.isArray(suggestions)) {
      const filteredFeedback = suggestions.filter((item) =>
        filter === 'all' ? true : item.includes(filter)
      );
      setFilteredFeedback(filteredFeedback);
    }
  }, [filter, suggestions]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilter(e.target.value);
  };

  return (
    <div className="feedback-filter-container">
      <h2 className="feedback-filter-header">Improvement Suggestions</h2>
      <select
        className="feedback-filter-select"
        value={filter}
        onChange={handleFilterChange}
      >
        <option value="all">All</option>
        <option value="skills">Skills</option>
        <option value="experience">Experience</option>
        <option value="formatting">Formatting</option>
      </select>
      {filteredFeedback && (
        <ul className="feedback-filter-list">
          {filteredFeedback.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FeedbackFilter;