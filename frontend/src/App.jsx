import LeftSidebar from './components/LeftSidebar';
import CenterWorkspace from './components/CenterWorkspace';
import RightDrawer from './components/RightDrawer';

export default function App() {
  return (
    <div className="h-full flex">
      <LeftSidebar />
      <CenterWorkspace />
      <RightDrawer />
    </div>
  );
}
