import { useState } from 'react';
import { DebugInfo } from '../api/recommend';

interface Props {
  debug: DebugInfo;
}

export default function DebugPanel({ debug }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="debug-section">
      <button
        className="debug-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? '▼ Hide Debug Info' : '▶ Show Debug Info'}
      </button>
      
      {isExpanded && (
        <div className="debug-content">
          <div>
            <h4>Model Used</h4>
            <p>{debug.llm_model_used}</p>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <h4>Reranking Method</h4>
            <p>{debug.rerank_method_used}</p>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <h4>Items Retrieved for Reranking</h4>
            <p>{debug.num_retrieved}</p>
          </div>
          <div style={{ marginTop: '1rem' }}>
            <h4>Synthetic Candidates Generated</h4>
            <ul>
              {debug.synthetic_candidates.map((candidate, i) => (
                <li key={i}>{candidate}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
