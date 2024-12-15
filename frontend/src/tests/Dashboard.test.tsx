import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Dashboard from '../components/dashboard/Dashboard';
import axios from 'axios';

// Mock Axios
jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Dashboard Component', () => {
  // Test rendering when data is being fetched
  it('should render loading state when data is being fetched', () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  // Test for error message if fetching data fails
  it('should display error message if fetching data fails', async () => {
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 422,
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText(/Please go to the input tab and submit your resume and job description/i)).toBeInTheDocument());
  });

  // Test rendering when valid fit score data is fetched
  it('should display the fetched fit score data correctly', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        fit_score: 85,
        matched_skills: ['JavaScript', 'React'],
        feedback: [
          { category: 'skills', text: 'Improve your JavaScript skills' },
          { category: 'experience', text: 'Add more experience in web development' },
        ],
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText(/Resume Analysis Results/i));

    // Check if fit score is displayed
    expect(screen.getByText(/85%/i)).toBeInTheDocument();
    // Check if matched skills are displayed
    let listItem = screen.getByText(/JavaScript/i, { selector: 'li.skills-matched-item' });
    expect(listItem).toBeInTheDocument();
    listItem = screen.getByText(/React/i, { selector: 'li.skills-matched-item' });
    expect(listItem).toBeInTheDocument();
    // Check if feedback is displayed
    expect(screen.getByText(/Improve your JavaScript skills/i)).toBeInTheDocument();
  });

  // Test for empty feedback scenario
  it('should display a message if no feedback is provided', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        fit_score: 85,
        matched_skills: ['JavaScript', 'React'],
        feedback: [],
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    await waitFor(() => screen.getByText(/Resume Analysis Results/i));

    expect(screen.getByText(/No feedback available/i)).toBeInTheDocument();
  });

  // Test that feedback can be filtered correctly
  it('should filter feedback by category correctly', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        fit_score: 85,
        matched_skills: ['JavaScript', 'React'],
        feedback: [
          { category: 'skills', text: 'Improve your JavaScript skills' },
          { category: 'experience', text: 'Add more experience in web development' },
          { category: 'formatting', text: 'Fix the formatting of your resume' },
        ],
      },
    });

    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );

    // Wait for the feedback section to load
    await waitFor(() => screen.getByText(/Resume Analysis Results/i));

    // Initially, all feedback should be visible
    expect(screen.getByText(/Improve your JavaScript skills/i)).toBeInTheDocument();
    expect(screen.getByText(/Add more experience in web development/i)).toBeInTheDocument();
    expect(screen.getByText(/Fix the formatting of your resume/i)).toBeInTheDocument();

    // Filter by "skills"
    fireEvent.change(screen.getByRole('combobox'), { target: { value: 'skills' } });

    // After filtering, only "skills" feedback should be visible
    await waitFor(() => screen.getByText(/Improve your JavaScript skills/i));
    expect(screen.queryByText(/Add more experience in web development/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Fix the formatting of your resume/i)).not.toBeInTheDocument();
  });
});
