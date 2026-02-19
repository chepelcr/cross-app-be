# 🦟 PlagaControl - Frontend

Sistema de gestión para empresas de control de plagas desarrollado con React, TypeScript y Tailwind CSS.

## 🎨 **Paleta de Colores**

La aplicación utiliza una paleta de colores basada en las mejores prácticas de la industria de control de plagas:

- **Verde Primario (#22c55e)**: Representa naturaleza, salud, soluciones eco-friendly y seguridad
- **Azul Secundario (#3b82f6)**: Transmite profesionalismo, confiabilidad y confianza
- **Naranja Acento (#f97316)**: Indica urgencia y llamadas a la acción
- **Tonos Neutros**: Grises para balance y profesionalismo

## ✨ **Características**

### Implementadas (Sprint 5-6)
- ✅ Dashboard con estadísticas en tiempo real
- ✅ Gestión de clientes con búsqueda y filtros
- ✅ Inventario de productos químicos con alertas de stock bajo
- ✅ Navegación lateral colapsable
- ✅ Componentes UI reutilizables (Button, Input, Card, Badge, Modal)
- ✅ Sistema de estados con Zustand
- ✅ Responsive design
- ✅ Animaciones suaves
- ✅ Gráficos interactivos (Recharts)

### Por Implementar (Sprints 7-12)
- 🔄 Estaciones de monitoreo con códigos QR
- 🔄 Registro de visitas con firma digital
- 🔄 Scanner QR (móvil)
- 🔄 Generación de reportes PDF
- 🔄 Modo offline con sincronización
- 🔄 Autenticación con AWS Cognito
- 🔄 Integración con API backend

## 🚀 **Inicio Rápido**

### Prerrequisitos

- Node.js 18+ 
- npm o yarn

### Instalación

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# La aplicación estará disponible en http://localhost:3000
```

### Build para Producción

```bash
# Crear build optimizado
npm run build

# Preview del build
npm run preview
```

## 📁 **Estructura del Proyecto**

```
src/
├── components/
│   ├── ui/              # Componentes reutilizables
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   └── Modal.tsx
│   ├── layout/          # Componentes de layout
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   └── forms/           # Formularios específicos (futuro)
├── pages/               # Páginas principales
│   ├── Dashboard.tsx
│   ├── Clients.tsx
│   ├── Products.tsx
│   └── ...
├── stores/              # Estado global (Zustand)
│   └── useAppStore.ts
├── types/               # Tipos TypeScript
│   └── index.ts
├── lib/                 # Utilidades
│   └── utils.ts
├── hooks/               # Custom hooks (futuro)
├── assets/              # Imágenes, iconos, etc
├── App.tsx              # Componente raíz con routing
├── main.tsx             # Punto de entrada
└── index.css            # Estilos globales
```

## 🎨 **Sistema de Diseño**

### Componentes UI

Todos los componentes UI están en `src/components/ui/` y son completamente reutilizables:

```tsx
import { Button, Input, Card, Badge, Modal } from '@/components/ui';

// Ejemplo de uso
<Button variant="primary" size="md" leftIcon={<Icon />}>
  Guardar
</Button>

<Badge variant="success">Activo</Badge>

<Input 
  label="Email"
  type="email"
  error="Email inválido"
  leftIcon={<Mail />}
/>
```

### Tailwind CSS

El proyecto usa Tailwind CSS con clases utilitarias personalizadas:

```css
/* Botones */
.btn-primary  /* Botón primario verde */
.btn-secondary /* Botón secundario azul */
.btn-outline  /* Botón con borde */
.btn-danger   /* Botón de peligro */

/* Cards */
.card         /* Card estándar */
.card-elevated /* Card con sombra elevada */

/* Badges */
.badge-success  /* Badge verde */
.badge-warning  /* Badge amarillo */
.badge-danger   /* Badge rojo */
.badge-info     /* Badge azul */
```

## 🔧 **Tecnologías Utilizadas**

### Core
- **React 18** - Framework UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool ultrarrápido
- **React Router v6** - Routing

### UI/UX
- **Tailwind CSS** - Framework CSS utility-first
- **Lucide React** - Iconos modernos
- **Recharts** - Gráficos interactivos
- **date-fns** - Manipulación de fechas

### Estado y Datos
- **Zustand** - State management ligero
- **React Hook Form** - Manejo de formularios
- **Zod** - Validación de esquemas

## 🌐 **Variables de Entorno**

Crea un archivo `.env` en la raíz:

```env
# API Backend (futuro)
VITE_API_URL=https://api.plagacontrol.cr

# AWS Cognito (futuro)
VITE_AWS_REGION=us-east-1
VITE_AWS_USER_POOL_ID=us-east-1_xxxxxx
VITE_AWS_USER_POOL_CLIENT_ID=xxxxxxxxxx

# AWS S3 (futuro)
VITE_AWS_S3_BUCKET=plagacontrol-uploads

# Modo de desarrollo
VITE_DEV_MODE=true
```

## 📱 **Responsive Design**

La aplicación es totalmente responsive con breakpoints:

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px

## 🎯 **Próximos Pasos**

### Sprint 7-8 (App Móvil)
1. Implementar scanner QR con cámara
2. Captura de fotos con geolocalización
3. Firma digital en canvas
4. Modo offline con AsyncStorage/IndexedDB
5. Sincronización automática

### Sprint 9 (PDFs y Reportes)
1. Generación de PDFs en backend
2. Templates personalizables
3. Certificados de servicio
4. Exportación de datos

### Sprint 10-11 (Integración)
1. Conectar con backend AWS Lambda
2. Autenticación Cognito
3. Upload de fotos a S3
4. Sincronización en tiempo real

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 **Licencia**

Este proyecto es privado y propiedad de PlagaControl CR.

## 👥 **Equipo**

- **Frontend Developer**: Sistema generado con IA
- **UI/UX Designer**: Basado en mejores prácticas de la industria
- **Arquitecto**: AWS Cloud Native Architecture

## 📞 **Soporte**

Para soporte técnico: dev@plagacontrol.cr

---

**Desarrollado con ❤️ en Costa Rica 🇨🇷**
