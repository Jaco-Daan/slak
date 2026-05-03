import { useStore } from '../../store';

function Slider({ label, value, onChange, min, max, step }) {
  return (
    <label className="block mb-5">
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-xs font-extrabold uppercase tracking-wider text-gray-600">{label}</span>
        <span className="text-sm text-black font-light">{value}</span>
      </div>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-black"
      />
    </label>
  );
}

export default function LifeCycleModifiers() {
  const { life_cycle, setLifeCycle } = useStore();
  return (
    <div className="max-w-xl">
      <h2 className="text-2xl font-extrabold text-black mb-1">Life Cycle Modifiers</h2>
      <p className="text-sm text-gray-600 mb-6">Demographic probabilities driving the engine.</p>

      <Slider
        label="Max Age Difference Between Partners"
        value={life_cycle.max_age_difference_between_partners}
        onChange={(v) => setLifeCycle({ max_age_difference_between_partners: v })}
        min={1} max={50} step={1}
      />
      <Slider
        label="Max Children Per Couple"
        value={life_cycle.max_children_per_couple}
        onChange={(v) => setLifeCycle({ max_children_per_couple: v })}
        min={0} max={15} step={1}
      />
      <Slider
        label="Base Fertility Rate"
        value={life_cycle.base_fertility_rate}
        onChange={(v) => setLifeCycle({ base_fertility_rate: v })}
        min={0} max={1} step={0.01}
      />
      <Slider
        label="Male Bastard Chance"
        value={life_cycle.male_bastard_chance}
        onChange={(v) => setLifeCycle({ male_bastard_chance: v })}
        min={0} max={1} step={0.01}
      />
      <Slider
        label="Female Bastard Chance"
        value={life_cycle.female_bastard_chance}
        onChange={(v) => setLifeCycle({ female_bastard_chance: v })}
        min={0} max={1} step={0.01}
      />
    </div>
  );
}
