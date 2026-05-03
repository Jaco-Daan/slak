// Zustand global state — sole source of truth (spec ch. 3).
// Serialized into JSON and POSTed to /generate when the user clicks
// "Generate Simulation".

import { create } from 'zustand';

export const useStore = create((set, get) => ({
  // Spec 3.1 — Global Settings
  global_settings: {
    start_year: 6800,
    end_year: 7000,
    maximum_generations: 30,
  },

  // Life Cycle Modifiers
  life_cycle: {
    max_age_difference_between_partners: 20,
    max_children_per_couple: 6,
    base_fertility_rate: 0.35,
    male_bastard_chance: 0.05,
    female_bastard_chance: 0.02,
  },

  // Negative Events
  negative_events: [],

  // Parsed File Data — populated as the user drops files
  parsed_files: {
    titles_txt: null,
    traits_txt: null,
    deaths_txt: null,
    name_lists: {},
    // UI-only previews
    titles: null,           // recursive title tree
    traits: [],             // genetic trait registry
    deaths: [],             // death reasons
    titles_filename: null,
    traits_filename: null,
    deaths_filename: null,
    names_filename: null,
  },

  // Title Sequences — keyed by title id, value = ordered array of dynasty blocks
  title_sequences: {},

  // UI navigation
  active_view: 'global',  // 'global' | 'lifecycle' | 'events' | 'titles'
  drawer_open: false,

  // Simulation status
  task_id: null,
  task_state: null,
  task_messages: [],
  task_result: null,
  task_error: null,

  // ----- Setters -----
  setGlobal: (patch) => set((s) => ({ global_settings: { ...s.global_settings, ...patch } })),
  setLifeCycle: (patch) => set((s) => ({ life_cycle: { ...s.life_cycle, ...patch } })),

  addNegativeEvent: () => set((s) => ({
    negative_events: [
      ...s.negative_events,
      {
        id: crypto.randomUUID(),
        name: 'New Event',
        start_year: s.global_settings.start_year,
        end_year: s.global_settings.start_year + 5,
        mortality_multiplier: 5.0,
      },
    ],
  })),
  updateNegativeEvent: (id, patch) => set((s) => ({
    negative_events: s.negative_events.map((e) => (e.id === id ? { ...e, ...patch } : e)),
  })),
  removeNegativeEvent: (id) => set((s) => ({
    negative_events: s.negative_events.filter((e) => e.id !== id),
  })),

  setParsedTitles: (data) => set((s) => ({
    parsed_files: {
      ...s.parsed_files,
      titles_txt: data.raw,
      titles: data.titles,
      titles_filename: data.filename,
    },
  })),
  setParsedTraits: (data) => set((s) => ({
    parsed_files: {
      ...s.parsed_files,
      traits_txt: data.raw,
      traits: data.traits,
      traits_filename: data.filename,
    },
  })),
  setParsedDeaths: (data) => set((s) => ({
    parsed_files: {
      ...s.parsed_files,
      deaths_txt: data.raw,
      deaths: data.deaths,
      deaths_filename: data.filename,
    },
  })),
  setParsedNames: (data) => set((s) => ({
    parsed_files: {
      ...s.parsed_files,
      name_lists: data.name_lists,
      names_filename: data.filename,
    },
  })),

  setSequences: (titleId, sequences) => set((s) => ({
    title_sequences: { ...s.title_sequences, [titleId]: sequences },
  })),

  setView: (view) => set({ active_view: view }),
  setDrawer: (open) => set({ drawer_open: open }),

  setTaskState: (patch) => set((s) => ({
    task_id: patch.task_id ?? s.task_id,
    task_state: patch.task_state ?? s.task_state,
    task_result: patch.task_result ?? s.task_result,
    task_error: patch.task_error ?? s.task_error,
    task_messages: patch.append_message
      ? [...s.task_messages, patch.append_message]
      : (patch.task_messages ?? s.task_messages),
  })),
  resetTask: () => set({ task_id: null, task_state: null, task_result: null, task_error: null, task_messages: [] }),

  // Build the JSON payload for /generate
  buildPayload: () => {
    const s = get();
    return {
      global_settings: s.global_settings,
      life_cycle: s.life_cycle,
      negative_events: s.negative_events.map(({ id, name, start_year, end_year, mortality_multiplier }) =>
        ({ id, name, start_year, end_year, mortality_multiplier })),
      parsed_files: {
        titles_txt: s.parsed_files.titles_txt,
        traits_txt: s.parsed_files.traits_txt,
        deaths_txt: s.parsed_files.deaths_txt,
        name_lists: s.parsed_files.name_lists,
      },
      title_sequences: s.title_sequences,
    };
  },

  isReady: () => {
    const s = get();
    return Boolean(s.parsed_files.titles_txt) && Object.keys(s.parsed_files.name_lists).length > 0;
  },
}));
