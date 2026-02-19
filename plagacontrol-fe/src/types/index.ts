// src/types/index.ts

export interface User {
  id: string;
  companyId: string;
  email: string;
  name: string;
  role: 'admin' | 'technician' | 'viewer';
  avatar?: string;
  createdAt: string;
}

export interface Company {
  id: string;
  name: string;
  logo?: string;
  address: string;
  phone: string;
  email: string;
  subscriptionTier: 'basic' | 'professional' | 'enterprise';
  createdAt: string;
}

export interface Client {
  id: string;
  companyId: string;
  name: string;
  businessName?: string;
  address: string;
  phone: string;
  email?: string;
  contactPerson: string;
  notes?: string;
  status: 'active' | 'inactive';
  createdAt: string;
  updatedAt: string;
}

export interface ChemicalProduct {
  id: string;
  companyId: string;
  name: string;
  activeIngredient: string;
  brand: string;
  stockQuantity: number;
  unit: 'ml' | 'l' | 'g' | 'kg';
  safetyDataSheetUrl?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export type StationType = 'bait_station' | 'adhesive_trap' | 'light_trap' | 'rodent_trap' | 'other';

export interface MonitoringStation {
  id: string;
  companyId: string;
  clientId: string;
  qrCode: string;
  stationType: StationType;
  locationName: string;
  description?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
  installDate: string;
  status: 'active' | 'inactive' | 'maintenance';
  createdAt: string;
  updatedAt: string;
}

export type VisitStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';

export interface ServiceVisit {
  id: string;
  companyId: string;
  clientId: string;
  technicianId: string;
  visitDate: string;
  scheduledTime?: string;
  status: VisitStatus;
  observations: string;
  photos: string[];
  clientSignatureUrl?: string;
  signedAt?: string;
  reportPdfUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface StationInspection {
  id: string;
  visitId: string;
  stationId: string;
  inspectionData: {
    findings: string;
    consumption?: number;
    condition: 'good' | 'fair' | 'poor';
    action: string;
  };
  scannedAt: string;
}

export interface ProductApplication {
  id: string;
  visitId: string;
  productId: string;
  quantity: number;
  applicationArea: string;
  notes?: string;
}

export interface StatsCardData {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease';
  icon: string;
}

export interface DashboardStats {
  totalClients: number;
  activeVisits: number;
  completedVisitsThisMonth: number;
  lowStockProducts: number;
  monthlyRevenue?: number;
}

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: any;
}

// Form validation types
export interface ClientFormData {
  name: string;
  businessName?: string;
  address: string;
  phone: string;
  email?: string;
  contactPerson: string;
  notes?: string;
}

export interface ProductFormData {
  name: string;
  activeIngredient: string;
  brand: string;
  stockQuantity: number;
  unit: 'ml' | 'l' | 'g' | 'kg';
  notes?: string;
}

export interface VisitFormData {
  clientId: string;
  visitDate: string;
  scheduledTime?: string;
  observations: string;
}

export interface StationFormData {
  clientId: string;
  stationType: StationType;
  locationName: string;
  description?: string;
  coordinates?: {
    lat: number;
    lng: number;
  };
}
