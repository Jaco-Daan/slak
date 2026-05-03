import { useStore } from '../store';
import GlobalSettings from './views/GlobalSettings';
import LifeCycleModifiers from './views/LifeCycleModifiers';
import NegativeEvents from './views/NegativeEvents';
import TitleHistories from './views/TitleHistories';

const VIEWS = {
  global: GlobalSettings,
  lifecycle: LifeCycleModifiers,
  events: NegativeEvents,
  titles: TitleHistories,
};

export default function CenterWorkspace() {
  const { active_view } = useStore();
  const View = VIEWS[active_view] ?? GlobalSettings;
  return (
    <main className="flex-1 overflow-y-auto bg-white p-8">
      <View />
    </main>
  );
}
