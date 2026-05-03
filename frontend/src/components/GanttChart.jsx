import { useState, useRef, useEffect, useMemo } from 'react';
import { useStore } from '../store';

const PX_PER_YEAR = 6;
const ROW_HEIGHT = 48;
const LABEL_WIDTH = 240;
const TRANSITION_LABELS = {
  marriage: 'Marriage',
  usurpation: 'Usurpation',
  extinction: 'Extinction',
};

// ------------------------------------------------------------
// Flatten the recursive title tree into a list of visible rows,
// honoring per-title collapse state. Collapsed titles hide all
// of their descendants from the view.
// ------------------------------------------------------------
function flattenTree(titles, collapsed, depth = 0, out = []) {
  if (!titles) return out;
  for (const [tid, node] of Object.entries(titles)) {
    out.push({ id: tid, depth, tier: node.tier, is_landed: node.is_landed, has_children: Object.keys(node.children).length > 0 });
    if (!collapsed[tid] && node.children) {
      flattenTree(node.children, collapsed, depth + 1, out);
    }
  }
  return out;
}

// ------------------------------------------------------------
// Dynasty Block — represents one DynastySequence. The user can
// drag the right edge to resize duration_value, and click on
// the right boundary to open the transition popover.
// ------------------------------------------------------------
function DynastyBlock({ titleId, index, sequence, startYear, totalYears, onResize, onChangeTransition }) {
  const startX = LABEL_WIDTH + (sequence._start_offset || 0) * PX_PER_YEAR;
  const widthYears = sequence.duration_type === 'years'
    ? sequence.duration_value
    : sequence.duration_value * 25; // approximate generation = 25 years for visual
  const width = Math.max(widthYears * PX_PER_YEAR, 40);

  const [dragging, setDragging] = useState(false);
  const startRef = useRef(null);

  const onMouseDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
    startRef.current = { x: e.clientX, durationYears: widthYears };
  };

  useEffect(() => {
    if (!dragging) return;
    const onMove = (e) => {
      const dx = e.clientX - startRef.current.x;
      const newYears = Math.max(5, Math.round(startRef.current.durationYears + dx / PX_PER_YEAR));
      const newValue = sequence.duration_type === 'years'
        ? newYears
        : Math.max(1, Math.round(newYears / 25));
      onResize(newValue);
    };
    const onUp = () => setDragging(false);
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [dragging, sequence.duration_type, onResize]);

  return (
    <div
      className="absolute bg-gray-800 text-white border border-black flex items-center px-2 text-xs"
      style={{
        left: startX,
        top: 8,
        width,
        height: ROW_HEIGHT - 16,
      }}
    >
      <div className="truncate font-extrabold flex-1">{sequence.dynasty_id}</div>
      <div className="text-gray-300 ml-2 text-[10px]">
        {sequence.duration_value}{sequence.duration_type === 'years' ? 'y' : 'g'}
      </div>
      {/* Resize handle */}
      <div
        onMouseDown={onMouseDown}
        className="absolute right-0 top-0 bottom-0 w-2 bg-black cursor-ew-resize hover:bg-gray-600"
      />
      {/* Transition boundary (clickable) — shown after the block */}
      {index >= 0 && (
        <button
          onClick={(e) => { e.stopPropagation(); onChangeTransition(); }}
          className="absolute -right-3 top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-black rounded-full hover:bg-gray-300"
          title={`Transition: ${TRANSITION_LABELS[sequence.transition_method]}`}
        />
      )}
    </div>
  );
}

// ------------------------------------------------------------
// One row in the Gantt — title label + timeline lane
// ------------------------------------------------------------
function GanttRow({ row, sequences, startYear, endYear, onAddBlock, onResize, onChangeTransition, collapsed, toggleCollapse }) {
  const totalYears = endYear - startYear;
  const inheritedFromAncestor = !sequences && row.depth > 0;

  // Compute cumulative offsets in years, so blocks render side-by-side
  const positioned = useMemo(() => {
    if (!sequences) return [];
    let offset = 0;
    return sequences.map((seq) => {
      const yrs = seq.duration_type === 'years' ? seq.duration_value : seq.duration_value * 25;
      const placed = { ...seq, _start_offset: offset };
      offset += yrs;
      return placed;
    });
  }, [sequences]);

  return (
    <div className="flex border-b border-gray-300 hover:bg-gray-50" style={{ height: ROW_HEIGHT }}>
      {/* Label column */}
      <div
        className="shrink-0 flex items-center pr-3 border-r border-gray-300 bg-white text-xs"
        style={{ width: LABEL_WIDTH, paddingLeft: 12 + row.depth * 16 }}
      >
        {row.has_children ? (
          <button
            onClick={() => toggleCollapse(row.id)}
            className="w-4 h-4 mr-1 text-gray-600 hover:text-black"
          >
            {collapsed[row.id] ? '▸' : '▾'}
          </button>
        ) : (
          <span className="w-5" />
        )}
        <span className={['truncate', row.is_landed ? 'text-black' : 'text-gray-600 italic'].join(' ')}>
          {row.id}
        </span>
        <span className="ml-2 text-[10px] text-gray-600 uppercase">{row.tier[0]}</span>
      </div>

      {/* Timeline lane */}
      <div
        className="relative flex-1 bg-white"
        style={{ minWidth: totalYears * PX_PER_YEAR + LABEL_WIDTH }}
      >
        {/* Decade gridlines */}
        {Array.from({ length: Math.floor(totalYears / 10) + 1 }, (_, i) => (
          <div
            key={`${row.id}-grid-${i}`}
            className="absolute top-0 bottom-0 border-l border-gray-100"
            style={{ left: i * 10 * PX_PER_YEAR }}
          />
        ))}

        {positioned.map((seq, i) => (
          <DynastyBlock
            key={i}
            titleId={row.id}
            index={i}
            sequence={seq}
            startYear={startYear}
            totalYears={totalYears}
            onResize={(newVal) => onResize(row.id, i, newVal)}
            onChangeTransition={() => onChangeTransition(row.id, i)}
          />
        ))}

        {/* Add-block button */}
        <button
          onClick={() => onAddBlock(row.id)}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-600 hover:text-black border border-gray-300 hover:border-black px-2 py-1"
        >
          + Block
        </button>

        {inheritedFromAncestor && (
          <div className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-600 italic">
            (cascades from ancestor)
          </div>
        )}
      </div>
    </div>
  );
}

// ------------------------------------------------------------
// Year ruler at the top
// ------------------------------------------------------------
function YearRuler({ startYear, endYear }) {
  const totalYears = endYear - startYear;
  return (
    <div className="flex border-b-2 border-black bg-gray-50 sticky top-0 z-10" style={{ height: 28 }}>
      <div className="shrink-0 border-r border-gray-300" style={{ width: LABEL_WIDTH }}>
        <div className="px-3 py-1 text-[10px] font-extrabold uppercase tracking-wider text-gray-600">Title</div>
      </div>
      <div className="relative flex-1" style={{ minWidth: totalYears * PX_PER_YEAR + LABEL_WIDTH }}>
        {Array.from({ length: Math.floor(totalYears / 25) + 1 }, (_, i) => {
          const y = startYear + i * 25;
          return (
            <div
              key={i}
              className="absolute top-0 bottom-0 border-l border-gray-300 px-1 text-[10px] text-gray-600"
              style={{ left: i * 25 * PX_PER_YEAR }}
            >
              {y}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ------------------------------------------------------------
// Transition popover
// ------------------------------------------------------------
function TransitionPopover({ open, onClose, current, onSelect }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div className="bg-white border border-black p-5 min-w-[280px]" onClick={(e) => e.stopPropagation()}>
        <div className="text-xs font-extrabold uppercase tracking-wider text-gray-600 mb-3">Transition Type</div>
        {Object.entries(TRANSITION_LABELS).map(([key, label]) => (
          <button
            key={key}
            onClick={() => { onSelect(key); onClose(); }}
            className={[
              'block w-full text-left px-3 py-2 mb-1 text-sm border',
              current === key ? 'bg-black text-white border-black' : 'bg-white text-black border-gray-300 hover:border-black',
            ].join(' ')}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ------------------------------------------------------------
// Main exported component
// ------------------------------------------------------------
export default function GanttChart() {
  const { parsed_files, global_settings, title_sequences, setSequences } = useStore();
  const [collapsed, setCollapsed] = useState({});
  const [popover, setPopover] = useState(null); // {titleId, index} | null

  const titles = parsed_files.titles;
  if (!titles) {
    return (
      <div className="p-12 text-sm text-gray-600 italic">
        Upload a landed_titles.txt file in the sidebar to start configuring title histories.
      </div>
    );
  }

  const rows = useMemo(() => flattenTree(titles, collapsed), [titles, collapsed]);

  const toggleCollapse = (id) =>
    setCollapsed((c) => ({ ...c, [id]: !c[id] }));

  const addBlock = (titleId) => {
    const existing = title_sequences[titleId] || [];
    const next = [
      ...existing,
      {
        dynasty_id: `house_${titleId}_${existing.length + 1}`,
        duration_type: 'years',
        duration_value: 50,
        transition_method: existing.length === 0 ? 'marriage' : 'marriage',
      },
    ];
    setSequences(titleId, next);
  };

  const onResize = (titleId, idx, newDuration) => {
    const seqs = [...(title_sequences[titleId] || [])];
    seqs[idx] = { ...seqs[idx], duration_value: newDuration };
    setSequences(titleId, seqs);
  };

  const onChangeTransition = (titleId, idx) => setPopover({ titleId, idx });

  const applyTransition = (method) => {
    if (!popover) return;
    const { titleId, idx } = popover;
    const seqs = [...(title_sequences[titleId] || [])];
    seqs[idx] = { ...seqs[idx], transition_method: method };
    setSequences(titleId, seqs);
  };

  const popoverSeq = popover && (title_sequences[popover.titleId] || [])[popover.idx];

  return (
    <div className="border border-gray-300 bg-white overflow-x-auto overflow-y-auto" style={{ maxHeight: '70vh' }}>
      <div style={{ minWidth: LABEL_WIDTH + (global_settings.end_year - global_settings.start_year) * PX_PER_YEAR + 50 }}>
        <YearRuler startYear={global_settings.start_year} endYear={global_settings.end_year} />
        {rows.map((row) => (
          <GanttRow
            key={row.id}
            row={row}
            sequences={title_sequences[row.id]}
            startYear={global_settings.start_year}
            endYear={global_settings.end_year}
            onAddBlock={addBlock}
            onResize={onResize}
            onChangeTransition={onChangeTransition}
            collapsed={collapsed}
            toggleCollapse={toggleCollapse}
          />
        ))}
      </div>

      <TransitionPopover
        open={Boolean(popover)}
        onClose={() => setPopover(null)}
        current={popoverSeq?.transition_method}
        onSelect={applyTransition}
      />
    </div>
  );
}
