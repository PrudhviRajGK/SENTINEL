import React from 'react';
import { Link } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  return (
    <nav className="nav">
      <div className="container nav-container">
        <Link to="/" className="nav-brand">
          <svg className="nav-logo" width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
            <path d="M12 8v8m-4-4h8" stroke="currentColor" strokeWidth="2"/>
          </svg>
          <span className="nav-brand-name">Sentinel</span>
        </Link>
        
        <div className="nav-links">
          <Link to="/" className="nav-link">Product</Link>
          <Link to="/education" className="nav-link">Education</Link>
          <a href="https://github.com" className="nav-link" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
          <Link to="/analyze" className="btn btn-primary btn-sm">
            Try Demo
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
