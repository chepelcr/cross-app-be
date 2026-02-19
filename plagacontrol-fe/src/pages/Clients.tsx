// src/pages/Clients.tsx
import { useState } from 'react';
import { Plus, Search, Edit, Trash2, Eye, Mail, Phone } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';

// Mock data
const clients = [
  {
    id: '1',
    name: 'Restaurant El Buen Sabor',
    contactPerson: 'Ana María López',
    phone: '8888-1234',
    email: 'ana@elbuen sabor.cr',
    address: 'San José, Centro',
    status: 'active',
    lastVisit: '2024-11-20',
  },
  {
    id: '2',
    name: 'Hotel Costa Rica',
    contactPerson: 'Roberto Fernández',
    phone: '8888-5678',
    email: 'roberto@hotelcr.com',
    address: 'Escazú, San José',
    status: 'active',
    lastVisit: '2024-11-25',
  },
  {
    id: '3',
    name: 'Supermercado La Económica',
    contactPerson: 'Carlos Mora',
    phone: '8888-9012',
    email: 'carlos@economica.cr',
    address: 'Alajuela, Centro',
    status: 'inactive',
    lastVisit: '2024-10-15',
  },
];

const Clients = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');

  const filteredClients = clients.filter((client) => {
    const matchesSearch =
      client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      client.contactPerson.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || client.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-600 mt-1">Gestiona tu cartera de clientes</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          Nuevo Cliente
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nombre o contacto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                statusFilter === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todos ({clients.length})
            </button>
            <button
              onClick={() => setStatusFilter('active')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                statusFilter === 'active'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Activos ({clients.filter((c) => c.status === 'active').length})
            </button>
            <button
              onClick={() => setStatusFilter('inactive')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                statusFilter === 'inactive'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Inactivos ({clients.filter((c) => c.status === 'inactive').length})
            </button>
          </div>
        </div>
      </Card>

      {/* Clients Table */}
      <Card className="p-0">
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Contacto</th>
                <th>Teléfono</th>
                <th>Dirección</th>
                <th>Última Visita</th>
                <th>Estado</th>
                <th className="text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredClients.map((client) => (
                <tr key={client.id}>
                  <td>
                    <div>
                      <p className="font-medium text-gray-900">{client.name}</p>
                      <p className="text-sm text-gray-500 flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        {client.email}
                      </p>
                    </div>
                  </td>
                  <td className="text-gray-900">{client.contactPerson}</td>
                  <td>
                    <div className="flex items-center gap-1 text-gray-900">
                      <Phone className="w-3 h-3" />
                      {client.phone}
                    </div>
                  </td>
                  <td className="text-gray-600">{client.address}</td>
                  <td className="text-gray-600">{client.lastVisit}</td>
                  <td>
                    <Badge variant={client.status === 'active' ? 'success' : 'neutral'}>
                      {client.status === 'active' ? 'Activo' : 'Inactivo'}
                    </Badge>
                  </td>
                  <td>
                    <div className="flex items-center justify-end gap-2">
                      <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                        <Edit className="w-4 h-4" />
                      </button>
                      <button className="p-2 text-danger hover:bg-red-50 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredClients.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500">No se encontraron clientes</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Clients;
