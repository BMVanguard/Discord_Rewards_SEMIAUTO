#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import json
import threading
import subprocess
import winsound
from pathlib import Path
from tkinter import messagebox, simpledialog
import psutil
import customtkinter as ctk

# 1. Obtener la ruta de los recursos (.ttf, .ico, etc.) en script o .exe
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).resolve().parent / relative_path

# Cargar la fuente integrada
FONT_FILE = get_resource_path("PressStart2P-Regular.ttf")

if FONT_FILE.exists():
    try:
        ctk.FontManager.load_font(str(FONT_FILE))
        FONT_NAME = "Press Start 2P"
    except Exception:
        FONT_NAME = "Consolas"
else:
    FONT_NAME = "Consolas"

# Rutas de archivos de persistencia
SHORTCUTS_FILE = Path.home() / "discord_misiones_shortcuts.json"
CONFIG_FILE = Path.home() / "discord_misiones_config.json"

class QueueItem:
    def __init__(self, exe_name, duration_minutes=15, folder_name="Win64"):
        self.exe_name = exe_name
        self.duration = duration_minutes * 60
        self.folder_name = folder_name.strip() if folder_name.strip() else "Win64"
        self.status = "Pendiente"

    @property
    def folder_path(self):
        return Path.home() / "Desktop" / self.folder_name

class ConfigDashboard(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("⚙️ Configuración")
        self.geometry("450x380")
        self.resizable(False, False)
        
        # Transparencia en la ventana de config
        self.attributes("-alpha", 0.90)

        # Ícono para la ventana modal
        ICON_FILE = get_resource_path("icono.ico")
        if ICON_FILE.exists():
            self.after(10, lambda: self.iconbitmap(str(ICON_FILE)))

        # Modal
        self.transient(parent)
        self.grab_set()

        # Variables locales de la config
        self.theme_var = ctk.StringVar(value=parent.config_data.get("theme", "Dark"))
        self.font_size_var = ctk.StringVar(value=f"{parent.base_font_size}pt")
        self.sound_enabled_var = ctk.BooleanVar(value=parent.config_data.get("sound_enabled", True))
        self.default_folder_var = ctk.StringVar(value=parent.config_data.get("default_folder", "Win64"))

        self.build_ui()

    def build_ui(self):
        main_frame = ctk.CTkFrame(self, corner_radius=12, border_width=1, border_color="#333333")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            main_frame, text="⚙️ Ajustes del Sistema", 
            font=ctk.CTkFont(family=FONT_NAME, size=11, weight="bold"), 
            text_color=("#121212", "#00E676")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        cfg_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        cfg_grid.pack(fill="x", padx=15, pady=5)

        # Tema
        ctk.CTkLabel(cfg_grid, text="Tema visual:", font=self.parent.f_sub).grid(row=0, column=0, sticky="w", pady=8)
        theme_menu = ctk.CTkOptionMenu(
            cfg_grid, values=["Dark", "Light", "System"],
            variable=self.theme_var,
            font=self.parent.f_sub, dropdown_font=self.parent.f_sub, width=140, height=30
        )
        theme_menu.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # Tamaño de Fuente
        ctk.CTkLabel(cfg_grid, text="Tamaño fuente:", font=self.parent.f_sub).grid(row=1, column=0, sticky="w", pady=8)
        font_menu = ctk.CTkOptionMenu(
            cfg_grid, values=["7pt", "8pt", "9pt", "10pt", "11pt", "12pt"],
            variable=self.font_size_var,
            font=self.parent.f_sub, dropdown_font=self.parent.f_sub, width=140, height=30
        )
        font_menu.grid(row=1, column=1, sticky="e", padx=(10, 0))

        # Carpeta por defecto
        ctk.CTkLabel(cfg_grid, text="Carpeta default:", font=self.parent.f_sub).grid(row=2, column=0, sticky="w", pady=8)
        folder_entry = ctk.CTkEntry(
            cfg_grid, textvariable=self.default_folder_var, width=140, height=30,
            justify="center", font=self.parent.f_input
        )
        folder_entry.grid(row=2, column=1, sticky="e", padx=(10, 0))

        # Sonido
        sound_chk = ctk.CTkCheckBox(
            cfg_grid, text="Alertas sonoras", variable=self.sound_enabled_var,
            font=self.parent.f_sub, checkbox_width=20, checkbox_height=20
        )
        sound_chk.grid(row=3, column=0, columnspan=2, sticky="w", pady=10)

        # Botón Guardar y Reiniciar App
        btn_save = ctk.CTkButton(
            main_frame, text="💾 Guardar y Aplicar Cambios", height=38,
            fg_color="#00E676", hover_color="#00C853", text_color="#000000",
            font=self.parent.f_btn, corner_radius=8, command=self.save_and_restart
        )
        btn_save.pack(fill="x", padx=15, pady=(15, 10))

    def save_and_restart(self):
        nuevo_tema = self.theme_var.get()
        size = int(self.font_size_var.get().replace("pt", ""))
        data = {
            "theme": nuevo_tema,
            "font_size": size,
            "sound_enabled": self.sound_enabled_var.get(),
            "default_folder": self.default_folder_var.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")
            return

        # 1. Liberar el foco modal
        self.grab_release()
        self.destroy()

        # 2. Reiniciar detectando si es .exe o script .py
        if getattr(sys, 'frozen', False):
            # Si es ejecutable compilado (.exe)
            subprocess.Popen([sys.executable] + sys.argv[1:])
        else:
            # Si se ejecuta directo en Python
            subprocess.Popen([sys.executable, sys.argv[0]] + sys.argv[1:])

        # 3. Cerrar la ventana actual
        self.parent.destroy()
        sys.exit()

class DiscordMisionesV3(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Discord Misiones V3")
        self.geometry("960x950")

        # Transparencia ventana principal
        self.attributes("-alpha", 0.90)

        # Ícono ventana principal
        ICON_FILE = get_resource_path("icono.ico")
        if ICON_FILE.exists():
            self.iconbitmap(str(ICON_FILE))

        # Cargar configuración
        self.config_data = self.load_config()
        
        # Aplicar tema inicial
        ctk.set_appearance_mode(self.config_data.get("theme", "Dark"))
        ctk.set_default_color_theme("green")

        # Variables de control
        self.base_font_size = self.config_data.get("font_size", 9)
        self.update_font_objects(self.base_font_size)

        # Variables de estado
        self.queue = []
        self.current_index = -1
        self.running = False
        self.current_process = None
        self.custom_shortcuts = self.load_shortcuts()

        self.exe_input_var = ctk.StringVar()
        self.time_input_var = ctk.StringVar(value="15")
        self.folder_input_var = ctk.StringVar(value=self.config_data.get("default_folder", "Win64"))

        # Contenedor principal
        self.main_scroll = ctk.CTkScrollableFrame(
            self, 
            scrollbar_button_color="#2D2D2D", 
            scrollbar_button_hover_color="#00E676",
            corner_radius=0
        )
        self.build_ui()

        # Pantalla de carga
        self.show_splash()

    def update_font_objects(self, size):
        self.f_title = ctk.CTkFont(family=FONT_NAME, size=size + 4, weight="bold")
        self.f_sub = ctk.CTkFont(family=FONT_NAME, size=size)
        self.f_btn = ctk.CTkFont(family=FONT_NAME, size=size, weight="bold")
        self.f_input = ctk.CTkFont(family=FONT_NAME, size=size + 1)

    def load_config(self):
        defaults = {
            "theme": "Dark",
            "font_size": 9,
            "sound_enabled": True,
            "default_folder": "Win64"
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
            except Exception:
                pass
        return defaults

    def show_splash(self):
        self.splash_frame = ctk.CTkFrame(self, corner_radius=0)
        self.splash_frame.pack(fill="both", expand=True)

        center_card = ctk.CTkFrame(
            self.splash_frame, 
            width=480, 
            height=230, 
            corner_radius=12, 
            border_width=1, 
            border_color="#333333"
        )
        center_card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            center_card, text="Discord Misiones V3",
            font=self.f_title,
            text_color="#00E676"
        ).pack(pady=(35, 10))

        self.splash_status = ctk.CTkLabel(
            center_card, text="Cargando componentes...",
            font=self.f_sub,
            text_color=("#444444", "#888888")
        )
        self.splash_status.pack(pady=5)

        self.splash_progress = ctk.CTkProgressBar(
            center_card, 
            progress_color="#00E676", 
            height=10, 
            corner_radius=5, 
            width=320
        )
        self.splash_progress.pack(pady=15)
        self.splash_progress.set(0)

        threading.Thread(target=self.animate_splash, daemon=True).start()

    def animate_splash(self):
        for i in range(1, 101):
            time.sleep(0.012)
            self.after(0, self.splash_progress.set, i / 100)
            if i == 30:
                self.after(0, self.splash_status.configure, {"text": "Cargando atajos y configuración..."})
            elif i == 70:
                self.after(0, self.splash_status.configure, {"text": "Iniciando interfaz..."})

        self.after(0, self.finish_splash)

    def finish_splash(self):
        self.splash_frame.pack_forget()
        self.splash_frame.destroy()
        self.main_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self.log("🚀 Discord Misiones V3 iniciado")

    def load_shortcuts(self):
        if SHORTCUTS_FILE.exists():
            try:
                with open(SHORTCUTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_shortcuts(self):
        try:
            with open(SHORTCUTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.custom_shortcuts, f, indent=4)
        except Exception as e:
            self.log(f"❌ Error al guardar atajos: {e}")

    def open_config(self):
        ConfigDashboard(self)

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title_lbl = ctk.CTkLabel(
            header, text="Discord Misiones V3", 
            font=self.f_title,
            text_color=("#1A1A1A", "#E0E0E0")
        )
        title_lbl.pack(side="left", padx=(0, 5))

        green_dot = ctk.CTkLabel(header, text="●", font=ctk.CTkFont(size=16), text_color="#00E676")
        green_dot.pack(side="left", padx=5)

        sub_lbl = ctk.CTkLabel(
            header, text="Ejecuta tus juegos en secuencia", 
            font=self.f_sub, 
            text_color=("#555555", "#888888")
        )
        sub_lbl.pack(side="left", padx=10)

        # Botón Engranaje
        btn_gear = ctk.CTkButton(
            header, text="⚙️", width=36, height=36, 
            fg_color="transparent", hover_color=("#E0E0E0", "#222222"),
            font=ctk.CTkFont(size=16), command=self.open_config
        )
        btn_gear.pack(side="right", padx=5)

        # 1. Agregar Juego
        add_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12, border_width=1, border_color="#333333")
        add_frame.pack(fill="x", pady=6, ipady=5)

        ctk.CTkLabel(
            add_frame, text="➕ Agregar juego a la cola", 
            font=ctk.CTkFont(family=FONT_NAME, size=10, weight="bold"), 
            text_color=("#00A859", "#00E676")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        input_grid = ctk.CTkFrame(add_frame, fg_color="transparent")
        input_grid.pack(fill="x", padx=15, pady=5)

        # Nombre EXE
        ctk.CTkLabel(input_grid, text="Nombre .exe:", font=self.f_sub, text_color=("#1A1A1A", "#E0E0E0")).grid(row=0, column=0, sticky="w", pady=6)
        ctk.CTkEntry(
            input_grid, textvariable=self.exe_input_var, width=240, height=34,
            placeholder_text="Ej: Endfield.exe", justify="center",
            corner_radius=8, font=self.f_input, text_color=("#1A1A1A", "#E0E0E0")
        ).grid(row=0, column=1, sticky="w", padx=10)

        # Duración
        ctk.CTkLabel(input_grid, text="Duración (min):", font=self.f_sub, text_color=("#1A1A1A", "#E0E0E0")).grid(row=1, column=0, sticky="w", pady=6)
        time_box = ctk.CTkFrame(input_grid, fg_color="transparent")
        time_box.grid(row=1, column=1, sticky="w", padx=10)

        ctk.CTkEntry(
            time_box, textvariable=self.time_input_var, width=70, height=34,
            justify="center", corner_radius=8, font=self.f_input, text_color=("#1A1A1A", "#E0E0E0")
        ).pack(side="left", padx=(0, 5))

        time_options = [
            ("5m", 6),
            ("10m", 11),
            ("15m", 16),
            ("30m", 31),
            ("60m", 61)
        ]

        for label_text, real_mins in time_options:
            ctk.CTkButton(
                time_box, text=label_text, width=42, height=34, fg_color="#00E676", text_color="#000000",
                hover_color="#00C853", corner_radius=6, font=self.f_btn,
                command=lambda m=real_mins: self.time_input_var.set(str(m))
            ).pack(side="left", padx=2)

        # Carpeta
        ctk.CTkLabel(input_grid, text="Carpeta:", font=self.f_sub, text_color=("#1A1A1A", "#E0E0E0")).grid(row=2, column=0, sticky="w", pady=6)
        ctk.CTkEntry(
            input_grid, textvariable=self.folder_input_var, width=240, height=34,
            justify="center", corner_radius=8, font=self.f_input, text_color=("#1A1A1A", "#E0E0E0")
        ).grid(row=2, column=1, sticky="w", padx=10)

        # Botones de agregar
        btn_add_box = ctk.CTkFrame(add_frame, fg_color="transparent")
        btn_add_box.pack(anchor="w", padx=15, pady=(10, 10))

        ctk.CTkButton(
            btn_add_box, text="➕ Agregar a la cola", height=36, fg_color="#00E676", hover_color="#00C853",
            text_color="#000000", font=self.f_btn, corner_radius=8, command=self.add_to_queue
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            btn_add_box, text="⭐ Guardar atajo", height=36, fg_color="#00E676", hover_color="#00C853",
            text_color="#000000", font=self.f_btn, corner_radius=8, command=self.add_custom_shortcut
        ).pack(side="left")

        # 2. Mis Atajos
        shortcuts_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12, border_width=1, border_color="#333333")
        shortcuts_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            shortcuts_frame, text="⭐ Mis atajos", 
            font=ctk.CTkFont(family=FONT_NAME, size=10, weight="bold"), 
            text_color=("#00A859", "#00E676")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.shortcuts_container = ctk.CTkScrollableFrame(
            shortcuts_frame, fg_color="transparent", height=45, orientation="horizontal",
            scrollbar_button_color="#2D2D2D", scrollbar_button_hover_color="#00E676"
        )
        self.shortcuts_container.pack(fill="x", padx=10, pady=(0, 10))
        self.render_shortcuts()

        # 3. Cola de Juegos
        queue_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12, border_width=1, border_color="#333333")
        queue_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            queue_frame, text="📋 Cola de juegos", 
            font=ctk.CTkFont(family=FONT_NAME, size=10, weight="bold"), 
            text_color=("#00A859", "#00E676")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.queue_scroll = ctk.CTkScrollableFrame(
            queue_frame, height=180, corner_radius=8,
            scrollbar_button_color="#2D2D2D", scrollbar_button_hover_color="#00E676"
        )
        self.queue_scroll.pack(fill="x", padx=15, pady=5)

        q_btns = ctk.CTkFrame(queue_frame, fg_color="transparent")
        q_btns.pack(fill="x", padx=15, pady=(5, 10))

        self.start_btn = ctk.CTkButton(
            q_btns, text="▶️ Iniciar cola", height=36, fg_color="#00E676", hover_color="#00C853", 
            text_color="#000000", font=self.f_btn, 
            corner_radius=8, command=self.start_queue
        )
        self.start_btn.pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            q_btns, text="🗑️ Eliminar", height=36, fg_color="#00E676", hover_color="#00C853", 
            text_color="#000000", font=self.f_btn, 
            corner_radius=8, command=self.remove_selected
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            q_btns, text="🧹 Limpiar", height=36, fg_color="#00E676", hover_color="#00C853", 
            text_color="#000000", font=self.f_btn, 
            corner_radius=8, command=self.clear_queue
        ).pack(side="left", padx=3)

        # 4. Control de Ejecución
        control_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12, border_width=1, border_color="#333333")
        control_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            control_frame, text="▶️ Control de ejecución", 
            font=ctk.CTkFont(family=FONT_NAME, size=10, weight="bold"), 
            text_color=("#00A859", "#00E676")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.current_games_scroll = ctk.CTkScrollableFrame(
            control_frame, height=90, corner_radius=8,
            scrollbar_button_color="#2D2D2D", scrollbar_button_hover_color="#00E676"
        )
        self.current_games_scroll.pack(fill="x", padx=15, pady=5)

        self.current_game_label = ctk.CTkLabel(
            self.current_games_scroll, text="Juego actual: Ninguno", 
            font=ctk.CTkFont(family=FONT_NAME, size=9, weight="bold"),
            text_color=("#1A1A1A", "#E0E0E0")
        )
        self.current_game_label.pack(anchor="w", padx=5, pady=2)

        self.current_folder_label = ctk.CTkLabel(
            self.current_games_scroll, text="Carpeta: --", 
            font=self.f_sub, text_color=("#555555", "#888888")
        )
        self.current_folder_label.pack(anchor="w", padx=5, pady=2)

        self.next_game_label = ctk.CTkLabel(
            self.current_games_scroll, text="Siguiente: --", 
            font=self.f_sub, text_color=("#555555", "#888888")
        )
        self.next_game_label.pack(anchor="w", padx=5, pady=2)

        self.progress = ctk.CTkProgressBar(control_frame, progress_color="#00E676", height=12, corner_radius=6)
        self.progress.pack(fill="x", padx=15, pady=8)
        self.progress.set(0)

        self.time_label = ctk.CTkLabel(
            control_frame, text="Esperando...", 
            font=ctk.CTkFont(family=FONT_NAME, size=9, weight="bold"), 
            text_color=("#00A859", "#00E676")
        )
        self.time_label.pack(pady=2)

        ctrl_btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        ctrl_btn_frame.pack(pady=(5, 10))

        ctk.CTkButton(
            ctrl_btn_frame, text="⏹️ Detener todo", height=36, fg_color="#00E676", hover_color="#00C853", 
            text_color="#000000", font=self.f_btn, 
            corner_radius=8, command=self.stop_queue
        ).pack(side="left", padx=5)

        # 5. Log de Eventos
        log_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12, border_width=1, border_color="#333333")
        log_frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            log_frame, text="📝 Log de eventos", 
            font=ctk.CTkFont(family=FONT_NAME, size=10, weight="bold"), 
            text_color=("#00A859", "#00E676")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.log_text = ctk.CTkTextbox(
            log_frame, height=100, text_color=("#007934", "#00E676"),
            corner_radius=8, scrollbar_button_color="#2D2D2D", scrollbar_button_hover_color="#00E676", 
            font=self.f_sub
        )
        self.log_text.pack(fill="x", padx=15, pady=(0, 10))
        self.log_text.configure(state="disabled")

    def render_shortcuts(self):
        for widget in self.shortcuts_container.winfo_children():
            widget.destroy()

        if not self.custom_shortcuts:
            ctk.CTkLabel(self.shortcuts_container, text="No hay atajos guardados.", font=self.f_sub, text_color=("#555555", "#888888")).pack(anchor="w", pady=5)
            return

        for name, data in self.custom_shortcuts.items():
            btn_box = ctk.CTkFrame(self.shortcuts_container, corner_radius=6)
            btn_box.pack(side="left", padx=4, pady=2)

            btn = ctk.CTkButton(
                btn_box, text=f"🎮 {name}", fg_color="transparent", text_color=("#1A1A1A", "#E0E0E0"),
                hover_color=("#D0D0D0", "#333333"), font=self.f_sub,
                command=lambda d=data: self.use_shortcut(d)
            )
            btn.pack(side="left", padx=(2, 0))

            del_btn = ctk.CTkButton(
                btn_box, text="✕", width=20, fg_color="transparent", text_color=("#555555", "#888888"),
                hover_color=("#C0C0C0", "#444444"), font=self.f_sub, 
                command=lambda n=name: self.delete_shortcut(n)
            )
            del_btn.pack(side="left", padx=2)

    def render_queue_list(self):
        for widget in self.queue_scroll.winfo_children():
            widget.destroy()

        if not self.queue:
            ctk.CTkLabel(self.queue_scroll, text="La cola está vacía.", font=self.f_sub, text_color=("#555555", "#888888")).pack(pady=10)
            return

        for i, item in enumerate(self.queue):
            mins = item.duration // 60
            row = ctk.CTkFrame(self.queue_scroll, corner_radius=6)
            row.pack(fill="x", pady=2, padx=2)

            txt = f"#{i+1} | {item.exe_name} | Folder: {item.folder_name} | {mins}m | {item.status}"
            lbl = ctk.CTkLabel(row, text=txt, font=self.f_sub, text_color=("#1A1A1A", "#E0E0E0"))
            lbl.pack(side="left", padx=10, pady=4)

    def add_custom_shortcut(self):
        exe = self.exe_input_var.get().strip()
        time_str = self.time_input_var.get().strip()
        folder = self.folder_input_var.get().strip()

        if not exe:
            messagebox.showwarning("Atención", "Ingresa al menos el nombre del ejecutable.")
            return

        if not time_str.isdigit() or int(time_str) <= 0:
            messagebox.showwarning("Atención", "Tiempo inválido.")
            return

        if not exe.endswith('.exe'):
            exe += '.exe'

        if not folder:
            folder = self.config_data.get("default_folder", "Win64")

        shortcut_name = simpledialog.askstring("Nuevo atajo", "Nombre para este atajo:", parent=self)
        if shortcut_name:
            shortcut_name = shortcut_name.strip()
            if not shortcut_name:
                return

            self.custom_shortcuts[shortcut_name] = {"exe": exe, "time": time_str, "folder": folder}
            self.save_shortcuts()
            self.render_shortcuts()
            self.log(f"⭐ Atajo creado: {shortcut_name} ({exe})")

    def use_shortcut(self, data):
        self.exe_input_var.set(data["exe"])
        self.time_input_var.set(data["time"])
        self.folder_input_var.set(data["folder"])
        self.add_to_queue()

    def delete_shortcut(self, name):
        if messagebox.askyesno("Eliminar atajo", f"¿Seguro que deseas eliminar '{name}'?"):
            if name in self.custom_shortcuts:
                del self.custom_shortcuts[name]
                self.save_shortcuts()
                self.render_shortcuts()
                self.log(f"🗑️ Atajo eliminado: {name}")

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def add_to_queue(self):
        exe = self.exe_input_var.get().strip()
        time_str = self.time_input_var.get().strip()
        folder = self.folder_input_var.get().strip()

        if not exe:
            messagebox.showwarning("Atención", "Ingresa un nombre de ejecutable")
            return

        if not time_str.isdigit() or int(time_str) <= 0:
            messagebox.showwarning("Atención", "Tiempo inválido")
            return

        if not exe.endswith('.exe'):
            exe += '.exe'

        if not folder:
            folder = self.config_data.get("default_folder", "Win64")

        item = QueueItem(exe, int(time_str), folder)
        self.queue.append(item)

        self.render_queue_list()
        self.log(f"➕ Agregado: {exe} ({time_str} min)")

        self.exe_input_var.set("")
        self.folder_input_var.set(self.config_data.get("default_folder", "Win64"))

    def remove_selected(self):
        if self.queue:
            removed = self.queue.pop()
            self.log(f"🗑️ Eliminado: {removed.exe_name}")
            self.render_queue_list()

    def clear_queue(self):
        if not self.queue:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar todos los juegos de la cola?"):
            self.queue.clear()
            self.log("🧹 Cola limpiada")
            self.render_queue_list()

    def find_wordpad(self):
        paths = [
            r"C:\Program Files\Windows NT\Accessories\wordpad.exe",
            r"C:\Windows\System32\write.exe",
            r"C:\Windows\notepad.exe",
        ]
        for p in paths:
            if os.path.exists(p):
                return p
        return None

    def create_game_exe(self, item):
        target_folder = item.folder_path
        target_folder.mkdir(parents=True, exist_ok=True)

        for old_exe in target_folder.glob("*.exe"):
            try:
                for proc in psutil.process_iter(['pid', 'exe']):
                    if str(old_exe).lower() in str(proc.info.get('exe', '')).lower():
                        proc.terminate()
                old_exe.unlink()
            except Exception:
                pass

        wordpad = self.find_wordpad()
        if not wordpad:
            self.log("❌ WordPad no encontrado")
            return None

        destino = target_folder / item.exe_name
        try:
            shutil.copy2(wordpad, destino)
            return str(destino)
        except Exception as e:
            self.log(f"❌ Error creando {item.exe_name}: {e}")
            return None

    def start_queue(self):
        if self.running:
            return
        if not self.queue:
            messagebox.showwarning("Atención", "La cola está vacía.")
            return

        self.running = True
        self.start_btn.configure(state="disabled")
        self.log("🚀 Iniciando cola de juegos")
        threading.Thread(target=self.process_queue, daemon=True).start()

    def process_queue(self):
        for i, item in enumerate(self.queue):
            if not self.running:
                break

            self.current_index = i
            item.status = "Ejecutando"
            self.after(0, self.render_queue_list)
            self.after(0, self.update_current_game, item)

            exe_path = self.create_game_exe(item)
            if not exe_path:
                item.status = "Error"
                continue

            try:
                self.log(f"▶️ Iniciando: {item.exe_name}")
                self.current_process = subprocess.Popen([exe_path], cwd=str(item.folder_path))

                start_time = time.time()
                while self.running:
                    elapsed = time.time() - start_time
                    remaining = item.duration - elapsed

                    if remaining <= 0:
                        break

                    progress_val = (elapsed / item.duration)
                    mins, secs = divmod(int(remaining), 60)
                    time_str = f"{mins:02d}:{secs:02d}"

                    self.after(0, self.update_progress, progress_val, time_str)
                    time.sleep(0.5)

                if self.current_process:
                    self.current_process.terminate()
                    self.current_process = None

                item.status = "Completado"
                self.log(f"✅ Completado: {item.exe_name}")

            except Exception as e:
                self.log(f"❌ Error con {item.exe_name}: {e}")
                item.status = "Error"

        self.running = False
        self.after(0, self.queue_finished)

    def update_current_game(self, item):
        self.current_game_label.configure(text=f"Juego actual: {item.exe_name}")
        self.current_folder_label.configure(text=f"Carpeta: Desktop/{item.folder_name}")
        if self.current_index + 1 < len(self.queue):
            self.next_game_label.configure(text=f"Siguiente: {self.queue[self.current_index + 1].exe_name}")
        else:
            self.next_game_label.configure(text="Siguiente: --")

    def update_progress(self, progress_val, time_str):
        self.progress.set(progress_val)
        self.time_label.configure(text=f"Tiempo restante: {time_str}")

    def stop_queue(self):
        if not self.running:
            return
        if messagebox.askyesno("Confirmar", "¿Detener la ejecución?"):
            self.running = False
            if self.current_process:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
            self.log("⏹️ Proceso detenido")
            self.start_btn.configure(state="normal")

    def queue_finished(self):
        self.current_game_label.configure(text="Juego actual: Ninguno")
        self.current_folder_label.configure(text="Carpeta: --")
        self.progress.set(0)
        self.time_label.configure(text="Proceso finalizado")
        self.start_btn.configure(state="normal")
        self.render_queue_list()
        
        if self.config_data.get("sound_enabled", True):
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
                
        messagebox.showinfo("¡Éxito!", "¡El proceso ha finalizado!")

if __name__ == "__main__":
    app = DiscordMisionesV3()
    app.mainloop()