// src/pages/Products.tsx
import { useState } from 'react';
import { Plus, Search, Edit, Trash2, AlertCircle, Package } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';

// Mock data
const products = [
  {
    id: '1',
    name: 'Termidor SC',
    activeIngredient: 'Fipronil 9.1%',
    brand: 'BASF',
    stockQuantity: 15,
    unit: 'l',
    minStock: 10,
    lastRestock: '2024-11-15',
  },
  {
    id: '2',
    name: 'Maxforce Quantum',
    activeIngredient: 'Imidacloprid 0.03%',
    brand: 'Bayer',
    stockQuantity: 45,
    unit: 'g',
    minStock: 20,
    lastRestock: '2024-11-10',
  },
  {
    id: '3',
    name: 'Demon WP',
    activeIngredient: 'Cipermetrina 40%',
    brand: 'Syngenta',
    stockQuantity: 3,
    unit: 'kg',
    minStock: 5,
    lastRestock: '2024-10-25',
  },
  {
    id: '4',
    name: 'Premise 200',
    activeIngredient: 'Imidacloprid 21.4%',
    brand: 'Bayer',
    stockQuantity: 8,
    unit: 'l',
    minStock: 5,
    lastRestock: '2024-11-18',
  },
];

const Products = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [stockFilter, setStockFilter] = useState<'all' | 'low' | 'normal'>('all');

  const filteredProducts = products.filter((product) => {
    const matchesSearch =
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.activeIngredient.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.brand.toLowerCase().includes(searchTerm.toLowerCase());
    
    const isLowStock = product.stockQuantity < product.minStock;
    const matchesStock =
      stockFilter === 'all' ||
      (stockFilter === 'low' && isLowStock) ||
      (stockFilter === 'normal' && !isLowStock);
    
    return matchesSearch && matchesStock;
  });

  const lowStockCount = products.filter((p) => p.stockQuantity < p.minStock).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Productos Químicos</h1>
          <p className="text-gray-600 mt-1">Gestiona tu inventario de productos</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          Nuevo Producto
        </Button>
      </div>

      {/* Alert for Low Stock */}
      {lowStockCount > 0 && (
        <div className="bg-warning-light border-l-4 border-warning p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-warning-dark" />
            <div>
              <p className="font-medium text-warning-dark">
                {lowStockCount} producto{lowStockCount > 1 ? 's' : ''} con stock bajo
              </p>
              <p className="text-sm text-warning-dark/80">
                Considera realizar un pedido pronto para mantener el inventario
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por nombre, ingrediente o marca..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          {/* Stock Filter */}
          <div className="flex gap-2">
            <button
              onClick={() => setStockFilter('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                stockFilter === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Todos ({products.length})
            </button>
            <button
              onClick={() => setStockFilter('low')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                stockFilter === 'low'
                  ? 'bg-warning text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Stock Bajo ({lowStockCount})
            </button>
            <button
              onClick={() => setStockFilter('normal')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                stockFilter === 'normal'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Stock Normal ({products.length - lowStockCount})
            </button>
          </div>
        </div>
      </Card>

      {/* Products Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredProducts.map((product) => {
          const isLowStock = product.stockQuantity < product.minStock;
          const stockPercentage = (product.stockQuantity / product.minStock) * 100;
          
          return (
            <Card key={product.id} className="relative">
              {isLowStock && (
                <div className="absolute top-4 right-4">
                  <Badge variant="warning">Stock Bajo</Badge>
                </div>
              )}
              
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-secondary-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Package className="w-6 h-6 text-secondary-600" />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 truncate">{product.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{product.activeIngredient}</p>
                  <p className="text-xs text-gray-500 mt-0.5">Marca: {product.brand}</p>
                </div>
              </div>

              {/* Stock Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-600">Stock Actual</span>
                  <span className="font-semibold text-gray-900">
                    {product.stockQuantity} {product.unit}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      isLowStock ? 'bg-warning' : 'bg-success'
                    }`}
                    style={{ width: `${Math.min(stockPercentage, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Mínimo: {product.minStock} {product.unit}
                </p>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-gray-200">
                <Button variant="outline" size="sm" className="flex-1">
                  <Edit className="w-4 h-4" />
                  Editar
                </Button>
                <Button variant="ghost" size="sm">
                  <Trash2 className="w-4 h-4 text-danger" />
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      {filteredProducts.length === 0 && (
        <Card className="text-center py-12">
          <p className="text-gray-500">No se encontraron productos</p>
        </Card>
      )}
    </div>
  );
};

export default Products;
