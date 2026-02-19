// src/pages/Dashboard.tsx
import {
  Users,
  Calendar,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { formatNumber, formatCurrency } from '@/lib/utils';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Mock data
const stats = [
  {
    title: 'Total Clientes',
    value: 147,
    change: 12,
    changeType: 'increase',
    icon: Users,
    color: 'bg-primary-500',
  },
  {
    title: 'Visitas Activas',
    value: 23,
    change: -3,
    changeType: 'decrease',
    icon: Calendar,
    color: 'bg-secondary-500',
  },
  {
    title: 'Completadas (Mes)',
    value: 89,
    change: 18,
    changeType: 'increase',
    icon: CheckCircle2,
    color: 'bg-success',
  },
  {
    title: 'Stock Bajo',
    value: 5,
    change: 2,
    changeType: 'increase',
    icon: AlertTriangle,
    color: 'bg-warning',
  },
];

const monthlyVisits = [
  { month: 'Ene', visitas: 65 },
  { month: 'Feb', visitas: 72 },
  { month: 'Mar', visitas: 81 },
  { month: 'Abr', visitas: 78 },
  { month: 'May', visitas: 85 },
  { month: 'Jun', visitas: 89 },
];

const clientsByType = [
  { name: 'Residencial', value: 85, color: '#22c55e' },
  { name: 'Comercial', value: 42, color: '#3b82f6' },
  { name: 'Industrial', value: 20, color: '#f97316' },
];

const recentVisits = [
  {
    id: '1',
    client: 'Restaurant El Buen Sabor',
    technician: 'Juan Pérez',
    date: '2024-11-26',
    status: 'completed',
  },
  {
    id: '2',
    client: 'Hotel Costa Rica',
    technician: 'María González',
    date: '2024-11-26',
    status: 'in_progress',
  },
  {
    id: '3',
    client: 'Supermercado La Económica',
    technician: 'Carlos Rodríguez',
    date: '2024-11-25',
    status: 'completed',
  },
];

const statusColors = {
  completed: { bg: 'bg-success-light', text: 'text-success-dark', label: 'Completada' },
  in_progress: { bg: 'bg-info-light', text: 'text-info-dark', label: 'En Progreso' },
  scheduled: { bg: 'bg-warning-light', text: 'text-warning-dark', label: 'Programada' },
};

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Vista general de tu sistema de control de plagas</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {formatNumber(stat.value)}
                </p>
                <div className="flex items-center gap-1 mt-2">
                  {stat.changeType === 'increase' ? (
                    <TrendingUp className="w-4 h-4 text-success" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-danger" />
                  )}
                  <span
                    className={`text-sm font-medium ${
                      stat.changeType === 'increase' ? 'text-success' : 'text-danger'
                    }`}
                  >
                    {stat.change > 0 ? '+' : ''}
                    {stat.change}%
                  </span>
                  <span className="text-sm text-gray-500">vs mes anterior</span>
                </div>
              </div>
              <div className={`${stat.color} w-12 h-12 rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Visits Chart */}
        <Card>
          <CardHeader title="Visitas Mensuales" subtitle="Últimos 6 meses" />
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyVisits}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="visitas" fill="#22c55e" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Clients by Type Chart */}
        <Card>
          <CardHeader title="Clientes por Tipo" subtitle="Distribución actual" />
          <CardContent>
            <div className="flex items-center justify-center">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={clientsByType}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {clientsByType.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Visits */}
      <Card>
        <CardHeader 
          title="Visitas Recientes" 
          subtitle="Últimas actividades del equipo"
          action={
            <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Ver todas
            </button>
          }
        />
        <CardContent>
          <div className="space-y-4">
            {recentVisits.map((visit) => (
              <div
                key={visit.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Activity className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{visit.client}</p>
                    <p className="text-sm text-gray-500">Técnico: {visit.technician}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <p className="text-sm text-gray-600">{visit.date}</p>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      statusColors[visit.status as keyof typeof statusColors].bg
                    } ${statusColors[visit.status as keyof typeof statusColors].text}`}
                  >
                    {statusColors[visit.status as keyof typeof statusColors].label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
