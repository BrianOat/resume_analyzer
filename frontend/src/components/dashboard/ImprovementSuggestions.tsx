import "../../styles/dashboard/improvement_suggestions.css";
const ImprovementSuggestions = () => {
  const suggestions = [
    'Include more action verbs.',
    'Highlight key achievements.',
    'Focus on relevant keywords.',
  ]; // Example data

  return (
    <div className="improvement-suggestions-container">
      <h2 className="improvement-suggestions-title">Improvement Suggestions</h2>
      <ul className="improvement-suggestions-list">
        {suggestions.map((suggestion, index) => (
          <li key={index} className="improvement-suggestions-item">
            {suggestion}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ImprovementSuggestions;
