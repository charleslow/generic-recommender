import { LatencyBreakdown } from '../api/recommend';

interface Props {
  latency: LatencyBreakdown;
}

export default function LatencyDisplay({ latency }: Props) {
  const maxLatency = latency.total_ms;
  
  const items = [
    { label: 'Candidate Generation', value: latency.candidate_generation_ms, className: 'candidate-gen' },
    { label: 'Embedding', value: latency.embedding_ms, className: 'embedding' },
    { label: 'Vector Search', value: latency.vector_search_ms, className: 'vector-search' },
    { label: 'Reranking', value: latency.reranking_ms, className: 'reranking' },
    { label: 'Total', value: latency.total_ms, className: 'total' },
  ];

  return (
    <div className="latency-display">
      <h3>⏱️ Latency Breakdown</h3>
      <div className="latency-bars">
        {items.map((item) => (
          <div key={item.label} className="latency-item">
            <span className="latency-label">{item.label}</span>
            <div className="latency-bar-container">
              <div
                className={`latency-bar ${item.className}`}
                style={{ width: `${(item.value / maxLatency) * 100}%` }}
              />
            </div>
            <span className="latency-value">{item.value.toFixed(0)} ms</span>
          </div>
        ))}
      </div>
    </div>
  );
}
