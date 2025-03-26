import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [backendUrl] = useState('http://localhost:5000');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      // First check if backend is reachable
      await axios.get(`${backendUrl}/health`);
      
      const response = await axios.post(`${backendUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        responseType: 'blob',
      });

      // Check if the response is actually an error
      if (response.headers['content-type'] === 'application/json') {
        const reader = new FileReader();
        reader.onload = () => {
          try {
            const errorData = JSON.parse(reader.result);
            throw new Error(errorData.error || 'An error occurred');
          } catch (e) {
            throw new Error('Failed to parse error response');
          }
        };
        reader.readAsText(response.data);
        return;
      }

      // Create download link for the Excel file
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${file.name.replace('.pdf', '')}_tables.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess(true);
    } catch (err) {
      let errorMessage = 'An error occurred';
      
      if (err.response) {
        if (err.response.data instanceof Blob) {
          const reader = new FileReader();
          reader.onload = () => {
            try {
              const errorData = JSON.parse(reader.result);
              setError(errorData.error || 'An error occurred');
            } catch (e) {
              setError('Failed to process PDF file');
            }
          };
          reader.readAsText(err.response.data);
          return;
        } else if (err.response.data && err.response.data.error) {
          errorMessage = err.response.data.error;
        } else {
          errorMessage = `Server error: ${err.response.status}`;
        }
      } else if (err.request) {
        errorMessage = 'No response from server. Is the backend running?';
      } else {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>PDF Table Extractor</h1>
      </header>
  
      <main className="main-content">
        <form onSubmit={handleSubmit} className="upload-form">
          <div className="file-input-container">
            <input
              type="file"
              id="pdf-upload"
              accept=".pdf"
              onChange={handleFileChange}
              className="file-input"
            />
            <label htmlFor="pdf-upload" className="file-label">
              {file ? file.name : 'Choose PDF file'}
            </label>
          </div>
  
          <button
            type="submit"
            disabled={!file || isLoading}
            className="submit-button"
          >
            {isLoading ? 'Processing...' : 'Extract Tables'}
          </button>
        </form>
  
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
            {error.includes('backend') && (
              <div style={{marginTop: '10px'}}>
                Make sure the Python backend is running on port 5000.
                Run: <code>python app.py</code>
              </div>
            )}
          </div>
        )}
        
        {success && (
          <div className="success-message">
            Tables extracted successfully! Your download should start automatically.
          </div>
        )}
      </main>
    </div>
  );
}
  export default App;