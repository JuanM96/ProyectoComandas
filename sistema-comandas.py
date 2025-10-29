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
        
        # Maximizar ventana al iniciar
        self.root.state('zoomed')  # Para Windows
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
        
    def init_database(self):
        """Inicializa la base de datos y crea las tablas"""
        self.conn = sqlite3.connect('comandas.db')
        self.cursor = self.conn.cursor()
        
        # Tabla de usuarios
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        ''')
        
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
                numero TEXT UNIQUE NOT NULL,
                capacidad INTEGER DEFAULT 4,
                estado TEXT DEFAULT 'libre'
            )
        ''')
        
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
        self.cursor.execute("SELECT * FROM usuarios WHERE nombre = 'Administrador'")
        if not self.cursor.fetchone():
            self.cursor.execute('''
                INSERT INTO usuarios (nombre, password, rol) 
                VALUES ('Administrador', 'admin123', 'admin')
            ''')
        
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
                ('Mesa 1', 4, 'libre'),
                ('Mesa 2', 6, 'libre'),
                ('Mesa 3', 2, 'libre'),
                ('Mesa 4', 4, 'libre'),
                ('Mesa 5', 8, 'libre'),
                ('Barra 1', 2, 'libre'),
                ('Barra 2', 2, 'libre'),
                ('Terraza 1', 6, 'libre')
            ]
            self.cursor.executemany('''
                INSERT INTO mesas (numero, capacidad, estado)
                VALUES (?, ?, ?)
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
        
        self.cursor.execute(
            "SELECT * FROM usuarios WHERE nombre = ? AND password = ?",
            (usuario, password)
        )
        user = self.cursor.fetchone()
        
        if user:
            self.usuario_actual = {
                'id': user[0],
                'nombre': user[1],
                'rol': user[3]
            }
            self.login_frame.destroy()
            self.mostrar_interfaz_principal()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    def mostrar_interfaz_principal(self):
        """Muestra la interfaz principal del sistema"""
        # Header
        header = tk.Frame(self.root, bg='#DC3545', height=80)
        header.pack(fill='x')
        
        tk.Label(
            header,
            text="🍽️ Sistema de Comandas",
            font=('Arial', 20, 'bold'),
            bg='#DC3545',
            fg='white'
        ).pack(side='left', padx=20, pady=15)
        
        tk.Label(
            header,
            text=f"👤 {self.usuario_actual['nombre']}",
            font=('Arial', 12),
            bg='#DC3545',
            fg='white'
        ).pack(side='right', padx=10)
        
        tk.Button(
            header,
            text="Cerrar Sesión",
            font=('Arial', 11),
            bg="#B02A37",
            fg='white',
            command=self.logout,
            cursor='hand2'
        ).pack(side='right', padx=10)
        
        # Notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Crear pestañas según el rol
        self.crear_pestaña_comandas()
        if self.usuario_actual['rol'] == 'admin':
            self.crear_pestaña_productos()
            self.crear_pestaña_mesas()
            self.crear_pestaña_reportes()
            self.crear_pestaña_usuarios()
    
    def crear_pestaña_comandas(self):
        """Crea la pestaña principal de comandas (diseño táctil)"""
        frame_comandas = tk.Frame(self.notebook, bg='#F8F9FA')
        self.notebook.add(frame_comandas, text='📝 Nueva Comanda')

        # Frame superior - Selección de mesa
        frame_mesa = tk.Frame(frame_comandas, bg='#E9ECEF', relief='raised', bd=2)
        frame_mesa.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            frame_mesa,
            text="🪑 Seleccionar Mesa:",
            font=('Arial', 16, 'bold'),
            bg='#E9ECEF'
        ).pack(side='left', padx=10, pady=10)
        
        # Botones de mesas
        self.frame_mesas = tk.Frame(frame_mesa, bg='#E9ECEF')
        self.frame_mesas.pack(side='left', fill='x', expand=True, padx=10, pady=5)
        
        self.label_mesa_actual = tk.Label(
            frame_mesa,
            text="Mesa: No seleccionada",
            font=('Arial', 14, 'bold'),
            bg='#E9ECEF',
            fg='#DC3545'
        )
        self.label_mesa_actual.pack(side='right', padx=10, pady=10)
        
        # Contenedor principal
        contenedor_principal = tk.Frame(frame_comandas, bg='#F8F9FA')
        contenedor_principal.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Frame izquierdo - Categorías y productos
        frame_izq = tk.Frame(contenedor_principal, bg='#F8F9FA')
        frame_izq.pack(side='left', fill='both', expand=True, padx=5)
        
        # Categorías (botones grandes para táctil)
        tk.Label(
            frame_izq,
            text="📂 Categorías",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=10)
        
        self.frame_categorias = tk.Frame(frame_izq, bg='#F8F9FA')
        self.frame_categorias.pack(fill='x', pady=5)
        
        # Productos (grid de botones grandes)
        tk.Label(
            frame_izq,
            text="🍽️ Productos",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=(20, 10))
        
        # Frame con scroll para productos
        canvas_productos = tk.Canvas(frame_izq, bg='#F8F9FA', height=400)
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
        
        # Frame derecho - Comanda actual
        frame_der = tk.Frame(contenedor_principal, bg='#F8F9FA', width=400)
        frame_der.pack(side='right', fill='both', padx=5)
        frame_der.pack_propagate(False)
        
        tk.Label(
            frame_der,
            text="📋 Comanda Actual",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=10)
        
        # Lista de la comanda
        frame_comanda = tk.Frame(frame_der, bg='#F8F9FA')
        frame_comanda.pack(fill='both', expand=True, pady=10)
        
        scrollbar_comanda = tk.Scrollbar(frame_comanda)
        scrollbar_comanda.pack(side='right', fill='y')
        
        self.lista_comanda = tk.Listbox(
            frame_comanda,
            font=('Arial', 11),
            yscrollcommand=scrollbar_comanda.set,
            height=15
        )
        self.lista_comanda.pack(side='left', fill='both', expand=True)
        scrollbar_comanda.config(command=self.lista_comanda.yview)
        
        # Botones de comanda (grandes para táctil)
        frame_botones_comanda = tk.Frame(frame_der, bg='#F8F9FA')
        frame_botones_comanda.pack(fill='x', pady=10)
        
        tk.Button(
            frame_botones_comanda,
            text="➖ Quitar",
            font=('Arial', 12, 'bold'),
            bg='#FFC107',
            fg='black',
            command=self.quitar_de_comanda,
            height=2,
            cursor='hand2'
        ).pack(fill='x', pady=2)
        
        tk.Button(
            frame_botones_comanda,
            text="🗑️ Limpiar Todo",
            font=('Arial', 12, 'bold'),
            bg='#DC3545',
            fg='white',
            command=self.limpiar_comanda,
            height=2,
            cursor='hand2'
        ).pack(fill='x', pady=2)
        
        # Observaciones
        tk.Label(
            frame_der,
            text="📝 Observaciones:",
            font=('Arial', 12, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=(10, 5))
        
        self.text_observaciones = tk.Text(
            frame_der,
            height=3,
            font=('Arial', 11),
            wrap=tk.WORD
        )
        self.text_observaciones.pack(fill='x', pady=5)
        
        # Total
        self.label_total = tk.Label(
            frame_der,
            text="TOTAL: $0",
            font=('Arial', 20, 'bold'),
            bg='#F8F9FA',
            fg='#DC3545'
        )
        self.label_total.pack(pady=15)
        
        # Botón finalizar comanda (muy grande para táctil)
        tk.Button(
            frame_der,
            text="✅ ENVIAR COMANDA",
            font=('Arial', 16, 'bold'),
            bg='#28A745',
            fg='white',
            command=self.finalizar_comanda,
            height=3,
            cursor='hand2'
        ).pack(fill='x', pady=10)
        
        # Inicializar
        self.cargar_mesas()
        self.cargar_categorias()
        self.cargar_productos()
    
    def cargar_mesas(self):
        """Carga los botones de mesas"""
        # Limpiar frame
        for widget in self.frame_mesas.winfo_children():
            widget.destroy()
        
        self.cursor.execute('SELECT * FROM mesas ORDER BY numero')
        mesas = self.cursor.fetchall()
        
        for i, mesa in enumerate(mesas):
            color_bg = '#28A745' if mesa[3] == 'libre' else '#DC3545'
            color_text = 'white'
            
            btn = tk.Button(
                self.frame_mesas,
                text=f"{mesa[1]}\n({mesa[2]} pers.)",
                font=('Arial', 11, 'bold'),
                bg=color_bg,
                fg=color_text,
                command=lambda m=mesa: self.seleccionar_mesa(m),
                width=10,
                height=2,
                cursor='hand2'
            )
            btn.grid(row=i//6, column=i%6, padx=2, pady=2)
    
    def seleccionar_mesa(self, mesa):
        """Selecciona una mesa para la comanda"""
        if mesa[3] == 'ocupada':
            if not messagebox.askyesno("Mesa Ocupada", f"La {mesa[1]} está ocupada. ¿Desea continuar?"):
                return
        
        self.mesa_actual = mesa
        self.label_mesa_actual.config(text=f"Mesa: {mesa[1]}")
        messagebox.showinfo("Mesa Seleccionada", f"Mesa seleccionada: {mesa[1]}")
    
    def cargar_categorias(self):
        """Carga los botones de categorías"""
        # Limpiar frame
        for widget in self.frame_categorias.winfo_children():
            widget.destroy()
        
        # Botón "Todas"
        tk.Button(
            self.frame_categorias,
            text="🍽️ Todas",
            font=('Arial', 12, 'bold'),
            bg='#6C757D',
            fg='white',
            command=lambda: self.filtrar_productos(None),
            width=12,
            height=2,
            cursor='hand2'
        ).pack(side='left', padx=2)
        
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
            
            tk.Button(
                self.frame_categorias,
                text=f"📂 {cat_nombre}",
                font=('Arial', 12, 'bold'),
                bg=color,
                fg='white',
                command=lambda c=cat_nombre: self.filtrar_productos(c),
                width=15,
                height=2,
                cursor='hand2'
            ).pack(side='left', padx=2)
    
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
        
        # Crear grid de productos (3 columnas)
        columnas = 3
        for i, producto in enumerate(productos):
            fila = i // columnas
            columna = i % columnas
            
            # Frame para cada producto
            frame_producto = tk.Frame(
                self.frame_productos_scroll,
                bg='white',
                relief='raised',
                bd=2
            )
            frame_producto.grid(row=fila, column=columna, padx=5, pady=5, sticky='ew')
            
            # Configurar peso de columnas
            self.frame_productos_scroll.columnconfigure(columna, weight=1)
            
            # Nombre del producto
            tk.Label(
                frame_producto,
                text=producto[1],
                font=('Arial', 14, 'bold'),
                bg='white',
                wraplength=200
            ).pack(pady=5)
            
            # Precio
            tk.Label(
                frame_producto,
                text=f"${producto[2]}",
                font=('Arial', 16, 'bold'),
                bg='white',
                fg='#DC3545'
            ).pack()
            
            # Descripción (si existe)
            if producto[5]:  # descripcion
                tk.Label(
                    frame_producto,
                    text=producto[5],
                    font=('Arial', 9),
                    bg='white',
                    fg='gray',
                    wraplength=180
                ).pack(pady=2)
            
            # Botón agregar (grande para táctil)
            tk.Button(
                frame_producto,
                text="➕ Agregar",
                font=('Arial', 12, 'bold'),
                bg='#28A745',
                fg='white',
                command=lambda p=producto: self.agregar_a_comanda(p),
                width=15,
                height=2,
                cursor='hand2'
            ).pack(pady=5, padx=5, fill='x')
    
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
        self.cargar_mesas()
        
        messagebox.showinfo("Éxito", f"Comanda {numero_comanda} enviada exitosamente\nTotal: ${total}")
    
    def generar_ticket_comanda(self, comanda_id, numero_comanda, total, observaciones):
        """Genera un ticket PDF de la comanda"""
        try:
            # Crear carpeta 'tickets' si no existe
            carpeta_tickets = "tickets"
            if not os.path.exists(carpeta_tickets):
                os.makedirs(carpeta_tickets)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 18)
            
            # Encabezado
            pdf.cell(0, 10, 'COMANDA DE COCINA', 0, 1, 'C')
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 8, '=' * 40, 0, 1, 'C')
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, f'Comanda N°: {numero_comanda}', 0, 1, 'L')
            pdf.cell(0, 8, f'Mesa: {self.mesa_actual[1]}', 0, 1, 'L')
            pdf.cell(0, 8, f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'L')
            pdf.cell(0, 8, f'Mesero: {self.usuario_actual["nombre"]}', 0, 1, 'L')
            pdf.ln(5)
            
            # Línea separadora
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 0, '=' * 60, 0, 1, 'C')
            pdf.ln(5)
            
            # Items
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 8, 'PEDIDO:', 0, 1, 'L')
            pdf.ln(2)
            
            pdf.set_font('Arial', '', 11)
            self.cursor.execute('''
                SELECT producto_nombre, cantidad, observaciones
                FROM items_comanda WHERE comanda_id = ?
            ''', (comanda_id,))
            
            items = self.cursor.fetchall()
            for item in items:
                # Cantidad y producto
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(20, 8, f'{item[1]}x', 0, 0, 'L')
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 8, item[0], 0, 1, 'L')
                
                # Observaciones del item si existen
                if item[2] and item[2].strip():
                    pdf.set_font('Arial', 'I', 9)
                    pdf.cell(20, 6, '', 0, 0)  # Sangría
                    pdf.cell(0, 6, f'Obs: {item[2]}', 0, 1, 'L')
                    pdf.ln(1)
                else:
                    pdf.ln(3)
            
            # Observaciones generales
            if observaciones and observaciones.strip():
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 8, 'OBSERVACIONES GENERALES:', 0, 1, 'L')
                pdf.set_font('Arial', '', 11)
                
                # Dividir observaciones en líneas
                obs_lines = observaciones.split('\n')
                for line in obs_lines:
                    if line.strip():
                        pdf.cell(0, 6, line.strip(), 0, 1, 'L')
            
            pdf.ln(10)
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 0, '=' * 60, 0, 1, 'C')
            pdf.ln(5)
            
            # Total (para referencia)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 8, f'TOTAL: ${total}', 0, 1, 'C')
            
            pdf.ln(5)
            pdf.set_font('Arial', 'I', 9)
            pdf.cell(0, 5, 'Ticket generado automáticamente', 0, 1, 'C')
            
            # Guardar en subcarpeta 'tickets'
            filename = os.path.join(carpeta_tickets, f'comanda_{numero_comanda}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
            pdf.output(filename)
            messagebox.showinfo("Ticket Generado", f"Ticket de comanda guardado como: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar ticket: {str(e)}")
    
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
        
        # Implementar gestión de mesas...
        tk.Label(
            frame_mesas,
            text="🚧 Gestión de Mesas - En desarrollo",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=50)
    
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
        
        # Implementar gestión de usuarios...
        tk.Label(
            frame_usuarios,
            text="🚧 Gestión de Usuarios - En desarrollo",
            font=('Arial', 16, 'bold'),
            bg='#F8F9FA'
        ).pack(pady=50)
    
    def logout(self):
        """Cierra sesión y vuelve al login"""
        if messagebox.askyesno("Cerrar Sesión", "¿Seguro que deseas cerrar sesión?"):
            self.conn.close()
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaComandas(root)
    root.mainloop()