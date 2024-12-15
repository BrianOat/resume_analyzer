import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from "axios";
import "../styles/styles.css"; // General styles
import "../styles/form/signup.css"; // Page-specific styles
const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000'; // Fallback to localhost in dev


const SignUp: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: "", 
        password: "",
        confirmPassword: "",
        username: "", 

    });
    const [passwordStrength, setPasswordStrength] = useState("")
    const [error, setError] = useState("");
    
    //Setting values for formData after user input
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        if (e.target.name === "password") {
            setPasswordStrength(checkPasswordStrength(e.target.value));
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        //Validate passwords match
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        if (passwordStrength === "Weak") {
            setError("Password is too weak.");
            return;
        }

        //Prepare payload for backend
        const payload = {
            email: formData.email, 
            password: formData.password,
            username: formData.username,
        };

        //Using Axios to send to backend
        try {
            const response = await axios.post(`${backendUrl}/api/register`, payload);
            //console.log("Registration successful:", response.data);
            alert(response.data.message);
            setError("");
            navigate('/login');
        } catch (err) {
            alert("Failed to register account. Please try again.");
            setError("Registration failed");
        }
    };

    const checkPasswordStrength = (password: string): string => {
        const strengthCriteria = [
            { regex: /.{8,}/, message: "at least 8 characters" },
            { regex: /[A-Z]/, message: "an uppercase letter" },
            { regex: /[a-z]/, message: "a lowercase letter" },
            { regex: /[0-9]/, message: "a number" },
            { regex: /[^A-Za-z0-9]/, message: "a special character" },
        ];

        const passedCriteria = strengthCriteria.filter(criteria => criteria.regex.test(password)).length;
        console.log("Password strength criteria met:", passedCriteria); // Debugging

        if (passedCriteria === 5) return "Strong";
        if (passedCriteria >= 3) return "Moderate";
        return "Weak";
    };

    return (
        <div className="container">
            <div className="form-wrapper signup-wrapper">
                <h2>Sign Up</h2>
                <form onSubmit={handleSubmit}>
                    <input
                        type="email"
                        name="email"
                        placeholder="Email"
                        value={formData.email}
                        onChange={handleChange}
                    />
                    <input
                        type="text"
                        name="username"
                        placeholder="Username"
                        value={formData.username}
                        onChange={handleChange}
                    />
                    <input
                        type="password"
                        name="password"
                        placeholder="Password"
                        value={formData.password}
                        onChange={handleChange}
                    />
                    {passwordStrength && (
                        <p className={`password-strength ${passwordStrength.toLowerCase()}`}>
                            Password Strength: {passwordStrength}
                        </p>
                    )}
                    <input
                        type="password"
                        name="confirmPassword"
                        placeholder="Confirm Password"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                    />
                    {error && <p>{error}</p>}
                    <button type="submit">Sign Up</button>
                </form>
                <div className="link">
                    <a href="/login">Already have an account? Login here</a> 
                </div>   
            </div>
        </div>
    );
};

export default SignUp;
