import React, { useState } from 'react';
import './AnalysisPage.css';

const AnalysisPage = () => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!input.trim()) {
      setError('Please enter a URL, message, or phone number');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: input.trim() }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Analysis failed. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', file);

      const response = await fetch('http://localhost:5000/api/analyze/image', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Image analysis failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError('Image analysis failed. Please try again.');
      console.error('Image analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadgeClass = (level) => {
    return `badge badge-${level}`;
  };

  const getRiskPercentage = (level) => {
    const percentages = {
      low: 25,
      medium: 60,
      high: 85,
      critical: 100
    };
    return percentages[level] || 50;
  };

  const formatRiskLevel = (level) => {
    const levels = {
      low: 'Low Risk',
      medium: 'Medium Risk',
      high: 'High Risk',
      critical: 'Critical Risk'
    };
    return levels[level] || level;
  };

  const getRiskDescription = (level) => {
    const descriptions = {
      low: 'Minimal risk indicators detected. Appears legitimate.',
      medium: 'Multiple suspicious indicators detected. Proceed with caution.',
      high: 'High likelihood of malicious intent. Avoid interaction.',
      critical: 'Confirmed threat. Do not interact under any circumstances.'
    };
    return descriptions[level] || 'Risk assessment in progress.';
  };

  return (
    <div className="analysis-page">
      <div className="container">
        <div className="analysis-container">
          <div className="analysis-header">
            <h1 className="analysis-title">Analyze a potential threat</h1>
            <p className="analysis-subtitle">
              Enter a URL, message, phone number, or upload an image
            </p>
          </div>

          <div className="analysis-console">
            <div className="console-input-section">
              <div className="input-group">
                <label htmlFor="threat-input" className="input-label">
                  Input
                </label>
                <textarea
                  id="threat-input"
                  className="input input-textarea"
                  placeholder="https://suspicious-site.com&#10;or&#10;Urgent! Your account will be suspended..."
                  rows="4"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="alert alert-error">
                  {error}
                </div>
              )}

              <div className="console-actions">
                <label className="btn btn-secondary">
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" stroke="currentColor" strokeWidth="2"/>
                  </svg>
                  Upload Image
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                    disabled={loading}
                  />
                </label>
                <button
                  className="btn btn-primary"
                  onClick={handleAnalyze}
                  disabled={loading}
                >
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
              </div>
            </div>

            {/* Results Section */}
            {result && (
              <div className="console-results">
                <div className="results-header">
                  <h2 className="results-title">Analysis Results</h2>
                  <span className={getRiskBadgeClass(result.riskLevel)}>
                    {formatRiskLevel(result.riskLevel)}
                  </span>
                </div>

                <div className="results-content">
                  {/* Summary */}
                  <div className="result-section">
                    <h3 className="result-section-title">Summary</h3>
                    <p className="result-section-content">
                      {result.summary}
                    </p>
                  </div>

                  <hr className="divider" />

                  {/* Risk Assessment */}
                  <div className="result-section">
                    <h3 className="result-section-title">Risk Assessment</h3>
                    <div className="risk-indicator">
                      <div className="risk-indicator-header">
                        <span className="risk-indicator-label">Overall Risk Level</span>
                        <span className="risk-indicator-value">
                          {formatRiskLevel(result.riskLevel)}
                        </span>
                      </div>
                      <div className="risk-indicator-bar">
                        <div
                          className="risk-indicator-fill"
                          style={{ width: `${getRiskPercentage(result.riskLevel)}%` }}
                          data-risk={result.riskLevel}
                        />
                      </div>
                      <p className="risk-indicator-description">
                        {getRiskDescription(result.riskLevel)}
                      </p>
                    </div>
                  </div>

                  <hr className="divider" />

                  {/* Evidence */}
                  {result.evidence && result.evidence.length > 0 && (
                    <>
                      <div className="result-section">
                        <h3 className="result-section-title">Evidence</h3>
                        <div className="table-container">
                          <table className="table">
                            <thead>
                              <tr>
                                <th>Source</th>
                                <th>Status</th>
                                <th>Details</th>
                              </tr>
                            </thead>
                            <tbody>
                              {result.evidence.map((item, index) => (
                                <tr key={index}>
                                  <td>{item.source}</td>
                                  <td>
                                    <span className={`badge badge-${item.status === 'clean' ? 'low' : 'medium'}`}>
                                      {item.status}
                                    </span>
                                  </td>
                                  <td>{item.details}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <hr className="divider" />
                    </>
                  )}

                  {/* Recommendations */}
                  {result.recommendations && result.recommendations.length > 0 && (
                    <div className="result-section">
                      <h3 className="result-section-title">Recommendations</h3>
                      <ul className="result-list">
                        {result.recommendations.map((rec, index) => (
                          <li key={index}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage;
