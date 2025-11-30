import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import GanttView from './pages/GanttView';
import Vendors from './pages/Vendors';
import VendorDetail from './pages/VendorDetail';
import Alerts from './pages/Alerts';

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/gantt" element={<GanttView />} />
          <Route path="/vendors" element={<Vendors />} />
          <Route path="/vendors/:id" element={<VendorDetail />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;
