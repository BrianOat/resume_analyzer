import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axios from "axios";
import { BrowserRouter as Router, useNavigate } from "react-router-dom";
import Login from "../components/Login";
import '@testing-library/jest-dom';

// Mock axios and useNavigate
jest.mock("axios");
jest.mock("react-router-dom", () => ({
  useNavigate: jest.fn(),
}));


describe("Login Component", () => {

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders form fields and button", () => {
    render(
        <Login />
    );

    expect(screen.getByPlaceholderText("Email")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Login" })).toBeInTheDocument();
  });
  
  test("submits the form with valid input", async () => {
    const mockResponse = {
      data: { token: "fake-token" },
    };

    (axios.post as jest.Mock).mockResolvedValueOnce(mockResponse);

    render(
        <Login />
    );

    
    userEvent.type(screen.getByPlaceholderText("Email"), "user@example.com");
    userEvent.type(screen.getByPlaceholderText("Password"), "password123");
    userEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => 
        expect(axios.post).toHaveBeenCalledWith("http://localhost:8000/api/login", {
            email: "user@example.com",
            password: "password123",
        })
    );

  });
  
});
