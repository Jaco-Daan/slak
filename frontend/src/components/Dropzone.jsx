import { useState, useCallback } from 'react';

export default function Dropzone({ label, accept = '.txt', onFile, filename, error }) {
  const [hover, setHover] = useState(false);

  const handle = useCallback((e) => {
    e.preventDefault();
    setHover(false);
    const file = e.dataTransfer?.files?.[0] ?? e.target?.files?.[0];
    if (file) onFile(file);
  }, [onFile]);

  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setHover(true); }}
      onDragLeave={() => setHover(false)}
      onDrop={handle}
      className={[
        'block cursor-pointer text-center text-xs',
        'rounded border-2 border-dashed transition-colors',
        'px-3 py-4 mb-3',
        hover ? 'bg-gray-100 border-black' : 'bg-gray-50 border-gray-300',
        error ? 'border-gray-600' : '',
      ].join(' ')}
    >
      <div className="font-extrabold text-black uppercase tracking-wide">{label}</div>
      {filename ? (
        <div className="mt-1 text-gray-600 truncate">
          <span className="text-black">✓</span> {filename}
        </div>
      ) : (
        <div className="mt-1 text-gray-600">drag .txt here or click</div>
      )}
      {error && <div className="mt-1 text-gray-600">{error}</div>}
      <input type="file" accept={accept} onChange={handle} className="hidden" />
    </label>
  );
}
