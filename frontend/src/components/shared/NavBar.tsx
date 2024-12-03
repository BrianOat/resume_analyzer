import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import "../../styles/navbar.css";

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo */}
        <div className="navbar-logo">
          <Link to="/">Resume Scanner</Link>
        </div>

        {/* Navigation Links */}
        <div className={`navbar-links ${isOpen ? 'open' : ''}`}>
          <Link to="/login" className="navbar-link">Login</Link>
          <Link to="/inputForm" className="navbar-link">Input</Link>
          <Link to="/dashboard" className="navbar-link">Dashboard</Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
