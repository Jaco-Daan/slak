import { useEffect, useRef } from 'react';
import { useStore } from '../store';
import { fetchStatus, downloadUrl } from '../api';

export default function RightDrawer() {
  const {
    drawer_open, setDrawer,
    task_id, task_state, task_messages, task_result, task_error,
    setTaskState,
  } = useStore();

  const lastMessageRef = useRef(null);

  // Poll the backend every 1.2s while a task is in flight
  useEffect(() => {
    if (!task_id) return;
    if (task_state === 'SUCCESS' || task_state === 'FAILURE') return;

    let cancelled = false;
    const poll = async () => {
      try {
        const data = await fetchStatus(task_id);
        if (cancelled) return;
        const next = { task_state: data.state };
        if (data.message && data.message !== lastMessageRef.current) {
          next.append_message = data.message;
          lastMessageRef.current = data.message;
        }
        if (data.state === 'SUCCESS') {
          next.task_result = data.result;
        } else if (data.state === 'FAILURE') {
          next.task_error = data.error;
        }
        setTaskState(next);
      } catch (err) {
        setTaskState({ task_state: 'FAILURE', task_error: err.message });
      }
    };

    poll();
    const handle = setInterval(poll, 1200);
    return () => {
      cancelled = true;
      clearInterval(handle);
    };
  }, [task_id, task_state, setTaskState]);

  if (!drawer_open) return null;

  return (
    <aside className="w-[30vw] min-w-[360px] shrink-0 bg-gray-50 border-l border-gray-300 h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-300 flex justify-between items-center">
        <div className="text-xs font-extrabold uppercase tracking-wider text-black">
          Generation Log
        </div>
        <button
          onClick={() => setDrawer(false)}
          className="text-gray-600 hover:text-black text-sm"
        >
          ✕
        </button>
      </div>

      {/* Mocked terminal */}
      <div className="flex-1 overflow-y-auto bg-black text-gray-300 font-mono text-xs p-3">
        {task_id && (
          <div className="text-gray-600 mb-2">$ task {task_id.slice(0, 8)}…</div>
        )}
        {task_messages.map((m, i) => (
          <div key={i} className="mb-1">
            <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span>{' '}
            {m}
          </div>
        ))}
        {task_state && task_state !== 'SUCCESS' && task_state !== 'FAILURE' && (
          <div className="text-white">▌ {task_state}…</div>
        )}
        {task_state === 'FAILURE' && (
          <div className="text-gray-300 mt-2">ERROR: {task_error}</div>
        )}
      </div>

      {/* Footer actions */}
      <div className="px-3 py-3 border-t border-gray-300">
        {task_state === 'SUCCESS' ? (
          <>
            <a
              href={downloadUrl(task_id)}
              className="block w-full text-center bg-gray-800 text-white py-3 text-sm font-extrabold uppercase tracking-wider hover:bg-black"
            >
              Download ZIP
            </a>
            {task_result && (
              <div className="text-xs text-gray-600 mt-2 text-center">
                {task_result.characters} characters · {task_result.titles_with_history} titles
              </div>
            )}
          </>
        ) : (
          <div className="text-xs text-gray-600 text-center italic">
            Output will appear here when generation completes.
          </div>
        )}
      </div>
    </aside>
  );
}
