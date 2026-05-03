import { useStore } from '../store';
import Dropzone from './Dropzone';
import {
  uploadTitles, uploadTraits, uploadDeaths, uploadNames,
  startGeneration,
} from '../api';

const NAV = [
  { id: 'global', label: 'Global Settings' },
  { id: 'lifecycle', label: 'Life Cycle Modifiers' },
  { id: 'events', label: 'Negative Events' },
  { id: 'titles', label: 'Title Histories' },
];

export default function LeftSidebar() {
  const {
    parsed_files, active_view, setView,
    setParsedTitles, setParsedTraits, setParsedDeaths, setParsedNames,
    isReady, setDrawer, setTaskState, resetTask, buildPayload,
  } = useStore();

  const ready = isReady();

  const handle = (uploader, setter) => async (file) => {
    try {
      const data = await uploader(file);
      setter(data);
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    }
  };

  const onGenerate = async () => {
    resetTask();
    setDrawer(true);
    try {
      const { task_id } = await startGeneration(buildPayload());
      setTaskState({ task_id, task_state: 'PENDING', append_message: 'Submitted to worker.' });
    } catch (err) {
      setTaskState({ task_state: 'FAILURE', task_error: err.message });
    }
  };

  return (
    <aside className="w-[250px] shrink-0 bg-gray-50 border-r border-gray-300 flex flex-col h-full">
      <div className="px-4 py-4 border-b border-gray-300">
        <div className="text-sm font-extrabold text-black uppercase tracking-wider">CK3 History</div>
        <div className="text-xs text-gray-600 mt-0.5">v7.0 Generator</div>
      </div>

      {/* Dropzones */}
      <div className="px-3 py-3 overflow-y-auto flex-1">
        <Dropzone
          label="Landed Titles"
          onFile={handle(uploadTitles, setParsedTitles)}
          filename={parsed_files.titles_filename}
        />
        <Dropzone
          label="Genetic Traits"
          onFile={handle(uploadTraits, setParsedTraits)}
          filename={parsed_files.traits_filename}
        />
        <Dropzone
          label="Death Reasons"
          onFile={handle(uploadDeaths, setParsedDeaths)}
          filename={parsed_files.deaths_filename}
        />
        <Dropzone
          label="Name Lists"
          onFile={handle(uploadNames, setParsedNames)}
          filename={parsed_files.names_filename}
        />

        <div className="border-t border-gray-300 my-4" />

        {/* Navigation */}
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className={[
                'text-left px-3 py-2 text-sm font-extrabold uppercase tracking-wide',
                active_view === item.id ? 'bg-black text-white' : 'text-gray-600 hover:text-black',
              ].join(' ')}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Execution button */}
      <div className="px-3 py-3 border-t border-gray-300">
        <button
          disabled={!ready}
          onClick={onGenerate}
          className={[
            'w-full py-3 text-sm font-extrabold uppercase tracking-wider',
            ready
              ? 'bg-gray-800 text-white hover:bg-black cursor-pointer'
              : 'bg-gray-100 text-gray-600 cursor-not-allowed',
          ].join(' ')}
        >
          Generate Simulation
        </button>
        {!ready && (
          <div className="text-xs text-gray-600 mt-2 text-center">
            Upload Titles + Names to enable.
          </div>
        )}
      </div>
    </aside>
  );
}
