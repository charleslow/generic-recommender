interface Props {
  llmModels: string[];
  rerankModels: string[];
  selectedLlmModel: string;
  selectedRerankModel: string;
  onLlmModelChange: (model: string) => void;
  onRerankModelChange: (model: string) => void;
}

export default function ModelSelector({
  llmModels,
  rerankModels,
  selectedLlmModel,
  selectedRerankModel,
  onLlmModelChange,
  onRerankModelChange,
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
