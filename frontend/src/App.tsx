import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import './styles/App.css';
import SignUp from './components/SignUp';
import Login from './components/Login';
import ResumeJobInputForm from "./components/form/InputComp";
import Dashboard from "./components/dashboard/Dashboard";
import Navbar from "./components/shared/NavBar";

const App: React.FC = () => {
  return (
    <Router>
      <Navbar /> 
      <Routes>
        {/* Render the Login component as landing page*/}
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/login" element={<Login />} />
        <Route path="/inputForm" element={<ResumeJobInputForm />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
};

export default App;