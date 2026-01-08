interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export default function QueryInput({ value, onChange, onSubmit, isLoading }: Props) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      onSubmit();
    }
  };

  return (
    <div className="query-input">
      <label htmlFor="user-context">User Context</label>
      <textarea
        id="user-context"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter user context here... e.g. I am a first time job seeker"
        disabled={isLoading}
      />
      <button
        className="submit-btn"
        onClick={onSubmit}
        disabled={isLoading || !value.trim()}
      >
        {isLoading ? (
          <>
            <span className="loading-spinner"></span>
            Getting Recommendations...
          </>
        ) : (
          'Get Recommendations (Ctrl+Enter)'
        )}
      </button>
    </div>
  );
}
