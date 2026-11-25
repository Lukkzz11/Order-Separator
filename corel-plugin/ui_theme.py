import sys
import os
import ctypes
from ctypes import wintypes
import customtkinter as ctk

# Configure CustomTkinter defaults
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Order Separator Design System Color Palette (Dark Zinc / Slate)
BG_CANVAS = "#0B0D11"       # Fundo principal da janela
BG_CARD = "#13151B"         # Superfície dos cards
BG_CONTAINER = "#181B22"    # Caixas internas, inputs e fundos de preview
BG_HOVER = "#27272A"        # Estado hover de botões secundários
BORDER = "#27272A"          # Bordas sutis de 1px
BORDER_FOCUS = "#3F3F46"    # Borda em foco

TEXT_MAIN = "#F4F4F5"       # Texto primário / títulos
TEXT_MUTED = "#A1A1AA"      # Texto secundário / legendas
TEXT_DIM = "#71717A"        # Texto terciário / placeholders

# Cores de Ação / Identidade dos Apps (Idênticos ao Sidebar do Order Separator)
EMERALD = "#10B981"         # Removedor IA (Fundo)
EMERALD_HOVER = "#059669"
SKY = "#38BDF8"             # Upscaler IA (4x/8x)
SKY_HOVER = "#0284C7"
INDIGO = "#818CF8"          # Vetorizador IA (Vetor)
INDIGO_HOVER = "#6366F1"
AMBER = "#F59E0B"           # Montador de Folha / Bobina
AMBER_HOVER = "#D97706"
PURPLE = "#A855F7"          # Pedidos & Contexto

def apply_dark_titlebar(window):
    """Aplica o tema escuro nativo do Windows 10/11 na barra de título da janela."""
    try:
        window.update_idletasks()
        hwnd = window.winfo_id()
        hwnd_top = ctypes.windll.user32.GetAncestor(hwnd, 2)
        if not hwnd_top:
            hwnd_top = hwnd
        val = ctypes.c_int(1)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE (Windows 11 e Windows 10 build 19041+)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd_top, 20, ctypes.byref(val), ctypes.sizeof(val))
        # 19 = fallback para builds anteriores do Windows 10
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd_top, 19, ctypes.byref(val), ctypes.sizeof(val))
    except Exception:
        pass

def create_header(parent, title_text, subtitle_text, accent_color, badge_text="OS"):
    """Cria o cabeçalho moderno no padrão Order Separator com badge pill e tipografia limpa."""
    hdr = ctk.CTkFrame(parent, fg_color="transparent")
    hdr.pack(fill="x", padx=18, pady=(14, 10))
    
    title_box = ctk.CTkFrame(hdr, fg_color="transparent")
    title_box.pack(side="left")
    
    top_row = ctk.CTkFrame(title_box, fg_color="transparent")
    top_row.pack(anchor="w")
    
    badge = ctk.CTkLabel(
        top_row,
        text=badge_text,
        font=("Segoe UI", 10, "bold"),
        fg_color=BG_CONTAINER,
        text_color=accent_color,
        corner_radius=6,
        width=28,
        height=22
    )
    badge.pack(side="left", padx=(0, 8))
    
    lbl_title = ctk.CTkLabel(
        top_row,
        text=title_text,
        font=("Segoe UI", 16, "bold"),
        text_color=TEXT_MAIN
    )
    lbl_title.pack(side="left")
    
    lbl_sub = ctk.CTkLabel(
        title_box,
        text=subtitle_text,
        font=("Segoe UI", 10),
        text_color=TEXT_MUTED
    )
    lbl_sub.pack(anchor="w", pady=(2, 0))
    
    actions_box = ctk.CTkFrame(hdr, fg_color="transparent")
    actions_box.pack(side="right")
    
    return hdr, actions_box
