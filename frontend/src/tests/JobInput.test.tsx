import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import axios from "axios";
import JobInput from "../components/form/JobInput";
import '@testing-library/jest-dom';

jest.mock("axios");

beforeAll(() => {
  window.alert = jest.fn();
});

describe("JobInput Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    (console.error as jest.Mock).mockRestore();
  });

  test("renders the component with label, textarea, character counter, and submit button", () => {
    render(<JobInput label="Job Description" />);

    expect(screen.getByText("Job Description")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Enter the job description here...")).toBeInTheDocument();
    expect(screen.getByText("0 / 5000 characters")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Submit" })).toBeInTheDocument();
  });

  test("updates textarea value on typing", () => {
    render(<JobInput label="Job Description" />);

    const textarea = screen.getByPlaceholderText("Enter the job description here...");

    fireEvent.change(textarea, { target: { value: "This is a sample job description." } });

    expect(textarea).toHaveValue("This is a sample job description.");
  });

  test("updates character counter as text is typed", () => {
    render(<JobInput label="Job Description" />);

    const textarea = screen.getByPlaceholderText("Enter the job description here...");
    const charCounter = screen.getByText("0 / 5000 characters");

    fireEvent.change(textarea, { target: { value: "Hello" } });

    expect(charCounter).toHaveTextContent("5 / 5000 characters");
  });

  test("applies 'char-counter-exceeded' class when text length exceeds 5000", () => {
    render(<JobInput label="Job Description" />);

    const textarea = screen.getByPlaceholderText("Enter the job description here...");

    const longText = "a".repeat(5001);
    fireEvent.change(textarea, { target: { value: longText } });

    const charCounter = screen.getByText("5001 / 5000 characters");

    expect(charCounter).toHaveClass("char-counter-exceeded");
  });


  test("submits the job description on clicking submit button", async () => {
    const mockResponse = {
      data: { message: "Job description submitted successfully" },
    };

    (axios.post as jest.Mock).mockResolvedValueOnce(mockResponse);

    render(<JobInput label="Job Description" />);

    const textarea = screen.getByPlaceholderText("Enter the job description here...");
    const submitButton = screen.getByRole("button", { name: "Submit" });

    fireEvent.change(textarea, { target: { value: "This is a sample job description." } });
    fireEvent.click(submitButton);

    await waitFor(() =>
      expect(axios.post).toHaveBeenCalledWith(
        "http://localhost:8000/api/job-description",
        { job_description: "This is a sample job description." }
      )
    );

    expect(window.alert).toHaveBeenCalledWith("Job description submitted successfully");
  });

  test("shows error alert when submission fails", async () => {
    const mockError = new Error("Network Error");

    (axios.post as jest.Mock).mockRejectedValueOnce(mockError);

    render(<JobInput label="Job Description" />);

    const textarea = screen.getByPlaceholderText("Enter the job description here...");
    const submitButton = screen.getByRole("button", { name: "Submit" });

    fireEvent.change(textarea, { target: { value: "This is a sample job description." } });
    fireEvent.click(submitButton);

    await waitFor(() => expect(axios.post).toHaveBeenCalled());

    expect(window.alert).toHaveBeenCalledWith("Failed to submit the job description. Please try again.");
  });
});
