import React from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';

const HomePage = () => {
  const capabilities = [
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2"/>
          <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ),
      title: 'URL & Domain Analysis',
      description: 'Cross-reference against VirusTotal and URLhaus databases for comprehensive threat assessment'
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ),
      title: 'Phone Number Detection',
      description: 'Identify scam and phishing attempts through web intelligence aggregation'
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ),
      title: 'Message Analysis',
      description: 'Detect phishing patterns in emails and text messages with AI-powered analysis'
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ),
      title: 'Image Inspection',
      description: 'Extract and analyze text from screenshots for embedded threats'
    },
    {
      icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" stroke="currentColor" strokeWidth="2"/>
        </svg>
      ),
      title: 'Cyber Awareness Mode',
      description: 'Interactive education on social engineering and attack patterns'
    }
  ];

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">
              Enterprise threat intelligence,<br />delivered with clarity
            </h1>
            <p className="hero-subtitle">
              Analyze URLs, messages, phone numbers, and images for security threats.
              Powered by AI, trusted by security teams.
            </p>
            <div className="hero-actions">
              <Link to="/analyze" className="btn btn-primary btn-lg">
                Analyze a Threat
              </Link>
              <Link to="/education" className="btn btn-secondary btn-lg">
                Learn How Attacks Work
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="capabilities">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Comprehensive threat analysis</h2>
            <p className="section-subtitle">
              Five core capabilities designed for security professionals
            </p>
          </div>
          
          <div className="capabilities-grid">
            {capabilities.map((capability, index) => (
              <div key={index} className="capability-card">
                <div className="capability-icon">
                  {capability.icon}
                </div>
                <h3 className="capability-title">{capability.title}</h3>
                <p className="capability-description">{capability.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
