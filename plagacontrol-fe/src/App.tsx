// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Clients from './pages/Clients';
import Products from './pages/Products';
import { useAppStore } from './stores/useAppStore';
import { useEffect } from 'react';

// Placeholder pages (puedes expandirlos después)
const Stations = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Estaciones de Monitoreo</h1>
    <p className="text-gray-600 mt-1">Gestiona tus estaciones con códigos QR</p>
  </div>
);

const Visits = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Visitas de Servicio</h1>
    <p className="text-gray-600 mt-1">Programa y gestiona visitas a clientes</p>
  </div>
);

const Reports = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Reportes</h1>
    <p className="text-gray-600 mt-1">Genera y descarga reportes en PDF</p>
  </div>
);

const Scanner = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">QR Scanner</h1>
    <p className="text-gray-600 mt-1">Escanea códigos QR de estaciones</p>
  </div>
);

const Analytics = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Analíticas</h1>
    <p className="text-gray-600 mt-1">Visualiza métricas y tendencias</p>
  </div>
);

const Settings = () => (
  <div>
    <h1 className="text-2xl font-bold text-gray-900">Configuración</h1>
    <p className="text-gray-600 mt-1">Ajusta las preferencias del sistema</p>
  </div>
);

function App() {
  const { login } = useAppStore();

  // Simular login automático para el prototipo (en producción esto vendría de Cognito)
  useEffect(() => {
    const mockUser = {
      id: '1',
      companyId: 'company-1',
      email: 'admin@plagacontrol.cr',
      name: 'Juan Pérez',
      role: 'admin' as const,
      avatar: undefined,
      createdAt: new Date().toISOString(),
    };

    const mockCompany = {
      id: 'company-1',
      name: 'PlagaControl CR',
      logo: undefined,
      address: 'San José, Costa Rica',
      phone: '8888-0000',
      email: 'info@plagacontrol.cr',
      subscriptionTier: 'professional' as const,
      createdAt: new Date().toISOString(),
    };

    login(mockUser, mockCompany);
  }, [login]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Main App Routes */}
        <Route
          path="/*"
          element={
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/clientes" element={<Clients />} />
                <Route path="/productos" element={<Products />} />
                <Route path="/estaciones" element={<Stations />} />
                <Route path="/visitas" element={<Visits />} />
                <Route path="/reportes" element={<Reports />} />
                <Route path="/scanner" element={<Scanner />} />
                <Route path="/analiticas" element={<Analytics />} />
                <Route path="/configuracion" element={<Settings />} />
                
                {/* 404 */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
