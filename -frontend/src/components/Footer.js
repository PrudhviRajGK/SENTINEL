import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-content">
          <div className="footer-brand">
            <svg className="footer-logo" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 8v8m-4-4h8" stroke="currentColor" strokeWidth="2"/>
            </svg>
            <span className="footer-brand-name">Sentinel</span>
          </div>
          <div className="footer-links">
            <Link to="/" className="footer-link">Documentation</Link>
            <a href="https://github.com" className="footer-link" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            <Link to="/" className="footer-link">Privacy</Link>
            <Link to="/" className="footer-link">Terms</Link>
          </div>
        </div>
        <div className="footer-bottom">
          <p className="footer-copyright">
            © 2026 Sentinel. Enterprise threat intelligence platform.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
