/**
 * App — Root application component with routing.
 */
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './shared/Layout';
import DashboardPage from './features/dashboard/DashboardPage';
import CaseOverviewPage from './features/case/CaseOverviewPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,   // 30 seconds
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/case/:caseId" element={<CaseOverviewPage />} />
            {/* Phase 2+: Additional routes will be added here */}
            {/* <Route path="/case/:caseId/documents" element={<DocumentsPage />} /> */}
            {/* <Route path="/case/:caseId/analysis" element={<AnalysisPage />} /> */}
            {/* <Route path="/case/:caseId/report" element={<ReportPage />} /> */}
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
