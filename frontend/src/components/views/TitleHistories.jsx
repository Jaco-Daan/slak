import GanttChart from '../GanttChart';

export default function TitleHistories() {
  return (
    <div>
      <h2 className="text-2xl font-extrabold text-black mb-1">Title Histories</h2>
      <p className="text-sm text-gray-600 mb-6">
        Drop dynasty blocks onto a title's timeline. Drag the right edge to resize the duration.
        Click the boundary node between blocks to set the transition type.
        Sequences cascade to child titles unless explicitly overridden.
      </p>
      <GanttChart />
    </div>
  );
}
