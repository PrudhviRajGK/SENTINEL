import React, { useState, useEffect } from 'react';
import './EducationPage.css';

const EducationPage = () => {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchQuestions();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/education/questions');
      const data = await response.json();
      setQuestions(data.questions || []);
    } catch (error) {
      console.error('Failed to load questions:', error);
    }
  };

  const handleSubmit = async () => {
    if (!answer.trim()) return;

    setLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/education/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: questions[currentIndex],
          answer: answer.trim(),
        }),
      });

      const data = await response.json();
      setFeedback(data.feedback);
    } catch (error) {
      console.error('Failed to check answer:', error);
      setFeedback('Failed to check answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    setAnswer('');
    setFeedback(null);
    setCurrentIndex((prev) => (prev + 1) % questions.length);
  };

  if (questions.length === 0) {
    return (
      <div className="education-page">
        <div className="container">
          <div className="education-loading">
            <p>Loading questions...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="education-page">
      <div className="container">
        <div className="education-container">
          <div className="education-header">
            <h1 className="education-title">Cyber Awareness Training</h1>
            <p className="education-subtitle">
              Test your knowledge of social engineering and cybersecurity threats
            </p>
            <div className="education-progress">
              Question {currentIndex + 1} of {questions.length}
            </div>
          </div>

          <div className="education-console">
            <div className="question-section">
              <h2 className="question-text">{questions[currentIndex]}</h2>
              
              <div className="input-group">
                <label htmlFor="answer-input" className="input-label">
                  Your Answer
                </label>
                <textarea
                  id="answer-input"
                  className="input input-textarea"
                  placeholder="Type your answer here..."
                  rows="4"
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  disabled={loading || feedback !== null}
                />
              </div>

              <div className="question-actions">
                {!feedback ? (
                  <button
                    className="btn btn-primary"
                    onClick={handleSubmit}
                    disabled={loading || !answer.trim()}
                  >
                    {loading ? 'Checking...' : 'Submit Answer'}
                  </button>
                ) : (
                  <button className="btn btn-primary" onClick={handleNext}>
                    Next Question
                  </button>
                )}
              </div>
            </div>

            {feedback && (
              <div className="feedback-section">
                <h3 className="feedback-title">Feedback</h3>
                <div className="feedback-content">
                  {feedback}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationPage;
