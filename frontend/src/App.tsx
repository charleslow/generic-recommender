import { useState, useEffect } from 'react';
import { getModels, getRecommendations, RecommendResponse } from './api/recommend';
import ModelSelector from './components/ModelSelector';
import QueryInput from './components/QueryInput';
import LatencyDisplay from './components/LatencyDisplay';
import ResultsList from './components/ResultsList';
import DebugPanel from './components/DebugPanel';

function App() {
  // Available options
  const [llmModels, setLlmModels] = useState<string[]>(['openai/gpt-4o-mini']);
  const [rerankModels, setRerankModels] = useState<string[]>(['zerank-2', 'openai/gpt-4o-mini']);
  
  // Selected options
  const [selectedLlmModel, setSelectedLlmModel] = useState('openai/gpt-4o-mini');
  const [selectedRerankModel, setSelectedRerankModel] = useState('zerank-2');
  
  // Query and results
  const [userContext, setUserContext] = useState('');
  const [result, setResult] = useState<RecommendResponse | null>(null);
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch available models on mount
  useEffect(() => {
    getModels()
      .then((data) => {
        setLlmModels(data.llm_models);
        setRerankModels(data.rerank_models);
        if (data.llm_models.length > 0) {
          setSelectedLlmModel(data.llm_models[0]);
        }
        if (data.rerank_models.length > 0) {
          setSelectedRerankModel(data.rerank_models[0]);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch models:', err);
        // Use defaults if fetch fails
      });
  }, []);

  const handleSubmit = async () => {
    if (!userContext.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await getRecommendations(
        userContext,
        selectedLlmModel,
        selectedRerankModel
      );
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🎯 Generic Recommender</h1>
        <p>Prompt-controlled recommendations with latency insights</p>
      </header>

      <section className="controls">
        <ModelSelector
          llmModels={llmModels}
          rerankModels={rerankModels}
          selectedLlmModel={selectedLlmModel}
          selectedRerankModel={selectedRerankModel}
          onLlmModelChange={setSelectedLlmModel}
          onRerankModelChange={setSelectedRerankModel}
        />
        <QueryInput
          value={userContext}
          onChange={setUserContext}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </section>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <section className="results-section">
        <div className="results-header">
          <h2>Recommendations</h2>
        </div>

        {isLoading && (
          <div className="loading">
            <span className="loading-spinner"></span>
            Processing your request...
          </div>
        )}

        {!isLoading && result && (
          <>
            <LatencyDisplay latency={result.latency} />
            <ResultsList recommendations={result.recommendations} />
            <DebugPanel debug={result.debug} />
          </>
        )}

        {!isLoading && !result && !error && (
          <div className="empty-state">
            Enter a user context above and click "Get Recommendations" to see results
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
