import { Toaster } from '@/components/ui/sonner';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import Index from './pages/Index';
import AuthCallback from './pages/AuthCallback';

const App = () => (
  <>
    <Toaster />
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="*" element={<Index />} />
      </Routes>
    </BrowserRouter>
  </>
);

export default App;
