interface Props {
  llmModels: string[];
  rerankMethods: string[];
  selectedLlmModel: string;
  selectedRerankMethod: string;
  onLlmModelChange: (model: string) => void;
  onRerankMethodChange: (method: string) => void;
}

export default function ModelSelector({
  llmModels,
  rerankMethods,
  selectedLlmModel,
  selectedRerankMethod,
  onLlmModelChange,
  onRerankMethodChange,
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
        <label htmlFor="rerank-method">Reranking Method</label>
        <select
          id="rerank-method"
          value={selectedRerankMethod}
          onChange={(e) => onRerankMethodChange(e.target.value)}
        >
          {rerankMethods.map((method) => (
            <option key={method} value={method}>
              {method === 'zerank-2' ? 'ZeroEntropy (zerank-2)' : 'LLM Reranking'}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
