# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import os
import sys
import logging
from PIL import Image, ImageTk

class SistemaComandas:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Comandas - Restaurante")
        
        # Configurar tamaño mínimo y centrar ventana
        self.root.minsize(1024, 768)
        
        # Obtener dimensiones de la pantalla
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcular tamaño de ventana (90% de la pantalla, mínimo 1024x768)
        window_width = max(1024, int(screen_width * 0.9))
        window_height = max(768, int(screen_height * 0.9))
        
        # Centrar la ventana
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg="#F8F9FA")
        
        # Configurar ícono de manera segura
        try:
            icon_path = self.get_resource_path("img", "comanda.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"No se pudo cargar el ícono: {e}")
        
        # Usuario actual
        self.usuario_actual = None
        
        # Inicializar base de datos
        self.init_database()
        
        # Comanda actual
        self.comanda_actual = []
        self.mesa_actual = None
        self.numero_comanda = None
        
        # Mostrar login
        self.mostrar_login()
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        
    def get_resource_path(self, *args):
        """Obtiene la ruta correcta para recursos tanto en desarrollo como en ejecutable"""
        try:
            # Cuando se ejecuta desde PyInstaller
            base_path = sys._MEIPASS
        except AttributeError:
            # Cuando se ejecuta desde el script normal
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        return os.path.join(base_path, *args)
    
    def get_app_directory(self):
        """Obtiene el directorio donde está ubicado el ejecutable/script"""
        try:
            # Si está compilado con pyinstaller
            if getattr(sys, 'frozen', False):
                return os.path.dirname(sys.executable)
            else:
                # Si está corriendo como script
                return os.path.dirname(os.path.abspath(__file__))
        except:
            # Fallback
            return os.path.dirname(os.path.abspath(__file__))
        
    def init_database(self):
        """Inicializa la base de datos y crea las tablas"""
        # Crear la base de datos en el directorio de la aplicación
        app_dir = self.get_app_directory()
        db_path = os.path.join(app_dir, 'comandas.db')
        
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        print(f"Base de datos ubicada en: {db_path}")
        
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                nombre_completo TEXT,
                rol TEXT NOT NULL,
                activo INTEGER DEFAULT 1,
                ultimo_acceso TEXT
            )
        ''')
        
        # Actualizar tabla usuarios si es necesaria (migración)
        try:
            # Verificar si existe la columna 'nombre_completo'
            self.cursor.execute("PRAGMA table_info(usuarios)")
            columnas = [col[1] for col in self.cursor.fetchall()]
            
            if 'nombre_completo' not in columnas:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT")
            if 'activo' not in columnas:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER DEFAULT 1")
            if 'ultimo_acceso' not in columnas:
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN ultimo_acceso TEXT")
            if 'usuario' not in columnas:
                # Si no existe 'usuario', crear la columna y copiar de 'nombre'
                self.cursor.execute("ALTER TABLE usuarios ADD COLUMN usuario TEXT")
                self.cursor.execute("UPDATE usuarios SET usuario = nombre WHERE usuario IS NULL")
            
            # Asegurar que ambas columnas tengan valores válidos
            self.cursor.execute("UPDATE usuarios SET nombre_completo = usuario WHERE nombre_completo IS NULL AND usuario IS NOT NULL")
            self.cursor.execute("UPDATE usuarios SET usuario = nombre_completo WHERE usuario IS NULL AND nombre_completo IS NOT NULL")
            
        except Exception as e:
            print(f"Error en migración de usuarios: {e}")
            pass
        
        # Tabla de productos/platos
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio REAL NOT NULL,
                categoria TEXT,
                disponible INTEGER DEFAULT 1,
                descripcion TEXT
            )
        ''')
        
        # Tabla de mesas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mesas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                capacidad INTEGER DEFAULT 4,
                estado TEXT DEFAULT 'Disponible',
                ubicacion TEXT
            )
        ''')
        
        # Actualizar tabla mesas si es necesaria (migración)
        try:
            # Verificar si existe la columna 'nombre'
            self.cursor.execute("PRAGMA table_info(mesas)")
            columnas = [col[1] for col in self.cursor.fetchall()]
            
            if 'nombre' not in columnas:
                self.cursor.execute("ALTER TABLE mesas ADD COLUMN nombre TEXT")
                # Migrar datos de 'numero' a 'nombre' si es necesario
                self.cursor.execute("UPDATE mesas SET nombre = numero WHERE nombre IS NULL")
            if 'ubicacion' not in columnas:
                self.cursor.execute("ALTER TABLE mesas ADD COLUMN ubicacion TEXT DEFAULT 'Sin ubicación'")
        except:
            pass
        
        # Tabla de comandas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comandas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_comanda TEXT NOT NULL,
                mesa_id INTEGER,
                fecha TEXT NOT NULL,
                usuario TEXT NOT NULL,
                total REAL NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                observaciones TEXT,
                FOREIGN KEY (mesa_id) REFERENCES mesas (id)
            )
        ''')
        
        # Tabla de items de comanda
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items_comanda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comanda_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                observaciones TEXT,
                FOREIGN KEY (comanda_id) REFERENCES comandas (id)
            )
        ''')
        
        # Insertar usuario admin por defecto si no existe
        self.cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
        admin_user = self.cursor.fetchone()
        
        if not admin_user:
            # No existe, crear el usuario admin
            self.cursor.execute('''
                INSERT INTO usuarios (usuario, password, nombre_completo, rol, activo) 
                VALUES ('admin', 'admin123', 'Administrador del Sistema', 'Administrador', 1)
            ''')
        else:
            # Existe, asegurar que tenga el rol correcto
            self.cursor.execute('''
                UPDATE usuarios 
                SET rol = 'Administrador', nombre_completo = 'Administrador del Sistema', activo = 1
                WHERE usuario = 'admin'
            ''')
        
        # Limpiar usuarios duplicados o con problemas (ej: 'Administrador' en lugar de 'admin')
        self.cursor.execute("DELETE FROM usuarios WHERE usuario = 'Administrador' AND usuario != 'admin'")
        
        # Insertar productos de ejemplo si no existen
        self.cursor.execute("SELECT COUNT(*) FROM productos")
        if self.cursor.fetchone()[0] == 0:
            productos_ejemplo = [
                ('Hamburguesa Clásica', 2500, 'Hamburguesas', 1, 'Carne, lechuga, tomate, cebolla'),
                ('Pizza Margarita', 3000, 'Pizzas', 1, 'Salsa de tomate, mozzarella, albahaca'),
                ('Papas Fritas', 800, 'Guarniciones', 1, 'Papas cortadas en bastones'),
                ('Coca Cola 500ml', 600, 'Bebidas', 1, 'Bebida gaseosa'),
                ('Milanesa con Puré', 2800, 'Platos Principales', 1, 'Milanesa de carne con puré de papas'),
                ('Ensalada César', 1800, 'Ensaladas', 1, 'Lechuga, pollo, crutones, aderezo césar'),
                ('Café Expreso', 400, 'Cafetería', 1, 'Café expreso tradicional'),
                ('Agua Mineral', 300, 'Bebidas', 1, 'Agua sin gas 500ml')
            ]
            self.cursor.executemany('''
                INSERT INTO productos (nombre, precio, categoria, disponible, descripcion)
                VALUES (?, ?, ?, ?, ?)
            ''', productos_ejemplo)
        
        # Insertar mesas de ejemplo si no existen
        self.cursor.execute("SELECT COUNT(*) FROM mesas")
        if self.cursor.fetchone()[0] == 0:
            mesas_ejemplo = [
                ('Mesa 1', 4, 'Disponible', 'Zona Principal'),
                ('Mesa 2', 4, 'Disponible', 'Zona Principal'),
                ('Mesa 3', 6, 'Disponible', 'Zona Principal'),
                ('Mesa 4', 2, 'Disponible', 'Zona Ventana'),
                ('Mesa 5', 8, 'Disponible', 'Zona VIP'),
                ('Barra 1', 1, 'Disponible', 'Barra'),
                ('Barra 2', 1, 'Disponible', 'Barra'),
                ('Terraza 1', 4, 'Disponible', 'Terraza'),
                ('Terraza 2', 6, 'Disponible', 'Terraza'),
                ('Privado 1', 10, 'Disponible', 'Salón Privado')
            ]
            self.cursor.executemany('''
                INSERT INTO mesas (nombre, capacidad, estado, ubicacion)
                VALUES (?, ?, ?, ?)
            ''', mesas_ejemplo)
        
        self.conn.commit()
    
    def mostrar_login(self):
        """Muestra la ventana de login"""
        self.login_frame = tk.Frame(self.root, bg='#F8F9FA')
        self.login_frame.place(relx=0.5, rely=0.5, anchor='center')

        # Logo/Título
        tk.Label(
            self.login_frame, 
            text="🍽️ Sistema de Comandas", 
            font=('Arial', 28, 'bold'),
            bg='#F8F9FA',
            fg='#DC3545'
        ).pack(pady=30)
        
        # Usuario
        tk.Label(
            self.login_frame, 
            text="Usuario:", 
            font=('Arial', 14),
            bg='#F8F9FA'
        ).pack(pady=8)
        
        self.entry_usuario = tk.Entry(self.login_frame, font=('Arial', 14), width=25)
        self.entry_usuario.pack(pady=8)
        
        # Contraseña
        tk.Label(
            self.login_frame, 
            text="Contraseña:", 
            font=('Arial', 14),
            bg='#F8F9FA'
        ).pack(pady=8)
        
        self.entry_password = tk.Entry(self.login_frame, font=('Arial', 14), width=25, show='*')
        self.entry_password.pack(pady=8)
        self.entry_password.bind('<Return>', lambda e: self.login())
        
        # Botón login
        tk.Button(
            self.login_frame,
            text="Iniciar Sesión",
            font=('Arial', 14, 'bold'),
            bg='#DC3545',
            fg='white',
            command=self.login,
            width=20,
            height=2,
            cursor='hand2'
        ).pack(pady=20)
    
    def login(self):
        """Procesa el login del usuario"""
        usuario = self.entry_usuario.get()
        password = self.entry_password.get()
        
        # Intentar login con nueva estructura
        self.cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND password = ? AND activo = 1",
            (usuario, password)
        )
        user = self.cursor.fetchone()
        
        # Si no encuentra, intentar con estructura antigua
        if not user:
            self.cursor.execute(
                "SELECT * FROM usuarios WHERE nombre_completo = ? AND password = ?",
                (usuario, password)
            )
            user = self.cursor.fetchone()
        
        if user:
            # Actualizar último acceso
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute(
                "UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?",
                (fecha_actual, user[0])
            )
            self.conn.commit()
            
            # Mapear correctamente los datos del usuario
            # Estructura: (id, usuario, password, nombre_completo, rol, activo, ultimo_acceso)
            usuario_nombre = user[1] if len(user) > 1 and user[1] else usuario
            nombre_completo = user[3] if len(user) > 3 and user[3] else usuario_nombre  # nombre_completo está en índice 3
            rol = user[4] if len(user) > 4 and user[4] else 'Mesero'  # rol está en índice 4
            
            self.usuario_actual = {
                'id': user[0],
                'usuario': usuario_nombre,
                'nombre': nombre_completo,
                'rol': rol
            }
            
            self.usuario_actual_completo = self.usuario_actual  # Para compatibilidad
            self.login_frame.destroy()
            self.mostrar_interfaz_principal()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    def mostrar_interfaz_principal(self):
        """Muestra la interfaz principal del sistema"""
        # Header más compacto
        header = tk.Frame(self.root, bg='#DC3545', height=50)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="🍽️ Sistema de Comandas",
            font=('Arial', 14, 'bold'),
            bg='#DC3545',
            fg='white'
        ).pack(side='left', padx=15, pady=10)
        
        tk.Label(
            header,
            text=f"👤 {self.usuario_actual['nombre']}",
            font=('Arial', 10),
            bg='#DC3545',
            fg='white'
        ).pack(side='right', padx=8)
        
        tk.Button(
            header,
            text="Cerrar Sesión",
            font=('Arial', 9),
            bg="#B02A37",
            fg='white',
            command=self.logout,
            cursor='hand2'
        ).pack(side='right', padx=8, pady=8)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Crear pestañas según el rol
        self.crear_pestaña_comandas()
        self.crear_pestaña_estado_comandas()  # Nueva pestaña para todos los usuarios
        
        # Verificar rol de manera segura
        rol_usuario = self.usuario_actual.get('rol', '').lower() if self.usuario_actual and self.usuario_actual.get('rol') else ''
        if rol_usuario in ['admin', 'administrador']:
            self.crear_pestaña_productos()
            self.crear_pestaña_mesas()
            self.crear_pestaña_reportes()
            self.crear_pestaña_usuarios()
        
        # Inicializar actualización automática de mesas
        self.root.after(30000, self.actualizar_mesas_automatico)
    
    def crear_pestaña_comandas(self):
        """Crea la pestaña principal de comandas (diseño táctil)"""
        frame_comandas = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_comandas, text='📝 Nueva Comanda')

        # Frame superior - Selección de mesa (altura fija más pequeña)
        frame_mesa = tk.Frame(frame_comandas, bg='#E9ECEF', relief='raised', bd=2, height=80)
        frame_mesa.pack(fill='x', padx=5, pady=3)
        frame_mesa.pack_propagate(False)
        
        tk.Label(
            frame_mesa,
            text="🪑 Mesa:",
            font=('Arial', 12, 'bold'),
            bg='#E9ECEF'
        ).pack(side='left', padx=10, pady=5)
        
        # Botones de mesas (más compactos)
        self.frame_mesas = tk.Frame(frame_mesa, bg='#E9ECEF')
        self.frame_mesas.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        
        self.label_mesa_actual = tk.Label(
            frame_mesa,
            text="No seleccionada",
            font=('Arial', 11, 'bold'),
            bg='#E9ECEF',
            fg='#DC3545'
        )
        self.label_mesa_actual.pack(side='right', padx=10, pady=5)
        
        # Contenedor principal con scroll si es necesario
        contenedor_principal = tk.Frame(frame_comandas, bg='#F8F9FA')
        contenedor_principal.pack(fill='both', expand=True, padx=5, pady=3)
        
        # Frame izquierdo - Categorías y productos (70% del ancho)
        frame_izq = tk.Frame(contenedor_principal, bg='#F8F9FA')
        frame_izq.pack(side='left', fill='both', expand=True, padx=3)
        
        # Categorías (botones más pequeños y en una sola fila)
        tk.Label(
            frame_izq,
            text="📂 Categorías",
            font=('Arial', 12, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=5)
        
        # Frame con scroll horizontal para categorías
        canvas_categorias = tk.Canvas(frame_izq, bg='#F8F9FA', height=60)
        scrollbar_cat_h = ttk.Scrollbar(frame_izq, orient="horizontal", command=canvas_categorias.xview)
        self.frame_categorias = tk.Frame(canvas_categorias, bg='#F8F9FA')
        
        self.frame_categorias.bind(
            "<Configure>",
            lambda e: canvas_categorias.configure(scrollregion=canvas_categorias.bbox("all"))
        )
        
        canvas_categorias.create_window((0, 0), window=self.frame_categorias, anchor="nw")
        canvas_categorias.configure(xscrollcommand=scrollbar_cat_h.set)
        
        canvas_categorias.pack(side="top", fill="x")
        scrollbar_cat_h.pack(side="top", fill="x")
        
        # Productos (grid más compacto)
        tk.Label(
            frame_izq,
            text="🍽️ Productos",
            font=('Arial', 12, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=(10, 5))
        
        # Frame con scroll para productos (altura fija)
        canvas_productos = tk.Canvas(frame_izq, bg='#F8F9FA', height=450)
        scrollbar_productos = ttk.Scrollbar(frame_izq, orient="vertical", command=canvas_productos.yview)
        self.frame_productos_scroll = tk.Frame(canvas_productos, bg='#F8F9FA')
        
        self.frame_productos_scroll.bind(
            "<Configure>",
            lambda e: canvas_productos.configure(scrollregion=canvas_productos.bbox("all"))
        )
        
        canvas_productos.create_window((0, 0), window=self.frame_productos_scroll, anchor="nw")
        canvas_productos.configure(yscrollcommand=scrollbar_productos.set)
        
        canvas_productos.pack(side="left", fill="both", expand=True)
        scrollbar_productos.pack(side="right", fill="y")
        
        # Frame derecho - Comanda actual (30% del ancho, ancho fijo)
        frame_der = tk.Frame(contenedor_principal, bg='#F8F9FA', width=320)
        frame_der.pack(side='right', fill='y', padx=3)
        frame_der.pack_propagate(False)
        
        tk.Label(
            frame_der,
            text="📋 Comanda",
            font=('Arial', 12, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=5)
        
        # Lista de la comanda (altura fija)
        frame_comanda = tk.Frame(frame_der, bg='#F8F9FA', height=200)
        frame_comanda.pack(fill='x', pady=5)
        frame_comanda.pack_propagate(False)
        
        scrollbar_comanda = tk.Scrollbar(frame_comanda)
        scrollbar_comanda.pack(side='right', fill='y')
        
        self.lista_comanda = tk.Listbox(
            frame_comanda,
            font=('Arial', 9),
            yscrollcommand=scrollbar_comanda.set
        )
        self.lista_comanda.pack(side='left', fill='both', expand=True)
        scrollbar_comanda.config(command=self.lista_comanda.yview)
        
        # Botones de comanda (más compactos)
        frame_botones_comanda = tk.Frame(frame_der, bg='#F8F9FA')
        frame_botones_comanda.pack(fill='x', pady=5)
        
        tk.Button(
            frame_botones_comanda,
            text="➖ Quitar",
            font=('Arial', 10, 'bold'),
            bg='#FFC107',
            fg='black',
            command=self.quitar_de_comanda,
            height=1,
            cursor='hand2'
        ).pack(fill='x', pady=1)
        
        tk.Button(
            frame_botones_comanda,
            text="🗑️ Limpiar",
            font=('Arial', 10, 'bold'),
            bg='#DC3545',
            fg='white',
            command=self.limpiar_comanda,
            height=1,
            cursor='hand2'
        ).pack(fill='x', pady=1)
        
        # Observaciones (más compacto)
        tk.Label(
            frame_der,
            text="📝 Observaciones:",
            font=('Arial', 10, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=(5, 2))
        
        self.text_observaciones = tk.Text(
            frame_der,
            height=3,
            font=('Arial', 9),
            wrap=tk.WORD
        )
        self.text_observaciones.pack(fill='x', pady=2)
        
        # Total
        self.label_total = tk.Label(
            frame_der,
            text="TOTAL: $0",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA',
            fg='#DC3545'
        )
        self.label_total.pack(pady=10)
        
        # Botón finalizar comanda
        tk.Button(
            frame_der,
            text="✅ ENVIAR COMANDA",
            font=('Arial', 12, 'bold'),
            bg='#28A745',
            fg='white',
            command=self.finalizar_comanda,
            height=2,
            cursor='hand2'
        ).pack(fill='x', pady=5)
        
        # Inicializar
        self.cargar_mesas()
        self.cargar_categorias()
        self.cargar_productos()
    
    def cargar_mesas(self):
        """Carga los botones de mesas"""
        # Limpiar frame
        for widget in self.frame_mesas.winfo_children():
            widget.destroy()
        
        # Intentar con nueva estructura primero
        try:
            self.cursor.execute('SELECT * FROM mesas ORDER BY nombre')
            mesas = self.cursor.fetchall()
            columna_nombre = 1  # columna 'nombre'
            columna_estado = 3  # columna 'estado'
        except:
            # Fallback a estructura antigua
            self.cursor.execute('SELECT * FROM mesas ORDER BY numero')
            mesas = self.cursor.fetchall()
            columna_nombre = 1  # columna 'numero'
            columna_estado = 3  # columna 'estado'
        
        for i, mesa in enumerate(mesas):
            estado = mesa[columna_estado].lower()
            mesa_id = mesa[0]
            
            # Verificar si hay comandas pendientes o en preparación para esta mesa
            self.cursor.execute("""
                SELECT COUNT(*) FROM comandas 
                WHERE mesa_id = ? AND estado IN ('Pendiente', 'En preparación')
            """, (mesa_id,))
            comandas_activas = self.cursor.fetchone()[0]
            
            # Determinar color según estado de mesa y comandas
            if estado in ['libre', 'disponible']:
                if comandas_activas > 0:
                    color_bg = '#FFC107'  # Amarillo: mesa libre pero con comandas pendientes
                    tooltip = f"Mesa disponible\nComandas pendientes: {comandas_activas}"
                else:
                    color_bg = '#28A745'  # Verde: mesa totalmente libre
                    tooltip = "Mesa disponible"
            elif estado.lower() == 'ocupada':
                # Verificar si hay comandas completadas
                self.cursor.execute("""
                    SELECT COUNT(*) FROM comandas 
                    WHERE mesa_id = ? AND estado = 'Completada'
                """, (mesa_id,))
                comandas_completadas = self.cursor.fetchone()[0]
                
                if comandas_completadas > 0 and comandas_activas == 0:
                    color_bg = '#17A2B8'  # Azul: mesa ocupada pero sin comandas activas (lista para liberar)
                    tooltip = f"Mesa ocupada\nComandas completadas: {comandas_completadas}\n¡Lista para liberar!"
                else:
                    color_bg = '#DC3545'  # Rojo: mesa ocupada con comandas activas
                    tooltip = f"Mesa ocupada\nComandas activas: {comandas_activas}"
            else:
                color_bg = '#6C757D'  # Gris: otros estados
                tooltip = f"Estado: {estado}"
            
            color_text = 'white'
            
            btn = tk.Button(
                self.frame_mesas,
                text=f"{mesa[columna_nombre]}",
                font=('Arial', 9, 'bold'),
                bg=color_bg,
                fg=color_text,
                command=lambda m=mesa: self.seleccionar_mesa(m),
                width=8,
                height=1,
                cursor='hand2'
            )
            btn.grid(row=i//8, column=i%8, padx=1, pady=1)
            
            # Agregar tooltip (simulado con bind de eventos)
            def create_tooltip(widget, text):
                def on_enter(event):
                    widget.config(relief='raised')
                def on_leave(event):
                    widget.config(relief='flat')
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            
            create_tooltip(btn, tooltip)
    
    def seleccionar_mesa(self, mesa):
        """Selecciona una mesa para la comanda"""
        # Determinar qué columna usar según la estructura
        try:
            nombre_mesa = mesa[1]  # nombre o numero
            estado_mesa = mesa[3].lower()  # estado
        except:
            nombre_mesa = mesa[1]
            estado_mesa = 'libre'
        
        if estado_mesa in ['ocupada']:
            if not messagebox.askyesno("Mesa Ocupada", f"La {nombre_mesa} está ocupada. ¿Desea continuar?"):
                return
        
        self.mesa_actual = mesa
        self.label_mesa_actual.config(text=f"{mesa[1]}")
        # Mensaje de confirmación más discreto - sin ventana emergente
        print(f"Mesa seleccionada: {mesa[1]}")
    
    def cargar_categorias(self):
        """Carga los botones de categorías"""
        # Limpiar frame
        for widget in self.frame_categorias.winfo_children():
            widget.destroy()
        
        # Botón "Todas"
        tk.Button(
            self.frame_categorias,
            text="🍽️ Todas",
            font=('Arial', 10, 'bold'),
            bg='#6C757D',
            fg='white',
            command=lambda: self.filtrar_productos(None),
            width=10,
            height=1,
            cursor='hand2'
        ).pack(side='left', padx=1)
        
        # Obtener categorías únicas
        self.cursor.execute('SELECT DISTINCT categoria FROM productos WHERE disponible = 1 ORDER BY categoria')
        categorias = self.cursor.fetchall()
        
        colores_categoria = {
            'Hamburguesas': '#FF6B6B',
            'Pizzas': '#4ECDC4',
            'Platos Principales': '#45B7D1',
            'Ensaladas': '#96CEB4',
            'Guarniciones': '#FECA57',
            'Bebidas': '#74B9FF',
            'Cafetería': '#A29BFE',
            'Otros': '#FD79A8'
        }
        
        for categoria in categorias:
            cat_nombre = categoria[0]
            color = colores_categoria.get(cat_nombre, '#6C757D')
            
            # Nombre más corto para categorías
            nombre_corto = cat_nombre.replace('Platos Principales', 'Platos').replace('Hamburguesas', 'Hambur.')
            
            tk.Button(
                self.frame_categorias,
                text=f"📂 {nombre_corto}",
                font=('Arial', 10, 'bold'),
                bg=color,
                fg='white',
                command=lambda c=cat_nombre: self.filtrar_productos(c),
                width=12,
                height=1,
                cursor='hand2'
            ).pack(side='left', padx=1)
    
    def filtrar_productos(self, categoria):
        """Filtra productos por categoría"""
        self.categoria_actual = categoria
        self.cargar_productos()
    
    def cargar_productos(self):
        """Carga los productos como botones grandes (diseño táctil)"""
        # Limpiar frame
        for widget in self.frame_productos_scroll.winfo_children():
            widget.destroy()
        
        # Consulta según filtro
        if hasattr(self, 'categoria_actual') and self.categoria_actual:
            self.cursor.execute('''
                SELECT * FROM productos 
                WHERE disponible = 1 AND categoria = ?
                ORDER BY nombre
            ''', (self.categoria_actual,))
        else:
            self.cursor.execute('''
                SELECT * FROM productos 
                WHERE disponible = 1
                ORDER BY categoria, nombre
            ''')
        
        productos = self.cursor.fetchall()
        
        # Crear grid de productos (4 columnas para 1024px)
        columnas = 4
        for i, producto in enumerate(productos):
            fila = i // columnas
            columna = i % columnas
            
            # Frame para cada producto
            frame_producto = tk.Frame(
                self.frame_productos_scroll,
                bg='white',
                relief='raised',
                bd=1,
                width=180,
                height=120
            )
            frame_producto.grid(row=fila, column=columna, padx=2, pady=2, sticky='ew')
            frame_producto.pack_propagate(False)
            
            # Configurar peso de columnas
            self.frame_productos_scroll.columnconfigure(columna, weight=1)
            
            # Nombre del producto (más corto)
            nombre_corto = producto[1][:25] + "..." if len(producto[1]) > 25 else producto[1]
            tk.Label(
                frame_producto,
                text=nombre_corto,
                font=('Arial', 10, 'bold'),
                bg='white',
                wraplength=170
            ).pack(pady=2)
            
            # Precio
            tk.Label(
                frame_producto,
                text=f"${producto[2]}",
                font=('Arial', 14, 'bold'),
                bg='white',
                fg='#DC3545'
            ).pack()
            
            # Descripción (más corta)
            if producto[5]:  # descripcion
                desc_corta = producto[5][:40] + "..." if len(producto[5]) > 40 else producto[5]
                tk.Label(
                    frame_producto,
                    text=desc_corta,
                    font=('Arial', 8),
                    bg='white',
                    fg='gray',
                    wraplength=160
                ).pack(pady=1)
            
            # Botón agregar (más compacto)
            tk.Button(
                frame_producto,
                text="➕ Agregar",
                font=('Arial', 10, 'bold'),
                bg='#28A745',
                fg='white',
                command=lambda p=producto: self.agregar_a_comanda(p),
                width=12,
                height=1,
                cursor='hand2'
            ).pack(pady=2, padx=2, side='bottom')
    
    def agregar_a_comanda(self, producto):
        """Agrega un producto a la comanda actual"""
        if not self.mesa_actual:
            messagebox.showwarning("Mesa", "Primero selecciona una mesa")
            return
        
        # Verificar si ya está en la comanda
        for item in self.comanda_actual:
            if item['id'] == producto[0]:
                item['cantidad'] += 1
                self.actualizar_comanda_display()
                return
        
        # Agregar nuevo item
        self.comanda_actual.append({
            'id': producto[0],
            'nombre': producto[1],
            'precio': producto[2],
            'cantidad': 1,
            'categoria': producto[3]
        })
        self.actualizar_comanda_display()
    
    def actualizar_comanda_display(self):
        """Actualiza la visualización de la comanda"""
        self.lista_comanda.delete(0, tk.END)
        total = 0
        
        for item in self.comanda_actual:
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            texto = f"{item['nombre']} x{item['cantidad']} - ${subtotal}"
            self.lista_comanda.insert(tk.END, texto)
        
        self.label_total.config(text=f"TOTAL: ${total}")
    
    def quitar_de_comanda(self):
        """Quita el item seleccionado de la comanda"""
        seleccion = self.lista_comanda.curselection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona un item para quitar")
            return
        
        index = seleccion[0]
        item = self.comanda_actual[index]
        
        if item['cantidad'] > 1:
            item['cantidad'] -= 1
        else:
            del self.comanda_actual[index]
        
        self.actualizar_comanda_display()
    
    def limpiar_comanda(self):
        """Limpia toda la comanda"""
        if self.comanda_actual and messagebox.askyesno("Confirmar", "¿Limpiar toda la comanda?"):
            self.comanda_actual = []
            self.actualizar_comanda_display()
    
    def finalizar_comanda(self):
        """Finaliza y guarda la comanda"""
        if not self.comanda_actual:
            messagebox.showwarning("Comanda Vacía", "La comanda está vacía")
            return
        
        if not self.mesa_actual:
            messagebox.showwarning("Mesa", "Selecciona una mesa")
            return
        
        # Calcular total
        total = sum(item['precio'] * item['cantidad'] for item in self.comanda_actual)
        
        # Generar número de comanda
        fecha_actual = datetime.now()
        numero_comanda = f"CMD-{fecha_actual.strftime('%Y%m%d-%H%M%S')}"
        
        # Obtener observaciones
        observaciones = self.text_observaciones.get("1.0", tk.END).strip()
        
        # Guardar comanda
        self.cursor.execute('''
            INSERT INTO comandas (numero_comanda, mesa_id, fecha, usuario, total, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (numero_comanda, self.mesa_actual[0], fecha_actual.strftime('%Y-%m-%d %H:%M:%S'), 
              self.usuario_actual['nombre'], total, observaciones))
        
        comanda_id = self.cursor.lastrowid
        
        # Guardar items de la comanda
        for item in self.comanda_actual:
            self.cursor.execute('''
                INSERT INTO items_comanda (comanda_id, producto_nombre, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            ''', (comanda_id, item['nombre'], item['cantidad'], item['precio']))
        
        # Marcar mesa como ocupada
        self.cursor.execute('''
            UPDATE mesas SET estado = 'ocupada' WHERE id = ?
        ''', (self.mesa_actual[0],))
        
        self.conn.commit()
        
        # Generar ticket
        if messagebox.askyesno("Ticket", "¿Deseas generar el ticket de comanda?"):
            self.generar_ticket_comanda(comanda_id, numero_comanda, total, observaciones)
        
        # Limpiar comanda
        self.comanda_actual = []
        self.actualizar_comanda_display()
        self.text_observaciones.delete("1.0", tk.END)
        
        # Actualizar mesas
        mesa_nombre = self.mesa_actual[1] if self.mesa_actual else 'N/A'
        self.cargar_mesas()
        
        # Limpiar selección de mesa
        self.mesa_actual = None
        self.label_mesa_actual.config(text="No seleccionada")
        
        messagebox.showinfo("Éxito", 
            f"✅ Comanda {numero_comanda} enviada exitosamente!\n\n"
            f"💰 Total: ${total}\n"
            f"🪑 Mesa: {mesa_nombre}\n\n"
            f"📄 Los tickets se guardan en la carpeta 'tickets'")
    
    def crear_pestaña_estado_comandas(self):
        """Crea la pestaña para gestionar el estado de comandas y mesas"""
        frame_estado = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_estado, text='📋 Estado Comandas')
        
        # Marco principal
        main_frame = tk.Frame(frame_estado, bg='#F8F9FA')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="📋 Estado de Comandas y Mesas",
            font=('Arial', 18, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        )
        title_label.pack(pady=(0, 10))
        
        # Frame de resumen estadístico
        self.frame_resumen = tk.Frame(main_frame, bg='#E9ECEF', relief='raised', bd=2)
        self.frame_resumen.pack(fill='x', pady=(0, 20))
        
        # Labels para estadísticas
        stats_frame = tk.Frame(self.frame_resumen, bg='#E9ECEF')
        stats_frame.pack(fill='x', padx=20, pady=15)
        
        self.label_stats = tk.Label(
            stats_frame,
            text="Cargando estadísticas...",
            font=('Arial', 12),
            bg='#E9ECEF',
            fg='#495057'
        )
        self.label_stats.pack()
        
        # Frame superior con botones de acción
        action_frame = tk.Frame(main_frame, bg='#F8F9FA')
        action_frame.pack(fill='x', pady=(0, 20))
        
        # Botón Actualizar
        btn_actualizar = tk.Button(
            action_frame,
            text="🔄 Actualizar",
            font=('Arial', 12, 'bold'),
            bg='#17A2B8',
            fg='white',
            command=self.actualizar_estado_comandas,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_actualizar.pack(side='left', padx=(0, 10))
        
        # Botón Completar Comanda
        btn_completar = tk.Button(
            action_frame,
            text="✅ Completar Comanda",
            font=('Arial', 12, 'bold'),
            bg='#28A745',
            fg='white',
            command=self.completar_comanda_seleccionada,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_completar.pack(side='left', padx=(0, 10))
        
        # Botón Liberar Mesa
        btn_liberar = tk.Button(
            action_frame,
            text="🔓 Liberar Mesa",
            font=('Arial', 12, 'bold'),
            bg='#FD7E14',
            fg='white',
            command=self.liberar_mesa_seleccionada,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_liberar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar Comanda
        btn_cancelar = tk.Button(
            action_frame,
            text="❌ Cancelar Comanda",
            font=('Arial', 12, 'bold'),
            bg='#DC3545',
            fg='white',
            command=self.cancelar_comanda_seleccionada,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Frame para la lista de comandas
        lista_frame = tk.Frame(main_frame, bg='#F8F9FA')
        lista_frame.pack(fill='both', expand=True)
        
        # Crear Treeview para mostrar las comandas
        self.tree_comandas = ttk.Treeview(
            lista_frame,
            columns=('Comanda', 'Mesa', 'Estado Mesa', 'Estado Comanda', 'Fecha', 'Mesero', 'Total', 'Items'),
            show='headings',
            height=15
        )
        
        # Configurar columnas
        self.tree_comandas.heading('Comanda', text='N° Comanda')
        self.tree_comandas.heading('Mesa', text='Mesa')
        self.tree_comandas.heading('Estado Mesa', text='Estado Mesa')
        self.tree_comandas.heading('Estado Comanda', text='Estado Comanda')
        self.tree_comandas.heading('Fecha', text='Fecha/Hora')
        self.tree_comandas.heading('Mesero', text='Mesero')
        self.tree_comandas.heading('Total', text='Total')
        self.tree_comandas.heading('Items', text='Items')
        
        # Configurar ancho de columnas
        self.tree_comandas.column('Comanda', width=80, anchor='center')
        self.tree_comandas.column('Mesa', width=100, anchor='center')
        self.tree_comandas.column('Estado Mesa', width=100, anchor='center')
        self.tree_comandas.column('Estado Comanda', width=120, anchor='center')
        self.tree_comandas.column('Fecha', width=140, anchor='center')
        self.tree_comandas.column('Mesero', width=100, anchor='center')
        self.tree_comandas.column('Total', width=80, anchor='center')
        self.tree_comandas.column('Items', width=50, anchor='center')
        
        # Scrollbar para el Treeview
        scrollbar_comandas = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_comandas.yview)
        self.tree_comandas.configure(yscrollcommand=scrollbar_comandas.set)
        
        # Empaquetar Treeview y scrollbar
        self.tree_comandas.pack(side='left', fill='both', expand=True)
        scrollbar_comandas.pack(side='right', fill='y')
        
        # Cargar las comandas existentes
        self.actualizar_estado_comandas()
        self.actualizar_estadisticas_resumen()
    
    def actualizar_estadisticas_resumen(self):
        """Actualiza las estadísticas mostradas en el resumen"""
        try:
            cursor = self.conn.cursor()
            
            # Estadísticas de mesas
            cursor.execute("SELECT estado, COUNT(*) FROM mesas GROUP BY estado")
            stats_mesas = dict(cursor.fetchall())
            
            # Estadísticas de comandas hoy
            cursor.execute("""
                SELECT estado, COUNT(*) 
                FROM comandas 
                WHERE DATE(fecha_creacion) = DATE('now') 
                GROUP BY estado
            """)
            stats_comandas_hoy = dict(cursor.fetchall())
            
            # Comandas pendientes total
            cursor.execute("""
                SELECT COUNT(*) FROM comandas 
                WHERE estado IN ('Pendiente', 'En preparación')
            """)
            comandas_pendientes = cursor.fetchone()[0]
            
            # Crear texto del resumen
            mesas_libres = stats_mesas.get('Disponible', 0) + stats_mesas.get('Libre', 0)
            mesas_ocupadas = stats_mesas.get('Ocupada', 0)
            total_mesas = sum(stats_mesas.values())
            
            comandas_pendientes_hoy = stats_comandas_hoy.get('Pendiente', 0)
            comandas_preparacion = stats_comandas_hoy.get('En preparación', 0)
            comandas_completadas_hoy = stats_comandas_hoy.get('Completada', 0)
            
            resumen_texto = (
                f"🪑 Mesas: {mesas_libres} libres, {mesas_ocupadas} ocupadas ({total_mesas} total) | "
                f"📝 Comandas hoy: {comandas_pendientes_hoy} pendientes, {comandas_preparacion} en prep., {comandas_completadas_hoy} completadas | "
                f"⚠️ Total pendientes: {comandas_pendientes}"
            )
            
            self.label_stats.config(text=resumen_texto)
            
        except Exception as e:
            self.label_stats.config(text=f"Error al cargar estadísticas: {str(e)}")

    def actualizar_estado_comandas(self):
        """Actualiza la lista de comandas en el Treeview"""
        # Limpiar lista actual
        for item in self.tree_comandas.get_children():
            self.tree_comandas.delete(item)
        
        # Cargar comandas desde la base de datos con información de las mesas
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                c.numero_comanda,
                m.nombre as mesa_nombre,
                m.estado as mesa_estado,
                c.estado as comanda_estado,
                c.fecha,
                c.usuario,
                c.total,
                COUNT(ic.id) as total_items,
                c.id as comanda_id,
                m.id as mesa_id
            FROM comandas c
            LEFT JOIN mesas m ON c.mesa_id = m.id
            LEFT JOIN items_comanda ic ON c.id = ic.comanda_id
            WHERE c.estado IN ('Pendiente', 'En preparación', 'Completada')
            GROUP BY c.id
            ORDER BY c.fecha DESC
        """)
        comandas = cursor.fetchall()
        
        # Agregar comandas al Treeview
        for comanda in comandas:
            numero, mesa, estado_mesa, estado_comanda, fecha, mesero, total, items, comanda_id, mesa_id = comanda
            
            # Formatear la fecha para mostrar solo fecha y hora
            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                fecha_formateada = fecha_obj.strftime("%d/%m %H:%M")
            except:
                fecha_formateada = fecha
            
            # Insertar en el tree
            item_id = self.tree_comandas.insert('', 'end', values=(
                numero, mesa or 'Sin mesa', estado_mesa or 'N/A', estado_comanda, 
                fecha_formateada, mesero, f'${total}', items
            ))
        
        # Actualizar estadísticas si existe el widget
        if hasattr(self, 'label_stats'):
            self.actualizar_estadisticas_resumen()
    
    def completar_comanda_seleccionada(self):
        """Marca la comanda seleccionada como completada"""
        seleccion = self.tree_comandas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una comanda para completar")
            return
        
        # Obtener datos de la comanda seleccionada
        item = self.tree_comandas.item(seleccion[0])
        valores = item['values']
        numero_comanda = valores[0]
        mesa_nombre = valores[1]
        estado_actual = valores[3]
        
        if estado_actual == 'Completada':
            messagebox.showinfo("Información", "Esta comanda ya está completada")
            return
        
        if messagebox.askyesno("Completar Comanda", 
                              f"¿Estás seguro de que deseas marcar la comanda {numero_comanda} como completada?"):
            try:
                # Buscar el ID real de la comanda y mesa
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT c.id, c.mesa_id 
                    FROM comandas c 
                    WHERE c.numero_comanda = ?
                """, (numero_comanda,))
                resultado = cursor.fetchone()
                
                if resultado:
                    comanda_id, mesa_id = resultado
                    # Actualizar estado de la comanda
                    cursor.execute("UPDATE comandas SET estado = 'Completada' WHERE id = ?", (comanda_id,))
                    self.conn.commit()
                    
                    # Verificar si se puede liberar automáticamente la mesa
                    mesa_liberada = self.liberar_mesa_si_completada(mesa_id) if mesa_id else False
                    
                    mensaje = f"Comanda {numero_comanda} marcada como completada"
                    if mesa_liberada:
                        mensaje += f"\n¡Mesa {mesa_nombre} liberada automáticamente!"
                    elif mesa_id:
                        mensaje += f"\nMesa {mesa_nombre} aún tiene comandas pendientes"
                    
                    messagebox.showinfo("Éxito", mensaje)
                    self.actualizar_estado_comandas()
                    self.cargar_mesas()  # Actualizar colores de mesas
                else:
                    messagebox.showerror("Error", "No se pudo encontrar la comanda")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al completar comanda: {str(e)}")
    
    def liberar_mesa_seleccionada(self):
        """Libera la mesa seleccionada (la marca como disponible)"""
        seleccion = self.tree_comandas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una comanda para liberar su mesa")
            return
        
        # Obtener datos de la mesa
        item = self.tree_comandas.item(seleccion[0])
        valores = item['values']
        numero_comanda = valores[0]
        mesa_nombre = valores[1]
        estado_mesa = valores[2]
        estado_comanda = valores[3]
        
        if estado_mesa == 'Disponible':
            messagebox.showinfo("Información", f"La mesa {mesa_nombre} ya está disponible")
            return
            
        if estado_comanda not in ['Completada']:
            if not messagebox.askyesno("Confirmar", 
                                      f"La comanda {numero_comanda} aún no está completada.\n"
                                      f"¿Estás seguro de que deseas liberar la mesa {mesa_nombre}?"):
                return
        
        if messagebox.askyesno("Liberar Mesa", 
                              f"¿Estás seguro de que deseas liberar la mesa {mesa_nombre}?"):
            try:
                # Buscar el ID de la mesa
                cursor = self.conn.cursor()
                cursor.execute("SELECT mesa_id FROM comandas WHERE numero_comanda = ?", (numero_comanda,))
                resultado = cursor.fetchone()
                
                if resultado and resultado[0]:
                    mesa_id = resultado[0]
                    # Actualizar estado de la mesa
                    cursor.execute("UPDATE mesas SET estado = 'Disponible' WHERE id = ?", (mesa_id,))
                    self.conn.commit()
                    
                    messagebox.showinfo("Éxito", f"Mesa {mesa_nombre} liberada correctamente")
                    self.actualizar_estado_comandas()
                    self.cargar_mesas()  # Actualizar colores de mesas
                else:
                    messagebox.showerror("Error", "No se pudo encontrar la mesa asociada")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al liberar mesa: {str(e)}")
    
    def cancelar_comanda_seleccionada(self):
        """Cancela la comanda seleccionada"""
        seleccion = self.tree_comandas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una comanda para cancelar")
            return
        
        # Obtener datos de la comanda seleccionada
        item = self.tree_comandas.item(seleccion[0])
        valores = item['values']
        numero_comanda = valores[0]
        mesa_nombre = valores[1]
        estado_actual = valores[3]
        
        if estado_actual == 'Cancelada':
            messagebox.showinfo("Información", "Esta comanda ya está cancelada")
            return
            
        if estado_actual == 'Completada':
            messagebox.showwarning("Advertencia", "No se puede cancelar una comanda completada")
            return
        
        if messagebox.askyesno("Cancelar Comanda", 
                              f"¿Estás seguro de que deseas cancelar la comanda {numero_comanda}?\n"
                              f"Esta acción también liberará la mesa {mesa_nombre}."):
            try:
                # Buscar los IDs de la comanda y mesa
                cursor = self.conn.cursor()
                cursor.execute("SELECT id, mesa_id FROM comandas WHERE numero_comanda = ?", (numero_comanda,))
                resultado = cursor.fetchone()
                
                if resultado:
                    comanda_id, mesa_id = resultado
                    
                    # Actualizar estado de la comanda
                    cursor.execute("UPDATE comandas SET estado = 'Cancelada' WHERE id = ?", (comanda_id,))
                    
                    # Liberar la mesa si tiene una asignada
                    if mesa_id:
                        cursor.execute("UPDATE mesas SET estado = 'Disponible' WHERE id = ?", (mesa_id,))
                    
                    self.conn.commit()
                    
                    messagebox.showinfo("Éxito", f"Comanda {numero_comanda} cancelada y mesa {mesa_nombre} liberada")
                    self.actualizar_estado_comandas()
                    self.cargar_mesas()  # Actualizar colores de mesas
                else:
                    messagebox.showerror("Error", "No se pudo encontrar la comanda")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Error al cancelar comanda: {str(e)}")
    
    def liberar_mesa_si_completada(self, mesa_id):
        """Liberar mesa automáticamente si todas las comandas están completadas"""
        try:
            self.cursor.execute("""
                SELECT COUNT(*) FROM comandas 
                WHERE mesa_id = ? AND estado IN ('Pendiente', 'En preparación')
            """, (mesa_id,))
            comandas_activas = self.cursor.fetchone()[0]
            
            if comandas_activas == 0:
                # No hay comandas activas, podemos liberar la mesa
                self.cursor.execute("""
                    UPDATE mesas SET estado = 'Disponible' WHERE id = ?
                """, (mesa_id,))
                self.conn.commit()
                return True
            return False
        except Exception as e:
            print(f"Error al verificar estado de mesa: {e}")
            return False
    
    def actualizar_mesas_automatico(self):
        """Actualizar vista de mesas cada 30 segundos"""
        try:
            if hasattr(self, 'frame_mesas'):
                self.cargar_mesas()
            # Programar siguiente actualización
            self.root.after(30000, self.actualizar_mesas_automatico)
        except Exception as e:
            print(f"Error en actualización automática: {e}")
            # Intentar nueva actualización en 60 segundos si hay error
            self.root.after(60000, self.actualizar_mesas_automatico)

    def generar_ticket_comanda(self, comanda_id, numero_comanda, total, observaciones):
        """Genera un ticket PDF de la comanda con formato específico de cocina"""
        try:
            # Crear carpeta 'tickets' en el directorio de la aplicación
            app_dir = self.get_app_directory()
            carpeta_tickets = os.path.join(app_dir, "tickets")
            
            if not os.path.exists(carpeta_tickets):
                os.makedirs(carpeta_tickets)
                print(f"Carpeta {carpeta_tickets} creada")

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12)
            
            # Mesa que ordenó (centrado en la parte superior)
            mesa_nombre = self.mesa_actual[1] if self.mesa_actual else "Mesa Sin Asignar"
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 8, f'{mesa_nombre} {mesa_nombre}', 0, 1, 'C')
            
            # Ficha
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 6, f'Ficha: {numero_comanda}', 0, 1, 'L')
            
            # Terminal (información del sistema)
            import platform
            import socket
            try:
                hostname = socket.gethostname()
                terminal_info = f'Terminal:{hostname} {platform.system()}'
            except:
                terminal_info = 'Terminal:Sistema Comandas'
            
            pdf.cell(0, 6, terminal_info, 0, 1, 'L')
            
            # Fecha (formato específico)
            fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            pdf.cell(0, 6, f'Fecha:{fecha_actual}', 0, 1, 'L')
            
            pdf.ln(3)
            
            # Línea de puntos separadora
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 4, '.' * 45, 0, 1, 'C')
            
            pdf.ln(2)
            
            # Obtener items de la comanda
            self.cursor.execute('''
                SELECT producto_nombre, cantidad, observaciones
                FROM items_comanda WHERE comanda_id = ?
                ORDER BY id
            ''', (comanda_id,))
            
            items = self.cursor.fetchall()
            total_articulos = 0
            
            # Lista de platillos con numeración
            pdf.set_font('Arial', '', 11)
            for i, item in enumerate(items, 1):
                cantidad = item[1]
                nombre_producto = item[0]
                observaciones_item = item[2]
                
                total_articulos += cantidad
                
                # Formato: (No. de Plato) Cantidad Nombre del Platillo
                linea_producto = f'({i}) {cantidad} {nombre_producto}'
                pdf.cell(0, 5, linea_producto, 0, 1, 'L')
                
                # Si hay observaciones del item, mostrarlas como complementos con asterisco
                if observaciones_item and observaciones_item.strip():
                    # Dividir observaciones por líneas y mostrar cada una con asterisco
                    obs_lines = observaciones_item.strip().split('\n')
                    for obs_line in obs_lines:
                        if obs_line.strip():
                            pdf.cell(0, 5, f'* {obs_line.strip()}', 0, 1, 'L')
            
            # Si hay observaciones generales de la comanda, también mostrarlas
            if observaciones and observaciones.strip():
                pdf.ln(2)
                obs_lines = observaciones.strip().split('\n')
                for obs_line in obs_lines:
                    if obs_line.strip():
                        pdf.cell(0, 5, f'* {obs_line.strip()}', 0, 1, 'L')
            
            pdf.ln(3)
            
            # Línea de puntos separadora
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 4, '.' * 45, 0, 1, 'C')
            
            pdf.ln(2)
            
            # Total de artículos
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 6, f'Total de articulos: {total_articulos}.0', 0, 1, 'L')
            
            # Guardar en subcarpeta 'tickets' del directorio de la aplicación
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(carpeta_tickets, f'comanda_{numero_comanda}_{timestamp}.pdf')
            
            # Verificar que el directorio existe antes de guardar
            if not os.path.exists(carpeta_tickets):
                os.makedirs(carpeta_tickets)
            
            pdf.output(filename)
            
            # Verificar que el archivo se creó
            if os.path.exists(filename):
                # Obtener ruta absoluta
                ruta_absoluta = os.path.abspath(filename)
                messagebox.showinfo("Ticket Generado", 
                    f"Ticket de comanda guardado exitosamente:\n\n{ruta_absoluta}\n\nTamaño: {os.path.getsize(filename)} bytes")
                
                # Abrir la carpeta donde se guardó
                if messagebox.askyesno("Abrir Carpeta", "¿Deseas abrir la carpeta donde se guardó el ticket?"):
                    os.startfile(os.path.dirname(ruta_absoluta))
            else:
                messagebox.showerror("Error", f"El archivo no se pudo crear en: {filename}")
            
        except Exception as e:
            error_msg = f"Error al generar ticket: {str(e)}\n\nDetalles técnicos:\n"
            error_msg += f"- Directorio de aplicación: {self.get_app_directory()}\n"
            error_msg += f"- Carpeta tickets: {os.path.join(self.get_app_directory(), 'tickets')}\n"
            error_msg += f"- Carpeta tickets existe: {os.path.exists(os.path.join(self.get_app_directory(), 'tickets'))}\n"
            error_msg += f"- Permisos de escritura: {os.access(self.get_app_directory(), os.W_OK)}\n"
            messagebox.showerror("Error", error_msg)
            print(f"Error detallado: {e}")
            import traceback
            traceback.print_exc()
    
    def crear_pestaña_productos(self):
        """Crea la pestaña de gestión de productos (solo admin)"""
        frame_productos = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_productos, text='🍽️ Productos')
        
        # Frame contenedor
        contenedor = tk.Frame(frame_productos, bg='#F8F9FA')
        contenedor.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Frame izquierdo - Formulario
        frame_form = tk.Frame(contenedor, bg='#F8F9FA', width=400)
        frame_form.pack(side='left', fill='y', padx=10)
        frame_form.pack_propagate(False)
        
        tk.Label(
            frame_form,
            text="Agregar/Editar Producto",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=15)
        
        # Campos del formulario
        self.producto_id = None
        
        tk.Label(frame_form, text="Nombre:", font=('Arial', 12), bg='#F8F9FA').pack(pady=3)
        self.prod_nombre = tk.Entry(frame_form, font=('Arial', 12), width=35)
        self.prod_nombre.pack(pady=3)
        
        tk.Label(frame_form, text="Precio ($):", font=('Arial', 12), bg='#F8F9FA').pack(pady=3)
        self.prod_precio = tk.Entry(frame_form, font=('Arial', 12), width=35)
        self.prod_precio.pack(pady=3)
        
        tk.Label(frame_form, text="Categoría:", font=('Arial', 12), bg='#F8F9FA').pack(pady=3)
        self.prod_categoria = ttk.Combobox(
            frame_form,
            font=('Arial', 12),
            width=33,
            values=['Hamburguesas', 'Pizzas', 'Platos Principales', 'Ensaladas', 
                   'Guarniciones', 'Bebidas', 'Cafetería', 'Postres', 'Otros']
        )
        self.prod_categoria.pack(pady=3)
        
        tk.Label(frame_form, text="Descripción:", font=('Arial', 12), bg='#F8F9FA').pack(pady=3)
        self.prod_descripcion = tk.Text(frame_form, font=('Arial', 11), width=35, height=4)
        self.prod_descripcion.pack(pady=3)
        
        # Disponibilidad
        self.disponible_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            frame_form,
            text="Producto disponible",
            variable=self.disponible_var,
            font=('Arial', 12),
            bg='#F8F9FA'
        ).pack(pady=10)
        
        # Botones
        frame_botones = tk.Frame(frame_form, bg='#F8F9FA')
        frame_botones.pack(pady=20)
        
        tk.Button(
            frame_botones,
            text="💾 Guardar",
            font=('Arial', 12, 'bold'),
            bg='#28A745',
            fg='white',
            command=self.guardar_producto,
            width=15,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            frame_botones,
            text="🗑️ Limpiar",
            font=('Arial', 12),
            bg='#6C757D',
            fg='white',
            command=self.limpiar_formulario_producto,
            width=15,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Frame derecho - Lista de productos
        frame_lista = tk.Frame(contenedor, bg='#F8F9FA')
        frame_lista.pack(side='right', fill='both', expand=True, padx=10)
        
        tk.Label(
            frame_lista,
            text="Lista de Productos",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=15)
        
        # Tabla de productos
        frame_tabla = tk.Frame(frame_lista, bg='#F8F9FA')
        frame_tabla.pack(fill='both', expand=True)
        
        scrollbar_tabla = ttk.Scrollbar(frame_tabla)
        scrollbar_tabla.pack(side='right', fill='y')
        
        self.tabla_productos = ttk.Treeview(
            frame_tabla,
            columns=('ID', 'Nombre', 'Precio', 'Categoría', 'Disponible'),
            show='headings',
            yscrollcommand=scrollbar_tabla.set
        )
        
        self.tabla_productos.heading('ID', text='ID')
        self.tabla_productos.heading('Nombre', text='Nombre')
        self.tabla_productos.heading('Precio', text='Precio')
        self.tabla_productos.heading('Categoría', text='Categoría')
        self.tabla_productos.heading('Disponible', text='Disponible')
        
        self.tabla_productos.column('ID', width=50)
        self.tabla_productos.column('Nombre', width=200)
        self.tabla_productos.column('Precio', width=100)
        self.tabla_productos.column('Categoría', width=150)
        self.tabla_productos.column('Disponible', width=100)
        
        self.tabla_productos.pack(side='left', fill='both', expand=True)
        scrollbar_tabla.config(command=self.tabla_productos.yview)
        
        self.tabla_productos.bind('<Double-Button-1>', self.editar_producto)
        
        # Botones de acción
        frame_acciones = tk.Frame(frame_lista, bg='#F8F9FA')
        frame_acciones.pack(fill='x', pady=10)
        
        tk.Button(
            frame_acciones,
            text="✏️ Editar",
            font=('Arial', 11),
            bg='#FFC107',
            fg='black',
            command=self.editar_producto,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            frame_acciones,
            text="🗑️ Eliminar",
            font=('Arial', 11),
            bg='#DC3545',
            fg='white',
            command=self.eliminar_producto,
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Cargar productos
        self.actualizar_tabla_productos()
    
    def guardar_producto(self):
        """Guarda o actualiza un producto"""
        nombre = self.prod_nombre.get().strip()
        precio = self.prod_precio.get().strip()
        categoria = self.prod_categoria.get().strip()
        descripcion = self.prod_descripcion.get("1.0", tk.END).strip()
        disponible = 1 if self.disponible_var.get() else 0
        
        if not nombre:
            messagebox.showwarning("Campo Vacío", "El nombre es obligatorio")
            return
        
        try:
            precio = float(precio) if precio else 0.0
        except ValueError:
            messagebox.showerror("Error", "El precio debe ser un número válido")
            return
        
        if self.producto_id:
            # Actualizar
            self.cursor.execute('''
                UPDATE productos 
                SET nombre=?, precio=?, categoria=?, descripcion=?, disponible=?
                WHERE id=?
            ''', (nombre, precio, categoria or 'Otros', descripcion, disponible, self.producto_id))
            messagebox.showinfo("Éxito", "Producto actualizado correctamente")
        else:
            # Insertar
            self.cursor.execute('''
                INSERT INTO productos (nombre, precio, categoria, descripcion, disponible)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre, precio, categoria or 'Otros', descripcion, disponible))
            messagebox.showinfo("Éxito", "Producto agregado correctamente")
        
        self.conn.commit()
        self.limpiar_formulario_producto()
        self.actualizar_tabla_productos()
        
        # Recargar datos en la pestaña de comandas si existe
        if hasattr(self, 'cargar_categorias'):
            self.cargar_categorias()
            self.cargar_productos()
    
    def limpiar_formulario_producto(self):
        """Limpia el formulario de productos"""
        self.producto_id = None
        self.prod_nombre.delete(0, tk.END)
        self.prod_precio.delete(0, tk.END)
        self.prod_categoria.set('')
        self.prod_descripcion.delete("1.0", tk.END)
        self.disponible_var.set(True)
    
    def actualizar_tabla_productos(self):
        """Actualiza la tabla de productos"""
        for item in self.tabla_productos.get_children():
            self.tabla_productos.delete(item)
        
        self.cursor.execute('SELECT * FROM productos ORDER BY categoria, nombre')
        productos = self.cursor.fetchall()
        
        for producto in productos:
            disponible_text = "Sí" if producto[4] else "No"
            valores = (producto[0], producto[1], f"${producto[2]}", 
                      producto[3], disponible_text)
            
            # Color según disponibilidad
            tag = 'disponible' if producto[4] else 'no_disponible'
            self.tabla_productos.insert('', 'end', values=valores, tags=(tag,))
        
        # Configurar colores
        self.tabla_productos.tag_configure('disponible', background='#D4F8D4')
        self.tabla_productos.tag_configure('no_disponible', background='#FFE6E6')
    
    def editar_producto(self, event=None):
        """Carga el producto seleccionado para editar"""
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona un producto")
            return
        
        item = self.tabla_productos.item(seleccion[0])
        producto_id = item['values'][0]
        
        # Obtener producto completo de la BD
        self.cursor.execute('SELECT * FROM productos WHERE id = ?', (producto_id,))
        producto = self.cursor.fetchone()
        
        if producto:
            self.producto_id = producto[0]
            self.prod_nombre.delete(0, tk.END)
            self.prod_nombre.insert(0, producto[1])
            self.prod_precio.delete(0, tk.END)
            self.prod_precio.insert(0, str(producto[2]))
            self.prod_categoria.set(producto[3])
            self.prod_descripcion.delete("1.0", tk.END)
            self.prod_descripcion.insert("1.0", producto[5] if producto[5] else "")
            self.disponible_var.set(bool(producto[4]))
    
    def eliminar_producto(self):
        """Elimina el producto seleccionado"""
        seleccion = self.tabla_productos.selection()
        if not seleccion:
            messagebox.showwarning("Selección", "Selecciona un producto")
            return
        
        if messagebox.askyesno("Confirmar", "¿Eliminar este producto?"):
            item = self.tabla_productos.item(seleccion[0])
            producto_id = item['values'][0]
            
            self.cursor.execute('DELETE FROM productos WHERE id = ?', (producto_id,))
            self.conn.commit()
            
            self.actualizar_tabla_productos()
            messagebox.showinfo("Éxito", "Producto eliminado correctamente")
    
    def crear_pestaña_mesas(self):
        """Crea la pestaña de gestión de mesas"""
        frame_mesas = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_mesas, text='🪑 Mesas')
        
        # Marco principal
        main_frame = tk.Frame(frame_mesas, bg='#F8F9FA')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="🪑 Gestión de Mesas",
            font=('Arial', 20, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        )
        title_label.pack(pady=(0, 20))
        
        # Frame superior con botones de acción
        action_frame = tk.Frame(main_frame, bg='#F8F9FA')
        action_frame.pack(fill='x', pady=(0, 20))
        
        # Botón Nueva Mesa
        btn_nueva_mesa = tk.Button(
            action_frame,
            text="➕ Nueva Mesa",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            command=self.nueva_mesa,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_nueva_mesa.pack(side='left', padx=(0, 10))
        
        # Botón Editar Mesa
        btn_editar_mesa = tk.Button(
            action_frame,
            text="✏️ Editar Mesa",
            font=('Arial', 12, 'bold'),
            bg='#3498DB',
            fg='white',
            command=self.editar_mesa,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_editar_mesa.pack(side='left', padx=(0, 10))
        
        # Botón Eliminar Mesa
        btn_eliminar_mesa = tk.Button(
            action_frame,
            text="🗑️ Eliminar Mesa",
            font=('Arial', 12, 'bold'),
            bg='#E74C3C',
            fg='white',
            command=self.eliminar_mesa,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_eliminar_mesa.pack(side='left', padx=(0, 10))
        
        # Botón Actualizar Lista
        btn_actualizar = tk.Button(
            action_frame,
            text="🔄 Actualizar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=self.actualizar_lista_mesas,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_actualizar.pack(side='right')
        
        # Frame para la lista de mesas
        lista_frame = tk.Frame(main_frame, bg='#F8F9FA')
        lista_frame.pack(fill='both', expand=True)
        
        # Crear Treeview para mostrar las mesas
        self.tree_mesas = ttk.Treeview(
            lista_frame,
            columns=('ID', 'Nombre', 'Capacidad', 'Estado', 'Ubicación'),
            show='headings',
            height=15
        )
        
        # Configurar columnas
        self.tree_mesas.heading('ID', text='ID')
        self.tree_mesas.heading('Nombre', text='Nombre')
        self.tree_mesas.heading('Capacidad', text='Capacidad')
        self.tree_mesas.heading('Estado', text='Estado')
        self.tree_mesas.heading('Ubicación', text='Ubicación')
        
        # Configurar ancho de columnas
        self.tree_mesas.column('ID', width=50, anchor='center')
        self.tree_mesas.column('Nombre', width=150, anchor='center')
        self.tree_mesas.column('Capacidad', width=100, anchor='center')
        self.tree_mesas.column('Estado', width=100, anchor='center')
        self.tree_mesas.column('Ubicación', width=200, anchor='center')
        
        # Scrollbar para el Treeview
        scrollbar_mesas = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_mesas.yview)
        self.tree_mesas.configure(yscrollcommand=scrollbar_mesas.set)
        
        # Empaquetar Treeview y scrollbar
        self.tree_mesas.pack(side='left', fill='both', expand=True)
        scrollbar_mesas.pack(side='right', fill='y')
        
        # Cargar las mesas existentes
        self.actualizar_lista_mesas()
    
    def actualizar_lista_mesas(self):
        """Actualiza la lista de mesas en el Treeview"""
        # Limpiar lista actual
        for item in self.tree_mesas.get_children():
            self.tree_mesas.delete(item)
        
        # Cargar mesas desde la base de datos
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, nombre, capacidad, estado, ubicacion 
            FROM mesas 
            ORDER BY nombre
        """)
        mesas = cursor.fetchall()
        
        # Agregar mesas al Treeview
        for mesa in mesas:
            self.tree_mesas.insert('', 'end', values=mesa)
    
    def nueva_mesa(self):
        """Abre ventana para crear una nueva mesa"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Mesa")
        ventana.geometry("400x300")
        ventana.configure(bg='#F8F9FA')
        ventana.resizable(False, False)
        
        # Centrar ventana
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Título
        tk.Label(
            ventana,
            text="➕ Nueva Mesa",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        ).pack(pady=20)
        
        # Frame para campos
        campos_frame = tk.Frame(ventana, bg='#F8F9FA')
        campos_frame.pack(padx=40, pady=20, fill='x')
        
        # Campo Nombre
        tk.Label(campos_frame, text="Nombre:", font=('Arial', 12), bg='#F8F9FA').grid(row=0, column=0, sticky='w', pady=5)
        entry_nombre = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_nombre.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Campo Capacidad
        tk.Label(campos_frame, text="Capacidad:", font=('Arial', 12), bg='#F8F9FA').grid(row=1, column=0, sticky='w', pady=5)
        entry_capacidad = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_capacidad.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Campo Ubicación
        tk.Label(campos_frame, text="Ubicación:", font=('Arial', 12), bg='#F8F9FA').grid(row=2, column=0, sticky='w', pady=5)
        entry_ubicacion = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_ubicacion.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Campo Estado
        tk.Label(campos_frame, text="Estado:", font=('Arial', 12), bg='#F8F9FA').grid(row=3, column=0, sticky='w', pady=5)
        combo_estado = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_estado['values'] = ('Disponible', 'Ocupada', 'Reservada', 'Fuera de servicio')
        combo_estado.current(0)  # Disponible por defecto
        combo_estado.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        def guardar_mesa():
            nombre = entry_nombre.get().strip()
            capacidad = entry_capacidad.get().strip()
            ubicacion = entry_ubicacion.get().strip()
            estado = combo_estado.get()
            
            if not nombre or not capacidad or not ubicacion:
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            try:
                capacidad = int(capacidad)
                if capacidad <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "La capacidad debe ser un número entero positivo")
                return
            
            # Verificar que no exista una mesa con el mismo nombre
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM mesas WHERE nombre = ?", (nombre,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"Ya existe una mesa con el nombre '{nombre}'")
                return
            
            # Insertar nueva mesa
            cursor.execute("""
                INSERT INTO mesas (nombre, capacidad, estado, ubicacion)
                VALUES (?, ?, ?, ?)
            """, (nombre, capacidad, estado, ubicacion))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Mesa '{nombre}' creada correctamente")
            ventana.destroy()
            self.actualizar_lista_mesas()
            self.cargar_mesas()  # Actualizar también la lista de mesas en comandas
        
        # Frame para botones
        botones_frame = tk.Frame(ventana, bg='#F8F9FA')
        botones_frame.pack(pady=20)
        
        # Botón Guardar
        btn_guardar = tk.Button(
            botones_frame,
            text="💾 Guardar",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            command=guardar_mesa,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_guardar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=ventana.destroy,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Enfocar primer campo
        entry_nombre.focus()
    
    def editar_mesa(self):
        """Abre ventana para editar la mesa seleccionada"""
        seleccion = self.tree_mesas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una mesa para editar")
            return
        
        # Obtener datos de la mesa seleccionada
        item = self.tree_mesas.item(seleccion[0])
        valores = item['values']
        mesa_id, nombre_actual, capacidad_actual, estado_actual, ubicacion_actual = valores
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Editar Mesa")
        ventana.geometry("400x300")
        ventana.configure(bg='#F8F9FA')
        ventana.resizable(False, False)
        
        # Centrar ventana
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Título
        tk.Label(
            ventana,
            text="✏️ Editar Mesa",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        ).pack(pady=20)
        
        # Frame para campos
        campos_frame = tk.Frame(ventana, bg='#F8F9FA')
        campos_frame.pack(padx=40, pady=20, fill='x')
        
        # Campo Nombre
        tk.Label(campos_frame, text="Nombre:", font=('Arial', 12), bg='#F8F9FA').grid(row=0, column=0, sticky='w', pady=5)
        entry_nombre = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_nombre.insert(0, nombre_actual)
        entry_nombre.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Campo Capacidad
        tk.Label(campos_frame, text="Capacidad:", font=('Arial', 12), bg='#F8F9FA').grid(row=1, column=0, sticky='w', pady=5)
        entry_capacidad = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_capacidad.insert(0, str(capacidad_actual))
        entry_capacidad.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Campo Ubicación
        tk.Label(campos_frame, text="Ubicación:", font=('Arial', 12), bg='#F8F9FA').grid(row=2, column=0, sticky='w', pady=5)
        entry_ubicacion = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_ubicacion.insert(0, ubicacion_actual)
        entry_ubicacion.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Campo Estado
        tk.Label(campos_frame, text="Estado:", font=('Arial', 12), bg='#F8F9FA').grid(row=3, column=0, sticky='w', pady=5)
        combo_estado = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_estado['values'] = ('Disponible', 'Ocupada', 'Reservada', 'Fuera de servicio')
        combo_estado.set(estado_actual)
        combo_estado.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        def actualizar_mesa():
            nombre = entry_nombre.get().strip()
            capacidad = entry_capacidad.get().strip()
            ubicacion = entry_ubicacion.get().strip()
            estado = combo_estado.get()
            
            if not nombre or not capacidad or not ubicacion:
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            try:
                capacidad = int(capacidad)
                if capacidad <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "La capacidad debe ser un número entero positivo")
                return
            
            # Verificar que no exista otra mesa con el mismo nombre (excepto la actual)
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM mesas WHERE nombre = ? AND id != ?", (nombre, mesa_id))
            if cursor.fetchone():
                messagebox.showerror("Error", f"Ya existe otra mesa con el nombre '{nombre}'")
                return
            
            # Actualizar mesa
            cursor.execute("""
                UPDATE mesas 
                SET nombre = ?, capacidad = ?, estado = ?, ubicacion = ?
                WHERE id = ?
            """, (nombre, capacidad, estado, ubicacion, mesa_id))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Mesa '{nombre}' actualizada correctamente")
            ventana.destroy()
            self.actualizar_lista_mesas()
            self.cargar_mesas()  # Actualizar también la lista de mesas en comandas
        
        # Frame para botones
        botones_frame = tk.Frame(ventana, bg='#F8F9FA')
        botones_frame.pack(pady=20)
        
        # Botón Actualizar
        btn_actualizar = tk.Button(
            botones_frame,
            text="💾 Actualizar",
            font=('Arial', 12, 'bold'),
            bg='#3498DB',
            fg='white',
            command=actualizar_mesa,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_actualizar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=ventana.destroy,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Enfocar primer campo
        entry_nombre.focus()
    
    def eliminar_mesa(self):
        """Elimina la mesa seleccionada"""
        seleccion = self.tree_mesas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una mesa para eliminar")
            return
        
        # Obtener datos de la mesa seleccionada
        item = self.tree_mesas.item(seleccion[0])
        valores = item['values']
        mesa_id, nombre, capacidad, estado, ubicacion = valores
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación", 
                                   f"¿Estás seguro de que deseas eliminar la mesa '{nombre}'?\n\n"
                                   f"Esta acción no se puede deshacer."):
            return
        
        # Verificar si la mesa tiene comandas pendientes
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM comandas 
            WHERE mesa_id = ? AND estado IN ('Pendiente', 'En preparación')
        """, (mesa_id,))
        comandas_pendientes = cursor.fetchone()[0]
        
        if comandas_pendientes > 0:
            messagebox.showerror("Error", 
                               f"No se puede eliminar la mesa '{nombre}' porque tiene {comandas_pendientes} comanda(s) pendiente(s).\n\n"
                               f"Completa o cancela las comandas antes de eliminar la mesa.")
            return
        
        try:
            # Eliminar mesa
            cursor.execute("DELETE FROM mesas WHERE id = ?", (mesa_id,))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Mesa '{nombre}' eliminada correctamente")
            self.actualizar_lista_mesas()
            self.cargar_mesas()  # Actualizar también la lista de mesas en comandas
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar la mesa: {str(e)}")
    
    def crear_pestaña_reportes(self):
        """Crea la pestaña de reportes"""
        frame_reportes = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_reportes, text='📊 Reportes')
        
        # Implementar reportes...
        tk.Label(
            frame_reportes,
            text="🚧 Reportes - En desarrollo",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=50)
    
    def crear_pestaña_usuarios(self):
        """Crea la pestaña de gestión de usuarios"""
        frame_usuarios = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_usuarios, text='👥 Usuarios')
        
        # Marco principal
        main_frame = tk.Frame(frame_usuarios, bg='#F8F9FA')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Título
        title_label = tk.Label(
            main_frame,
            text="👥 Gestión de Usuarios",
            font=('Arial', 20, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        )
        title_label.pack(pady=(0, 20))
        
        # Frame superior con botones de acción
        action_frame = tk.Frame(main_frame, bg='#F8F9FA')
        action_frame.pack(fill='x', pady=(0, 20))
        
        # Botón Nuevo Usuario
        btn_nuevo_usuario = tk.Button(
            action_frame,
            text="➕ Nuevo Usuario",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            command=self.nuevo_usuario,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_nuevo_usuario.pack(side='left', padx=(0, 10))
        
        # Botón Editar Usuario
        btn_editar_usuario = tk.Button(
            action_frame,
            text="✏️ Editar Usuario",
            font=('Arial', 12, 'bold'),
            bg='#3498DB',
            fg='white',
            command=self.editar_usuario,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_editar_usuario.pack(side='left', padx=(0, 10))
        
        # Botón Eliminar Usuario
        btn_eliminar_usuario = tk.Button(
            action_frame,
            text="�️ Eliminar Usuario",
            font=('Arial', 12, 'bold'),
            bg='#E74C3C',
            fg='white',
            command=self.eliminar_usuario,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_eliminar_usuario.pack(side='left', padx=(0, 10))
        
        # Botón Cambiar Contraseña
        btn_cambiar_password = tk.Button(
            action_frame,
            text="🔑 Cambiar Contraseña",
            font=('Arial', 12, 'bold'),
            bg='#F39C12',
            fg='white',
            command=self.cambiar_password_usuario,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_cambiar_password.pack(side='left', padx=(0, 10))
        
        # Botón Actualizar Lista
        btn_actualizar = tk.Button(
            action_frame,
            text="🔄 Actualizar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=self.actualizar_lista_usuarios,
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        btn_actualizar.pack(side='right')
        
        # Frame para la lista de usuarios
        lista_frame = tk.Frame(main_frame, bg='#F8F9FA')
        lista_frame.pack(fill='both', expand=True)
        
        # Crear Treeview para mostrar los usuarios
        self.tree_usuarios = ttk.Treeview(
            lista_frame,
            columns=('ID', 'Usuario', 'Nombre', 'Rol', 'Estado', 'Último acceso'),
            show='headings',
            height=15
        )
        
        # Configurar columnas
        self.tree_usuarios.heading('ID', text='ID')
        self.tree_usuarios.heading('Usuario', text='Usuario')
        self.tree_usuarios.heading('Nombre', text='Nombre Completo')
        self.tree_usuarios.heading('Rol', text='Rol')
        self.tree_usuarios.heading('Estado', text='Estado')
        self.tree_usuarios.heading('Último acceso', text='Último Acceso')
        
        # Configurar ancho de columnas
        self.tree_usuarios.column('ID', width=50, anchor='center')
        self.tree_usuarios.column('Usuario', width=120, anchor='center')
        self.tree_usuarios.column('Nombre', width=200, anchor='center')
        self.tree_usuarios.column('Rol', width=100, anchor='center')
        self.tree_usuarios.column('Estado', width=100, anchor='center')
        self.tree_usuarios.column('Último acceso', width=150, anchor='center')
        
        # Scrollbar para el Treeview
        scrollbar_usuarios = ttk.Scrollbar(lista_frame, orient='vertical', command=self.tree_usuarios.yview)
        self.tree_usuarios.configure(yscrollcommand=scrollbar_usuarios.set)
        
        # Empaquetar Treeview y scrollbar
        self.tree_usuarios.pack(side='left', fill='both', expand=True)
        scrollbar_usuarios.pack(side='right', fill='y')
        
        # Cargar los usuarios existentes
        self.actualizar_lista_usuarios()
    
    def actualizar_lista_usuarios(self):
        """Actualiza la lista de usuarios en el Treeview"""
        # Limpiar lista actual
        for item in self.tree_usuarios.get_children():
            self.tree_usuarios.delete(item)
        
        # Cargar usuarios desde la base de datos
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, usuario, nombre_completo, rol, activo, ultimo_acceso
            FROM usuarios 
            ORDER BY usuario
        """)
        usuarios = cursor.fetchall()
        
        # Agregar usuarios al Treeview
        for usuario in usuarios:
            id_usuario, nombre_usuario, nombre_completo, rol, activo, ultimo_acceso = usuario
            estado = "Activo" if activo else "Inactivo"
            ultimo_acceso_str = ultimo_acceso if ultimo_acceso else "Nunca"
            
            self.tree_usuarios.insert('', 'end', values=(
                id_usuario, nombre_usuario, nombre_completo, rol, estado, ultimo_acceso_str
            ))
    
    def nuevo_usuario(self):
        """Abre ventana para crear un nuevo usuario"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Nuevo Usuario")
        ventana.geometry("450x400")
        ventana.configure(bg='#F8F9FA')
        ventana.resizable(False, False)
        
        # Centrar ventana
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Título
        tk.Label(
            ventana,
            text="➕ Nuevo Usuario",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        ).pack(pady=20)
        
        # Frame para campos
        campos_frame = tk.Frame(ventana, bg='#F8F9FA')
        campos_frame.pack(padx=40, pady=20, fill='x')
        
        # Campo Usuario
        tk.Label(campos_frame, text="Usuario:", font=('Arial', 12), bg='#F8F9FA').grid(row=0, column=0, sticky='w', pady=5)
        entry_usuario = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_usuario.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Campo Nombre Completo
        tk.Label(campos_frame, text="Nombre Completo:", font=('Arial', 12), bg='#F8F9FA').grid(row=1, column=0, sticky='w', pady=5)
        entry_nombre = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_nombre.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Campo Contraseña
        tk.Label(campos_frame, text="Contraseña:", font=('Arial', 12), bg='#F8F9FA').grid(row=2, column=0, sticky='w', pady=5)
        entry_password = tk.Entry(campos_frame, font=('Arial', 12), width=25, show="*")
        entry_password.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Campo Confirmar Contraseña
        tk.Label(campos_frame, text="Confirmar Contraseña:", font=('Arial', 12), bg='#F8F9FA').grid(row=3, column=0, sticky='w', pady=5)
        entry_confirm_password = tk.Entry(campos_frame, font=('Arial', 12), width=25, show="*")
        entry_confirm_password.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        # Campo Rol
        tk.Label(campos_frame, text="Rol:", font=('Arial', 12), bg='#F8F9FA').grid(row=4, column=0, sticky='w', pady=5)
        combo_rol = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_rol['values'] = ('Administrador', 'Mesero', 'Cajero', 'Cocinero')
        combo_rol.current(1)  # Mesero por defecto
        combo_rol.grid(row=4, column=1, pady=5, padx=(10, 0))
        
        # Campo Estado
        tk.Label(campos_frame, text="Estado:", font=('Arial', 12), bg='#F8F9FA').grid(row=5, column=0, sticky='w', pady=5)
        combo_estado = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_estado['values'] = ('Activo', 'Inactivo')
        combo_estado.current(0)  # Activo por defecto
        combo_estado.grid(row=5, column=1, pady=5, padx=(10, 0))
        
        def guardar_usuario():
            usuario = entry_usuario.get().strip()
            nombre_completo = entry_nombre.get().strip()
            password = entry_password.get()
            confirm_password = entry_confirm_password.get()
            rol = combo_rol.get()
            estado = combo_estado.get()
            
            if not usuario or not nombre_completo or not password or not confirm_password:
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            if password != confirm_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(password) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres")
                return
            
            # Verificar que no exista un usuario con el mismo nombre
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"Ya existe un usuario con el nombre '{usuario}'")
                return
            
            # Insertar nuevo usuario
            activo = 1 if estado == 'Activo' else 0
            cursor.execute("""
                INSERT INTO usuarios (nombre, usuario, password, nombre_completo, rol, activo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario, usuario, password, nombre_completo, rol, activo))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Usuario '{usuario}' creado correctamente")
            ventana.destroy()
            self.actualizar_lista_usuarios()
        
        # Frame para botones
        botones_frame = tk.Frame(ventana, bg='#F8F9FA')
        botones_frame.pack(pady=20)
        
        # Botón Guardar
        btn_guardar = tk.Button(
            botones_frame,
            text="💾 Guardar",
            font=('Arial', 12, 'bold'),
            bg='#27AE60',
            fg='white',
            command=guardar_usuario,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_guardar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=ventana.destroy,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Enfocar primer campo
        entry_usuario.focus()
    
    def editar_usuario(self):
        """Abre ventana para editar el usuario seleccionado"""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para editar")
            return
        
        # Obtener datos del usuario seleccionado
        item = self.tree_usuarios.item(seleccion[0])
        valores = item['values']
        usuario_id, nombre_usuario, nombre_completo, rol_actual, estado_actual, ultimo_acceso = valores
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Editar Usuario")
        ventana.geometry("450x350")
        ventana.configure(bg='#F8F9FA')
        ventana.resizable(False, False)
        
        # Centrar ventana
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Título
        tk.Label(
            ventana,
            text="✏️ Editar Usuario",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50'
        ).pack(pady=20)
        
        # Frame para campos
        campos_frame = tk.Frame(ventana, bg='#F8F9FA')
        campos_frame.pack(padx=40, pady=20, fill='x')
        
        # Campo Usuario
        tk.Label(campos_frame, text="Usuario:", font=('Arial', 12), bg='#F8F9FA').grid(row=0, column=0, sticky='w', pady=5)
        entry_usuario = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_usuario.insert(0, nombre_usuario)
        entry_usuario.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Campo Nombre Completo
        tk.Label(campos_frame, text="Nombre Completo:", font=('Arial', 12), bg='#F8F9FA').grid(row=1, column=0, sticky='w', pady=5)
        entry_nombre = tk.Entry(campos_frame, font=('Arial', 12), width=25)
        entry_nombre.insert(0, nombre_completo)
        entry_nombre.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # Campo Rol
        tk.Label(campos_frame, text="Rol:", font=('Arial', 12), bg='#F8F9FA').grid(row=2, column=0, sticky='w', pady=5)
        combo_rol = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_rol['values'] = ('Administrador', 'Mesero', 'Cajero', 'Cocinero')
        combo_rol.set(rol_actual)
        combo_rol.grid(row=2, column=1, pady=5, padx=(10, 0))
        
        # Campo Estado
        tk.Label(campos_frame, text="Estado:", font=('Arial', 12), bg='#F8F9FA').grid(row=3, column=0, sticky='w', pady=5)
        combo_estado = ttk.Combobox(campos_frame, font=('Arial', 12), width=22, state='readonly')
        combo_estado['values'] = ('Activo', 'Inactivo')
        combo_estado.set(estado_actual)
        combo_estado.grid(row=3, column=1, pady=5, padx=(10, 0))
        
        def actualizar_usuario():
            usuario = entry_usuario.get().strip()
            nombre_completo = entry_nombre.get().strip()
            rol = combo_rol.get()
            estado = combo_estado.get()
            
            if not usuario or not nombre_completo:
                messagebox.showerror("Error", "El usuario y nombre completo son obligatorios")
                return
            
            # Verificar que no exista otro usuario con el mismo nombre (excepto el actual)
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE usuario = ? AND id != ?", (usuario, usuario_id))
            if cursor.fetchone():
                messagebox.showerror("Error", f"Ya existe otro usuario con el nombre '{usuario}'")
                return
            
            # Actualizar usuario
            activo = 1 if estado == 'Activo' else 0
            cursor.execute("""
                UPDATE usuarios 
                SET nombre = ?, usuario = ?, nombre_completo = ?, rol = ?, activo = ?
                WHERE id = ?
            """, (usuario, usuario, nombre_completo, rol, activo, usuario_id))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Usuario '{usuario}' actualizado correctamente")
            ventana.destroy()
            self.actualizar_lista_usuarios()
        
        # Frame para botones
        botones_frame = tk.Frame(ventana, bg='#F8F9FA')
        botones_frame.pack(pady=20)
        
        # Botón Actualizar
        btn_actualizar = tk.Button(
            botones_frame,
            text="💾 Actualizar",
            font=('Arial', 12, 'bold'),
            bg='#3498DB',
            fg='white',
            command=actualizar_usuario,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_actualizar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=ventana.destroy,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Enfocar primer campo
        entry_usuario.focus()
    
    def eliminar_usuario(self):
        """Elimina el usuario seleccionado"""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para eliminar")
            return
        
        # Obtener datos del usuario seleccionado
        item = self.tree_usuarios.item(seleccion[0])
        valores = item['values']
        usuario_id, nombre_usuario, nombre_completo, rol, estado, ultimo_acceso = valores
        
        # No permitir eliminar el usuario actual
        if self.usuario_actual['usuario'] == nombre_usuario:
            messagebox.showerror("Error", "No puedes eliminar tu propio usuario")
            return
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar Eliminación", 
                                   f"¿Estás seguro de que deseas eliminar el usuario '{nombre_usuario}'?\n\n"
                                   f"Esta acción no se puede deshacer."):
            return
        
        try:
            # Eliminar usuario
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Usuario '{nombre_usuario}' eliminado correctamente")
            self.actualizar_lista_usuarios()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar el usuario: {str(e)}")
    
    def cambiar_password_usuario(self):
        """Cambia la contraseña del usuario seleccionado"""
        seleccion = self.tree_usuarios.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un usuario para cambiar la contraseña")
            return
        
        # Obtener datos del usuario seleccionado
        item = self.tree_usuarios.item(seleccion[0])
        valores = item['values']
        usuario_id, nombre_usuario, nombre_completo, rol, estado, ultimo_acceso = valores
        
        ventana = tk.Toplevel(self.root)
        ventana.title("Cambiar Contraseña")
        ventana.geometry("400x250")
        ventana.configure(bg='#F8F9FA')
        ventana.resizable(False, False)
        
        # Centrar ventana
        ventana.transient(self.root)
        ventana.grab_set()
        
        # Título
        tk.Label(
            ventana,
            text=f"🔑 Cambiar Contraseña\nUsuario: {nombre_usuario}",
            font=('Arial', 14, 'bold'),
            bg='#F8F9FA',
            fg='#2C3E50',
            justify='center'
        ).pack(pady=20)
        
        # Frame para campos
        campos_frame = tk.Frame(ventana, bg='#F8F9FA')
        campos_frame.pack(padx=40, pady=20, fill='x')
        
        # Campo Nueva Contraseña
        tk.Label(campos_frame, text="Nueva Contraseña:", font=('Arial', 12), bg='#F8F9FA').grid(row=0, column=0, sticky='w', pady=5)
        entry_nueva_password = tk.Entry(campos_frame, font=('Arial', 12), width=25, show="*")
        entry_nueva_password.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Campo Confirmar Nueva Contraseña
        tk.Label(campos_frame, text="Confirmar Contraseña:", font=('Arial', 12), bg='#F8F9FA').grid(row=1, column=0, sticky='w', pady=5)
        entry_confirmar_password = tk.Entry(campos_frame, font=('Arial', 12), width=25, show="*")
        entry_confirmar_password.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        def cambiar_password():
            nueva_password = entry_nueva_password.get()
            confirmar_password = entry_confirmar_password.get()
            
            if not nueva_password or not confirmar_password:
                messagebox.showerror("Error", "Todos los campos son obligatorios")
                return
            
            if nueva_password != confirmar_password:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if len(nueva_password) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres")
                return
            
            # Actualizar contraseña
            cursor = self.conn.cursor()
            cursor.execute("UPDATE usuarios SET password = ? WHERE id = ?", (nueva_password, usuario_id))
            self.conn.commit()
            
            messagebox.showinfo("Éxito", f"Contraseña del usuario '{nombre_usuario}' cambiada correctamente")
            ventana.destroy()
        
        # Frame para botones
        botones_frame = tk.Frame(ventana, bg='#F8F9FA')
        botones_frame.pack(pady=20)
        
        # Botón Cambiar
        btn_cambiar = tk.Button(
            botones_frame,
            text="🔑 Cambiar",
            font=('Arial', 12, 'bold'),
            bg='#F39C12',
            fg='white',
            command=cambiar_password,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cambiar.pack(side='left', padx=(0, 10))
        
        # Botón Cancelar
        btn_cancelar = tk.Button(
            botones_frame,
            text="❌ Cancelar",
            font=('Arial', 12, 'bold'),
            bg='#95A5A6',
            fg='white',
            command=ventana.destroy,
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2'
        )
        btn_cancelar.pack(side='left')
        
        # Enfocar primer campo
        entry_nueva_password.focus()
    
    def logout(self):
        """Cierra sesión y vuelve al login"""
        if messagebox.askyesno("Cerrar Sesión", "¿Seguro que deseas cerrar sesión?"):
            self.conn.close()
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaComandas(root)
    root.mainloop()