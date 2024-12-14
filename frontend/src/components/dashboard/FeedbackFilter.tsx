import React, { useState, useEffect } from 'react';
import "../../styles/dashboard/feedback_filter.css";

interface FeedbackFilterProps {
  feedback: { category: string, text: string }[]; // Change from suggestions to feedback
}

const FeedbackFilter: React.FC<FeedbackFilterProps> = ({ feedback }) => {
  const [filter, setFilter] = useState<string>('all');
  const [filteredFeedback, setFilteredFeedback] = useState<{ category: string, text: string }[]>([]);

  useEffect(() => {
    if (Array.isArray(feedback)) {
      const filteredFeedback = feedback.filter((item) =>
        filter === 'all' ? true : item.category.toLowerCase().includes(filter.toLowerCase())
      );
      setFilteredFeedback(filteredFeedback);
    }
  }, [filter, feedback]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilter(e.target.value);
  };

  // Function to capitalize the category
  const capitalizeCategory = (category: string) => {
    return category.charAt(0).toUpperCase() + category.slice(1);
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
            <li key={index}>
              <strong>{capitalizeCategory(item.category)}:</strong> {item.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default FeedbackFilter;
