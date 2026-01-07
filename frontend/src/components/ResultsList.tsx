import { Recommendation } from '../api/recommend';

interface Props {
  recommendations: Recommendation[];
}

export default function ResultsList({ recommendations }: Props) {
  if (recommendations.length === 0) {
    return <div className="empty-state">No recommendations yet</div>;
  }

  return (
    <div className="recommendations-list">
      {recommendations.map((rec, index) => (
        <div key={rec.item_id} className="recommendation-card">
          <div className="recommendation-header">
            <span className="recommendation-title">
              {index + 1}. {rec.title}
            </span>
            <span className="recommendation-score">
              Score: {rec.score.toFixed(3)}
            </span>
          </div>
          <p className="recommendation-text">{rec.text}</p>
          <p className="recommendation-id">ID: {rec.item_id}</p>
        </div>
      ))}
    </div>
  );
}
