import { useStore } from '../../store';

function NumberField({ label, value, onChange, min, max, step = 1 }) {
  return (
    <label className="block mb-4">
      <span className="block text-xs font-extrabold uppercase tracking-wider text-gray-600 mb-1">
        {label}
      </span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full bg-gray-50 border border-gray-300 px-3 py-2 text-sm text-black focus:outline-none focus:border-black"
      />
    </label>
  );
}

export default function GlobalSettings() {
  const { global_settings, setGlobal } = useStore();
  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-extrabold text-black mb-1">Global Settings</h2>
      <p className="text-sm text-gray-600 mb-6">Bounds of the simulation timeline.</p>

      <NumberField
        label="Start Year"
        value={global_settings.start_year}
        onChange={(v) => setGlobal({ start_year: v })}
      />
      <NumberField
        label="End Year"
        value={global_settings.end_year}
        onChange={(v) => setGlobal({ end_year: v })}
      />
      <NumberField
        label="Maximum Generations"
        value={global_settings.maximum_generations}
        onChange={(v) => setGlobal({ maximum_generations: v })}
      />
    </div>
  );
}
