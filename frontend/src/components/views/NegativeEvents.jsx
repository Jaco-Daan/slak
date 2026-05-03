import { useStore } from '../../store';

export default function NegativeEvents() {
  const {
    negative_events, addNegativeEvent, updateNegativeEvent, removeNegativeEvent,
  } = useStore();

  return (
    <div className="max-w-3xl">
      <div className="flex justify-between items-baseline mb-6">
        <div>
          <h2 className="text-2xl font-extrabold text-black mb-1">Negative Events</h2>
          <p className="text-sm text-gray-600">Mortality spikes (plagues, wars) — multiply base mortality during these years.</p>
        </div>
        <button
          onClick={addNegativeEvent}
          className="bg-gray-800 text-white px-4 py-2 text-xs font-extrabold uppercase tracking-wider hover:bg-black"
        >
          + Add Event
        </button>
      </div>

      {negative_events.length === 0 && (
        <div className="text-sm text-gray-600 italic">No events. Add one to spike mortality.</div>
      )}

      <div className="flex flex-col gap-3">
        {negative_events.map((ev) => (
          <div key={ev.id} className="bg-gray-50 border border-gray-300 p-4 grid grid-cols-12 gap-3">
            <input
              className="col-span-4 bg-white border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black"
              value={ev.name}
              onChange={(e) => updateNegativeEvent(ev.id, { name: e.target.value })}
              placeholder="Event name"
            />
            <input
              type="number"
              className="col-span-2 bg-white border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black"
              value={ev.start_year}
              onChange={(e) => updateNegativeEvent(ev.id, { start_year: Number(e.target.value) })}
              placeholder="Start"
            />
            <input
              type="number"
              className="col-span-2 bg-white border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black"
              value={ev.end_year}
              onChange={(e) => updateNegativeEvent(ev.id, { end_year: Number(e.target.value) })}
              placeholder="End"
            />
            <input
              type="number"
              step="0.1"
              className="col-span-2 bg-white border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black"
              value={ev.mortality_multiplier}
              onChange={(e) => updateNegativeEvent(ev.id, { mortality_multiplier: Number(e.target.value) })}
              placeholder="× multiplier"
            />
            <button
              onClick={() => removeNegativeEvent(ev.id)}
              className="col-span-2 text-xs text-gray-600 hover:text-black border border-gray-300 hover:border-black"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
