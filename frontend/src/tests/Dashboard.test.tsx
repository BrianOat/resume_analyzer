import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import FeedbackFilter from '../components/dashboard/FeedbackFilter';

interface FeedbackFilterProps {
  feedback: { category: string; text: string }[];
}

const FeedbackFilterComponent: React.FC<FeedbackFilterProps> = FeedbackFilter;

describe('FeedbackFilter component', () => {
  const feedbackData = [
    { category: 'skills', text: 'Feedback 1' },
    { category: 'experience', text: 'Feedback 2' },
    { category: 'formatting', text: 'Feedback 3' },
  ];

  it('renders all feedback by default', () => {
    const { getByText } = render(<FeedbackFilterComponent feedback={feedbackData} />);
    expect(getByText('Feedback 1')).toBeInTheDocument();
    expect(getByText('Feedback 2')).toBeInTheDocument();
    expect(getByText('Feedback 3')).toBeInTheDocument();
  });

  it('updates displayed feedback when filter is selected', () => {
    const { getByText, getByRole } = render(<FeedbackFilterComponent feedback={feedbackData} />);
    const selectElement = getByRole('combobox');
    fireEvent.change(selectElement, { target: { value: 'skills' } });
    expect(getByText('Feedback 1')).toBeInTheDocument();
    expect(getByText('Feedback 2')).not.toBeInTheDocument();
    expect(getByText('Feedback 3')).not.toBeInTheDocument();
  });

  it('displays no feedback when filter has no matching feedback', () => {
    const { getByText, getByRole } = render(<FeedbackFilterComponent feedback={feedbackData} />);
    const selectElement = getByRole('combobox');
    fireEvent.change(selectElement, { target: { value: 'general' } });
    expect(getByText('No feedback found')).toBeInTheDocument();
  });

  it('displays all feedback when "All" filter is selected', () => {
    const { getByText, getByRole } = render(<FeedbackFilterComponent feedback={feedbackData} />);
    const selectElement = getByRole('combobox');
    fireEvent.change(selectElement, { target: { value: 'all' } });
    expect(getByText('Feedback 1')).toBeInTheDocument();
    expect(getByText('Feedback 2')).toBeInTheDocument();
    expect(getByText('Feedback 3')).toBeInTheDocument();
  });
});