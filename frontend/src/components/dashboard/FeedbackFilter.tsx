import React, { useState, useEffect } from 'react';
import "../../styles/dashboard/feedback_filter.css";
import axios from 'axios';

interface FeedbackItem {
  category: string;
  text: string;
}

interface FeedbackData {
  fitScore: number;
  feedback: FeedbackItem[];
}

const FeedbackFilter = () => {
  const [filter, setFilter] = useState<string>('all');
  const [feedback, setFeedback] = useState<FeedbackItem[]>([]);
  const [filteredFeedback, setFilteredFeedback] = useState<FeedbackItem[]>([]);

  // Dummy data for testing
  const dummyData: FeedbackData = {
    fitScore: 100,
    feedback: [
      { category: 'skills', text: 'random feedback 1' },
      { category: 'experience', text: 'random feedback 1' },
      { category: 'formatting', text: 'random feedback 1' },
      { category: 'general', text: 'random feedback 1' },
    ],
  };

  // API call (commented out for now)
  // useEffect(() => {
  //   const getFeedback = async () => {
  //     try {
  //       const response = await axios.get('/api/feedback');
  //       const data: FeedbackData = response.data;
  //       setFeedback(data.feedback);
  //     } catch (error) {
  //       console.error(error);
  //     }
  //   };
  //   getFeedback();
  // }, []);

  useEffect(() => {
    setFeedback(dummyData.feedback);
  }, []);

  useEffect(() => {
    const filteredFeedback = feedback.filter((item) =>
      filter === 'all' ? true : item.category === filter
    );
    setFilteredFeedback(filteredFeedback);
  }, [filter, feedback]);

  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilter(e.target.value);
  };

  return (
    <div className="feedback-filter-container">
      <h2 className="feedback-filter-header">Feedback</h2>
      <select
        className="feedback-filter-select"
        value={filter}
        onChange={handleFilterChange}
      >
        <option value="all">All</option>
        <option value="skills">Skills</option>
        <option value="experience">Experience</option>
        <option value="formatting">Formatting</option>
        <option value="general">General</option>
      </select>
      <ul className="feedback-filter-list">
        {filteredFeedback.map((item, index) => (
          <li key={index}>{item.text}</li>
        ))}
      </ul>
    </div>
  );
};

export default FeedbackFilter;