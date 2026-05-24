import GanttChart from '../GanttChart';

export default function TitleHistories() {
  return (
    <div>
      <h2 className="text-2xl font-extrabold text-black dark:text-white mb-1">Title Histories</h2>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        Existing rulers from the uploaded history show as grey locked bars and are never
        overwritten. Assign a dynasty to each open gap (vacant for more than 50 years, within
        the Start/End window) to have the generator fill it — generated rulers are inserted into
        the original history without touching the existing blocks.
      </p>
      <GanttChart />
    </div>
  );
}
