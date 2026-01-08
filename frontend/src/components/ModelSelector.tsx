interface Props {
  llmModels: string[];
  rerankModels: string[];
  embeddingModels: string[];
  selectedLlmModel: string;
  selectedRerankModel: string;
  selectedEmbeddingModel: string;
  onLlmModelChange: (model: string) => void;
  onRerankModelChange: (model: string) => void;
  onEmbeddingModelChange: (model: string) => void;
}

// Display names for embedding models
const EMBEDDING_DISPLAY_NAMES: Record<string, string> = {
  'gist': 'GIST-MiniLM-L6 (local)',
};

export default function ModelSelector({
  llmModels,
  rerankModels,
  embeddingModels,
  selectedLlmModel,
  selectedRerankModel,
  selectedEmbeddingModel,
  onLlmModelChange,
  onRerankModelChange,
  onEmbeddingModelChange,
}: Props) {
  return (
    <div className="control-row">
      <div className="control-group">
        <label htmlFor="llm-model">LLM Model</label>
        <select
          id="llm-model"
          value={selectedLlmModel}
          onChange={(e) => onLlmModelChange(e.target.value)}
        >
          {llmModels.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>
      <div className="control-group">
        <label htmlFor="embedding-model">Embedding Model</label>
        <select
          id="embedding-model"
          value={selectedEmbeddingModel}
          onChange={(e) => onEmbeddingModelChange(e.target.value)}
        >
          {embeddingModels.map((model) => (
            <option key={model} value={model}>
              {EMBEDDING_DISPLAY_NAMES[model] || model}
            </option>
          ))}
        </select>
      </div>
      <div className="control-group">
        <label htmlFor="rerank-model">Reranking Model</label>
        <select
          id="rerank-model"
          value={selectedRerankModel}
          onChange={(e) => onRerankModelChange(e.target.value)}
        >
          {rerankModels.map((model) => (
            <option key={model} value={model}>
              {model.startsWith('zerank') ? `ZeroEntropy (${model})` : model}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
