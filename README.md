# Sistema de Comandas - Restaurante 🍽️

Sistema de comandas desarrollado en Python con interfaz gráfica táctil, diseñado específicamente para restaurantes, bares y establecimientos gastronómicos.

## 🚀 Características Principales

- **Interfaz Táctil**: Diseño optimizado para pantallas táctiles
- **Gestión de Mesas**: Control completo de mesas y su estado
- **Comandas Digitales**: Creación y envío de comandas a cocina
- **Productos por Categorías**: Organización intuitiva del menú
- **Tickets de Comanda**: Impresión automática de tickets para cocina
- **Observaciones**: Notas especiales por producto y comanda general
- **Multi-usuario**: Sistema de autenticación para meseros y administradores
- **Tiempo Real**: Actualizaciones inmediatas del estado de mesas

## 📋 Requisitos del Sistema

- Python 3.8 o superior
- Windows 10/11 (recomendado para pantallas táctiles)
- Pantalla táctil (opcional pero recomendado)

### Dependencias Python

```txt
tkinter (incluido en Python)
sqlite3 (incluido en Python)
pandas
openpyxl
fpdf
Pillow (PIL)
```

## 🛠️ Instalación para Desarrollo

1. **Clonar o descargar el proyecto:**
   ```bash
   cd c:\Proyectos\ProyectoComanda
   ```

2. **Instalar dependencias:**
   ```bash
   pip install pandas openpyxl fpdf Pillow
   ```

3. **Ejecutar el programa:**
   ```bash
   python sistema-comandas.py
   ```

## 📦 Generar Ejecutable

Para crear un archivo ejecutable (.exe):

### Instalar PyInstaller:
```bash
pip install pyinstaller
```

### Generar el ejecutable:
```bash
pyinstaller --onefile --windowed --add-data "img;img" --icon "img\comanda.ico" --clean sistema-comandas.py
```

## 🎯 Uso del Sistema

### Primera Ejecución
1. Al abrir por primera vez, se creará automáticamente la base de datos
2. Usuario administrador por defecto: **Administrador** / **admin123**
3. Se incluyen productos y mesas de ejemplo

### Flujo de Trabajo

#### Para Meseros:
1. **Login** con credenciales de usuario
2. **Seleccionar Mesa** desde el panel principal
3. **Elegir Categoría** de productos del menú
4. **Agregar Productos** tocando los botones de cada item
5. **Añadir Observaciones** especiales si es necesario
6. **Enviar Comanda** a cocina
7. **Generar Ticket** de comanda para cocina

#### Interfaz Táctil Optimizada:
- **Botones Grandes**: Diseñados para dedos, no para mouse
- **Colores Intuitivos**: Verde (disponible), Rojo (ocupado), etc.
- **Categorías Visuales**: Cada categoría tiene color diferente
- **Texto Grande**: Fácil lectura en pantallas táctiles

## 📁 Estructura del Proyecto

```
ProyectoComanda/
├── sistema-comandas.py     # Archivo principal del sistema
├── img/                    # Recursos de imágenes
│   └── comanda.ico        # Ícono del programa
├── tickets/               # Tickets de comanda generados
├── comandas.db           # Base de datos SQLite (auto-generada)
└── README.md             # Este archivo
```

## 🗄️ Base de Datos

El sistema utiliza SQLite con las siguientes tablas:

- **productos**: Menú de productos con categorías y precios
- **mesas**: Información y estado de mesas del restaurante
- **comandas**: Registro de comandas enviadas a cocina
- **items_comanda**: Detalles de productos por comanda
- **usuarios**: Cuentas de meseros y administradores

## 🍽️ Categorías de Productos Predefinidas

- **🍔 Hamburguesas** - Color: Rojo
- **🍕 Pizzas** - Color: Turquesa
- **🍖 Platos Principales** - Color: Azul
- **🥗 Ensaladas** - Color: Verde
- **🍟 Guarniciones** - Color: Amarillo
- **🥤 Bebidas** - Color: Azul claro
- **☕ Cafetería** - Color: Púrpura
- **📂 Otros** - Color: Rosa

## 📊 Estados de Mesa

- **🟢 Libre**: Mesa disponible para nuevos clientes
- **🔴 Ocupada**: Mesa con comanda activa
- **🟡 Pendiente**: Mesa con comanda enviada pero no finalizada

## 🎨 Características de Diseño Táctil

### Botones Optimizados:
- **Tamaño Mínimo**: 60x40 pixels para fácil toque
- **Espaciado**: Separación adecuada entre elementos
- **Feedback Visual**: Cambios de color al interactuar
- **Texto Legible**: Fuentes grandes y contraste alto

### Layout Intuitivo:
- **Panel de Mesas**: Visión rápida del estado del restaurante
- **Categorías Horizontales**: Navegación fácil del menú
- **Grid de Productos**: Presentación clara de opciones
- **Comanda Lateral**: Vista constante del pedido actual

## 🔧 Configuración Avanzada

### Personalización de Productos:
- Agregar/editar productos desde panel de administración
- Configurar categorías personalizadas
- Establecer precios y descripciones
- Activar/desactivar disponibilidad

### Gestión de Mesas:
- Configurar número y capacidad de mesas
- Modificar estados manualmente
- Asignar comandas a mesas específicas

## 🚨 Solución de Problemas

### Pantalla Táctil No Responde:
1. Verificar drivers de pantalla táctil
2. Calibrar pantalla en configuración de Windows
3. Ajustar configuración de toque en el sistema

### Base de Datos Corrupta:
- Eliminar archivo `comandas.db`
- El sistema recreará la base automáticamente

### Problemas de Rendimiento:
- Cerrar aplicaciones innecesarias
- Verificar que la pantalla táctil esté optimizada
- Reiniciar el sistema si es necesario

## 🔐 Niveles de Usuario

### Meseros:
- Acceso a creación de comandas
- Selección de mesas
- Envío de pedidos a cocina

### Administradores:
- Todas las funciones de meseros
- Gestión de productos y menú
- Configuración de mesas
- Reportes y estadísticas
- Gestión de usuarios

## 📝 Diferencias con Sistema POS

| Característica | Sistema POS | Sistema Comandas |
|----------------|-------------|------------------|
| **Propósito** | Ventas y cobro | Comandas a cocina |
| **Interfaz** | Tradicional | Táctil optimizada |
| **Stock** | Control completo | No aplica |
| **Mesas** | No | Sí |
| **Tickets** | Facturación | Comanda cocina |
| **Pago** | Múltiples métodos | No aplica |

## 🤝 Contribución

Este proyecto está diseñado para restaurantes y puede ser personalizado según necesidades específicas.

## 📄 Licencia

Proyecto desarrollado para uso comercial en restaurantes y establecimientos gastronómicos.

---
**Desarrollado por**: JuanM96  
**Basado en**: ProyectoKiosco  
**Fecha**: Octubre 2025  
**Versión**: 1.0

## 🆕 Próximas Características

- [ ] Gestión completa de mesas
- [ ] Reportes de comandas por período
- [ ] Integración con impresoras de tickets
- [ ] Notificaciones push a cocina
- [ ] Gestión de turnos de trabajo
- [ ] Histórico de comandas por mesa
- [ ] Exportación de datos a Excel