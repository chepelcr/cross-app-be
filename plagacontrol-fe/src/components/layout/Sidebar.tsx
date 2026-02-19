// src/components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom';
import {
  Home,
  Users,
  FlaskConical,
  Calendar,
  MapPin,
  FileText,
  Settings,
  QrCode,
  BarChart3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/stores/useAppStore';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Clientes', href: '/clientes', icon: Users },
  { name: 'Productos', href: '/productos', icon: FlaskConical },
  { name: 'Estaciones', href: '/estaciones', icon: MapPin },
  { name: 'Visitas', href: '/visitas', icon: Calendar },
  { name: 'Reportes', href: '/reportes', icon: FileText },
  { name: 'QR Scanner', href: '/scanner', icon: QrCode },
  { name: 'Analíticas', href: '/analiticas', icon: BarChart3 },
  { name: 'Configuración', href: '/configuracion', icon: Settings },
];

const Sidebar = () => {
  const { sidebarOpen, toggleSidebar, company } = useAppStore();

  return (
    <>
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen bg-white border-r border-gray-200 z-30 transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-200">
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">PC</span>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">PlagaControl</h1>
                <p className="text-xs text-gray-500">{company?.name || 'Sistema'}</p>
              </div>
            </div>
          ) : (
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center mx-auto">
              <span className="text-white font-bold text-lg">PC</span>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'nav-item',
                  isActive && 'nav-item-active',
                  !sidebarOpen && 'justify-center'
                )
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Toggle Button */}
        <button
          onClick={toggleSidebar}
          className="absolute -right-3 top-20 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors"
        >
          {sidebarOpen ? (
            <ChevronLeft className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </aside>

      {/* Spacer */}
      <div
        className={cn(
          'transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      />
    </>
  );
};

export default Sidebar;
