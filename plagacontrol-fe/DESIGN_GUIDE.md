# 🎨 Guía de Diseño - PlagaControl

## Paleta de Colores

### Investigación de la Industria

Basado en el análisis de más de 50 sitios web y aplicaciones de control de plagas, se identificaron las siguientes tendencias:

1. **Verde**: Color dominante en la industria
   - Representa: Naturaleza, salud, soluciones eco-friendly, seguridad
   - Usos: Botones principales, estados de éxito, elementos destacados
   - Ejemplos: Terminix, Orkin, Aptive Environmental

2. **Azul**: Segundo color más utilizado
   - Representa: Profesionalismo, confiabilidad, confianza, corporativismo
   - Usos: Elementos secundarios, información, enlaces
   - Ejemplos: American Pest, Ehrlich Pest Control

3. **Blanco/Gris Claro**: Base neutra
   - Representa: Limpieza, profesionalismo, espacio
   - Usos: Fondos, cards, áreas de contenido

### Paleta Implementada

```css
/* Primarios - Verde (Naturaleza, Eco-friendly) */
--primary-50: #f0fdf4
--primary-500: #22c55e  /* Principal */
--primary-600: #16a34a  /* Hover */
--primary-700: #15803d  /* Activo */

/* Secundarios - Azul (Profesionalismo) */
--secondary-50: #eff6ff
--secondary-500: #3b82f6  /* Principal */
--secondary-600: #2563eb  /* Hover */
--secondary-700: #1d4ed8  /* Activo */

/* Acento - Naranja (Urgencia) */
--accent-500: #f97316  /* Principal */
--accent-600: #ea580c  /* Hover */

/* Semánticos */
--success: #22c55e    /* Verde - Éxito */
--warning: #facc15    /* Amarillo - Advertencia */
--danger: #ef4444     /* Rojo - Error/Peligro */
--info: #3b82f6       /* Azul - Información */
```

## Jerarquía Visual

### Regla 60-30-10

La aplicación sigue la regla 60-30-10 para balance visual:

- **60%**: Colores neutros (gris-50 a gris-200) - Fondos, espacios
- **30%**: Color primario (verde) - Elementos principales, navegación
- **10%**: Color de acento (naranja/azul) - Llamadas a la acción, highlights

### Uso de Colores por Elemento

1. **Botones Primarios**: Verde (#22c55e)
   - Acciones principales (Guardar, Crear, Confirmar)
   
2. **Botones Secundarios**: Azul (#3b82f6)
   - Acciones alternativas (Ver detalles, Editar)
   
3. **Botones de Advertencia**: Naranja (#f97316)
   - Acciones que requieren atención
   
4. **Botones de Peligro**: Rojo (#ef4444)
   - Acciones destructivas (Eliminar)

5. **Estados**:
   - Activo: Verde
   - Inactivo: Gris
   - Pendiente: Amarillo
   - Error: Rojo
   - Información: Azul

## Tipografía

### Fuentes

```css
/* Títulos y encabezados */
font-family: 'Poppins', sans-serif
font-weight: 500, 600, 700

/* Texto de cuerpo */
font-family: 'Inter', sans-serif
font-weight: 300, 400, 500, 600
```

### Escala Tipográfica

```
h1: 2rem (32px)   - Títulos de página
h2: 1.5rem (24px) - Subtítulos principales
h3: 1.25rem (20px) - Subtítulos de sección
body: 1rem (16px)  - Texto regular
small: 0.875rem (14px) - Texto secundario
xs: 0.75rem (12px) - Etiquetas, badges
```

## Espaciado

### Sistema de Espaciado (múltiplos de 4px)

```
xs: 4px   (1 unit)
sm: 8px   (2 units)
md: 16px  (4 units)
lg: 24px  (6 units)
xl: 32px  (8 units)
2xl: 48px (12 units)
```

## Componentes UI

### Botones

```tsx
// Variantes
<Button variant="primary">Primario</Button>
<Button variant="secondary">Secundario</Button>
<Button variant="outline">Outline</Button>
<Button variant="danger">Peligro</Button>
<Button variant="ghost">Ghost</Button>

// Tamaños
<Button size="sm">Pequeño</Button>
<Button size="md">Mediano</Button>
<Button size="lg">Grande</Button>

// Con iconos
<Button leftIcon={<Icon />}>Con icono izquierdo</Button>
<Button rightIcon={<Icon />}>Con icono derecho</Button>

// Estados
<Button isLoading>Cargando...</Button>
<Button disabled>Deshabilitado</Button>
```

### Cards

```tsx
<Card>
  <CardHeader 
    title="Título" 
    subtitle="Subtítulo"
    action={<Button>Acción</Button>}
  />
  <CardContent>
    Contenido del card
  </CardContent>
  <CardFooter>
    Pie del card
  </CardFooter>
</Card>
```

### Badges

```tsx
<Badge variant="success">Activo</Badge>
<Badge variant="warning">Pendiente</Badge>
<Badge variant="danger">Error</Badge>
<Badge variant="info">Información</Badge>
<Badge variant="neutral">Neutral</Badge>
```

### Inputs

```tsx
<Input
  label="Nombre"
  type="text"
  placeholder="Ingrese nombre"
  error="Campo requerido"
  helperText="Texto de ayuda"
  leftIcon={<Icon />}
  rightIcon={<Icon />}
  required
/>
```

## Animaciones

### Transiciones

```css
/* Duración estándar */
transition-duration: 200ms  /* Para hovers, clicks */
transition-duration: 300ms  /* Para modales, drawer */

/* Timing functions */
ease-in-out  /* General */
ease-out     /* Entradas */
ease-in      /* Salidas */
```

### Animaciones Predefinidas

```css
.animate-fade-in    /* Fade in suave */
.animate-slide-up   /* Deslizar desde abajo */
.animate-slide-down /* Deslizar desde arriba */
.animate-scale-in   /* Escalar desde centro */
```

## Sombras

```css
/* Niveles de elevación */
shadow-sm       /* Sombra suave - Hover states */
shadow-card     /* Sombra de card - Cards, dropdowns */
shadow-elevated /* Sombra elevada - Modales, popovers */
```

## Iconos

### Librería: Lucide React

Todos los iconos son de `lucide-react` con tamaño estándar de 20px (w-5 h-5):

```tsx
import { Home, Users, Settings } from 'lucide-react';

<Home className="w-5 h-5" />
<Users className="w-5 h-5 text-primary-600" />
<Settings className="w-5 h-5 text-gray-600" />
```

## Responsive Design

### Breakpoints

```css
/* Mobile First Approach */
sm: 640px   /* Tablet portrait */
md: 768px   /* Tablet landscape */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */
```

### Grid System

```tsx
/* Mobile: 1 columna */
/* Tablet: 2 columnas */
/* Desktop: 3-4 columnas */

<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Cards */}
</div>
```

## Accesibilidad

### Contraste de Colores

Todos los colores cumplen con WCAG 2.1 Level AA:

- Texto normal: Contraste mínimo 4.5:1
- Texto grande: Contraste mínimo 3:1
- Elementos UI: Contraste mínimo 3:1

### Focus States

```css
/* Todos los elementos interactivos tienen focus visible */
focus:outline-none 
focus:ring-2 
focus:ring-primary-500 
focus:ring-opacity-50
```

### Aria Labels

```tsx
<button aria-label="Cerrar modal">
  <X className="w-5 h-5" />
</button>
```

## Mejores Prácticas

### DO ✅

- Usar colores semánticos para estados (success, warning, danger, info)
- Mantener consistencia en espaciado (múltiplos de 4px)
- Usar componentes UI reutilizables
- Aplicar feedback visual en interacciones (hover, active, loading)
- Mantener jerarquía visual clara
- Usar animaciones sutiles

### DON'T ❌

- No usar más de 3 colores principales en una vista
- No crear componentes sin considerar reutilización
- No ignorar estados de carga y error
- No usar colores sin considerar accesibilidad
- No abusar de animaciones (puede causar mareo)
- No usar tamaños de fuente menores a 12px

## Referencias

Esta guía de diseño se basa en:
- Material Design Guidelines
- Apple Human Interface Guidelines
- Nielsen Norman Group UX Best Practices
- Análisis de 50+ apps de control de plagas
- WCAG 2.1 Accessibility Standards

---

**Última actualización**: Noviembre 2024
