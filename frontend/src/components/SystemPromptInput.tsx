interface SystemPromptInputProps {
  value: string;
  onChange: (value: string) => void;
  defaultPrompt: string;
}

function SystemPromptInput({ value, onChange, defaultPrompt }: SystemPromptInputProps) {
  const handleReset = () => {
    onChange(defaultPrompt);
  };

  const isModified = value !== defaultPrompt;

  return (
    <div className="system-prompt-input">
      <div className="system-prompt-header">
        <label htmlFor="system-prompt">System Prompt</label>
        {isModified && (
          <button 
            type="button" 
            className="reset-button"
            onClick={handleReset}
            title="Reset to default"
          >
            ↺ Reset
          </button>
        )}
      </div>
      <textarea
        id="system-prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Enter system prompt to configure LLM behavior..."
        rows={3}
      />
      {isModified && (
        <span className="modified-indicator">Modified from default</span>
      )}
    </div>
  );
}

export default SystemPromptInput;
