// Sentinel Frontend Application

class SentinelApp {
  constructor() {
    this.apiEndpoint = '/api/analyze'; // Update with actual backend endpoint
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.setupSmoothScroll();
  }

  setupEventListeners() {
    // Analyze button
    const analyzeBtn = document.querySelector('.console-actions .btn-primary');
    if (analyzeBtn) {
      analyzeBtn.addEventListener('click', () => this.handleAnalyze());
    }

    // Upload image button
    const uploadBtn = document.querySelector('.console-actions .btn-secondary');
    if (uploadBtn) {
      uploadBtn.addEventListener('click', () => this.handleImageUpload());
    }

    // Input field - Enter key
    const input = document.getElementById('threat-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
          this.handleAnalyze();
        }
      });
    }
  }

  setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(anchor.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      });
    });
  }

  async handleAnalyze() {
    const input = document.getElementById('threat-input');
    const value = input.value.trim();

    if (!value) {
      this.showError('Please enter a URL, message, or phone number');
      return;
    }

    // Show loading state
    this.setLoadingState(true);

    try {
      // Call backend API
      const result = await this.analyzeInput(value);
      
      // Display results
      this.displayResults(result);
    } catch (error) {
      this.showError('Analysis failed. Please try again.');
      console.error('Analysis error:', error);
    } finally {
      this.setLoadingState(false);
    }
  }

  async analyzeInput(input) {
    const response = await fetch(this.apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'API request failed');
    }

    return await response.json();
  }

  displayResults(result) {
    const resultsSection = document.querySelector('.console-results');
    if (!resultsSection) return;

    // Update risk badge
    const badge = resultsSection.querySelector('.badge');
    if (badge) {
      badge.className = `badge badge-${result.riskLevel}`;
      badge.textContent = this.formatRiskLevel(result.riskLevel);
    }

    // Update summary
    const summary = resultsSection.querySelector('.result-section-content');
    if (summary) {
      summary.textContent = result.summary;
    }

    // Update risk indicator
    const riskValue = resultsSection.querySelector('.risk-indicator-value');
    const riskFill = resultsSection.querySelector('.risk-indicator-fill');
    const riskDescription = resultsSection.querySelector('.risk-indicator-description');
    
    if (riskValue && riskFill && riskDescription) {
      riskValue.textContent = this.formatRiskLevel(result.riskLevel);
      riskFill.style.width = this.getRiskPercentage(result.riskLevel) + '%';
      riskFill.setAttribute('data-risk', result.riskLevel);
      riskDescription.textContent = this.getRiskDescription(result.riskLevel);
    }

    // Update evidence table
    const tbody = resultsSection.querySelector('.table tbody');
    if (tbody && result.evidence) {
      tbody.innerHTML = result.evidence.map(item => `
        <tr>
          <td>${item.source}</td>
          <td><span class="badge badge-${this.getStatusBadge(item.status)}">${this.formatStatus(item.status)}</span></td>
          <td>${item.details}</td>
        </tr>
      `).join('');
    }

    // Update recommendations
    const recommendations = resultsSection.querySelector('.result-list');
    if (recommendations && result.recommendations) {
      recommendations.innerHTML = result.recommendations.map(rec => `
        <li>${rec}</li>
      `).join('');
    }

    // Show results
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  handleImageUpload() {
    // Create file input
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      this.setLoadingState(true);

      try {
        // Upload and analyze image
        const result = await this.analyzeImage(file);
        this.displayResults(result);
      } catch (error) {
        this.showError('Image analysis failed. Please try again.');
        console.error('Image analysis error:', error);
      } finally {
        this.setLoadingState(false);
      }
    };

    input.click();
  }

  async analyzeImage(file) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(this.apiEndpoint + '/image', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Image upload failed');
    }

    return await response.json();
  }

  setLoadingState(isLoading) {
    const analyzeBtn = document.querySelector('.console-actions .btn-primary');
    const input = document.getElementById('threat-input');

    if (analyzeBtn) {
      analyzeBtn.disabled = isLoading;
      analyzeBtn.textContent = isLoading ? 'Analyzing...' : 'Analyze';
    }

    if (input) {
      input.disabled = isLoading;
    }
  }

  showError(message) {
    // Simple alert for now - could be replaced with a toast notification
    alert(message);
  }

  formatRiskLevel(level) {
    const levels = {
      low: 'Low Risk',
      medium: 'Medium Risk',
      high: 'High Risk',
      critical: 'Critical Risk'
    };
    return levels[level] || level;
  }

  getRiskPercentage(level) {
    const percentages = {
      low: 25,
      medium: 60,
      high: 85,
      critical: 100
    };
    return percentages[level] || 50;
  }

  getRiskDescription(level) {
    const descriptions = {
      low: 'Minimal risk indicators detected. Appears legitimate.',
      medium: 'Multiple suspicious indicators detected. Proceed with caution.',
      high: 'High likelihood of malicious intent. Avoid interaction.',
      critical: 'Confirmed threat. Do not interact under any circumstances.'
    };
    return descriptions[level] || 'Risk assessment in progress.';
  }

  getStatusBadge(status) {
    const badges = {
      clean: 'low',
      suspicious: 'medium',
      malicious: 'high',
      recent: 'medium',
      complete: 'info'
    };
    return badges[status] || 'info';
  }

  formatStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1);
  }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new SentinelApp();
});
