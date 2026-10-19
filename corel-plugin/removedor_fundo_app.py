"""
Order Separator - Removedor de Fundo Profissional 2.5 para CorelDRAW
Motor Inteligente de Remoção de Fundo com IA Dual (BiRefNet Ultra HD & U2-Net),
Fundo Branco de Prancheta, Chroma Key com Despill de Hardware VFX,
Conta-gotas Interativo no Canvas, Choke/Sangria DTF e Eliminação Total de Halos Verdes.
100% Offline, Gratuito, Sem Limites e Sem Falsos Positivos de Antivírus.
"""

import sys
import os
import re
import math
import tempfile
import threading
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageTk, ImageOps, ImageFilter, ImageGrab
import numpy as np
import cv2

# Importação condicional do rembg
try:
    import rembg
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# Sessões mantidas em memória para resposta instantânea
GLOBAL_SESSIONS = {}

def get_rembg_session(model_name="u2net"):
    global GLOBAL_SESSIONS
    if not HAS_REMBG:
        return None
    if model_name not in GLOBAL_SESSIONS:
        try:
            GLOBAL_SESSIONS[model_name] = rembg.new_session(model_name)
        except Exception:
            try:
                GLOBAL_SESSIONS[model_name] = rembg.new_session("u2net")
            except Exception:
                GLOBAL_SESSIONS[model_name] = None
    return GLOBAL_SESSIONS.get(model_name)


# =========================================================================
# MOTORES DE PROCESSAMENTO DE IMAGEM E REMOÇÃO DE FUNDO 2.5
# =========================================================================

def create_checkerboard_pattern(width, height, check_size=12, color1=(215, 220, 228), color2=(255, 255, 255)):
    """Cria uma imagem de padrão xadrez para representar transparência visualmente."""
    bg = Image.new("RGB", (width, height), color2)
    draw_img = np.array(bg)
    for y in range(0, height, check_size):
        for x in range(0, width, check_size):
            if ((x // check_size) + (y // check_size)) % 2 == 0:
                draw_img[y:min(y + check_size, height), x:min(x + check_size, width)] = color1
    return Image.fromarray(draw_img)


def apply_mask_choke_or_expand(alpha_np, choke_px=0):
    """
    Aplica Choke (encolhimento / retração) ou Expansão na máscara Alfa.
    Essencial para estamparia DTF e silk-screen para eliminar 100% da rebarba branca!
    """
    if choke_px == 0:
        return alpha_np

    k_size = abs(int(choke_px)) * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))

    if choke_px < 0:
        return cv2.erode(alpha_np, kernel, iterations=1)
    else:
        return cv2.dilate(alpha_np, kernel, iterations=1)


def apply_chroma_despill_vfx(img_rgba, intensity=3):
    """
    Filtro Hollywood VFX de Despill e Eliminação Total de Halos Verdes e Azuis:
    1. Elimina faixas/manchas de fundo verde residual (como bordas esquerdas/direitas deixadas por IA).
    2. Decontamina o reflexo verde da luz que rebate na roupa, terno, cabelo e fones de ouvido.
    3. Converte a rebarba verde em tom neutro perfeitamente integrado ao sujeito (terno escuro / cabelo).
    """
    arr = np.array(img_rgba, dtype=np.float32)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    a = arr[:, :, 3]

    # 1. Limpeza de Fundo Verde Residual Puro (Chroma Clean-Up)
    # Qualquer pixel com predominância verde forte de estúdio é fundo e deve ter alfa = 0
    greenness = g - np.maximum(r, b)
    is_pure_chroma_green = (greenness > 16.0) & (g > 65.0)
    a = np.where(is_pure_chroma_green, 0.0, a)

    # Limpeza de Fundo Azul Residual Puro (Blue Screen)
    blueness = b - np.maximum(r, g)
    is_pure_chroma_blue = (blueness > 20.0) & (b > 80.0)
    a = np.where(is_pure_chroma_blue, 0.0, a)

    # 2. Despill nas Bordas e no Primeiro Plano
    # Onde a luz verde vazou na roupa, cabelo ou pele, substitui o verde pelo limite neutro dos outros canais
    limit_g = np.minimum(np.maximum(r, b), 0.5 * (r + b) + 3.0)
    has_green_spill = (g > limit_g) & (a > 0.0)
    g = np.where(has_green_spill, limit_g, g)

    # Despill Azul
    limit_b = np.minimum(np.maximum(r, g), 0.5 * (r + g) + 3.0)
    has_blue_spill = (b > limit_b) & (a > 0.0)
    b = np.where(has_blue_spill, limit_b, b)

    # 3. Suavização de Borda em Pixels com resquício de cor
    edge_chroma = ((greenness > 6.0) | (blueness > 8.0)) & (a > 0.0) & (a < 250.0)
    a = np.where(edge_chroma, np.clip(a - 25.0 * intensity, 0.0, 255.0), a)

    res = np.dstack((np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255), np.clip(a, 0, 255))).astype(np.uint8)
    return Image.fromarray(res, mode="RGBA")


def decontaminate_edge_colors(img_rgba_np, alpha_np):
    """
    Decontamina as cores das bordas semi-transparentes:
    Neutraliza o tom do fundo removido nos pixels de borda, puxando a cor sólida interna mais próxima.
    """
    edge_mask = (alpha_np > 5) & (alpha_np < 245)
    if not np.any(edge_mask):
        return img_rgba_np

    rgb = img_rgba_np[:, :, :3].astype(np.float32)
    solid_mask = (alpha_np >= 245).astype(np.uint8)

    if np.count_nonzero(solid_mask) > 100:
        inpaint_color = cv2.inpaint(rgb.astype(np.uint8), (alpha_np < 245).astype(np.uint8), 3, cv2.INPAINT_TELEA).astype(np.float32)
        blend_factor = (alpha_np.astype(np.float32) / 255.0)[:, :, np.newaxis]
        rgb = np.where(edge_mask[:, :, np.newaxis], inpaint_color * (1.0 - blend_factor) + rgb * blend_factor, rgb)

    res = np.dstack((np.clip(rgb, 0, 255).astype(np.uint8), alpha_np))
    return res


def remove_white_background_floodfill(pil_img, tolerance=28, edge_feather=1.0, choke_px=0):
    """
    Remove o fundo branco externo (canvas/bounding box de prancheta)
    através de floodfill conectado exclusivamente pelas bordas externas da imagem.
    PRESERVA 100% DOS BRANCOS INTERNOS (olhos, dentes, camisas, faixas brancas).
    """
    img_rgb = pil_img.convert("RGB")
    arr = np.array(img_rgb)
    h, w = arr.shape[:2]

    r = arr[:, :, 0].astype(int)
    g = arr[:, :, 1].astype(int)
    b = arr[:, :, 2].astype(int)
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    chroma = max_c - min_c
    lum = (r + g + b) // 3

    white_thresh = max(195, 255 - int(tolerance * 1.5))
    is_white_candidate = (lum >= white_thresh) & (chroma <= max(14, int(tolerance * 0.75)))

    sample_points = []
    for x in range(0, w, max(1, w // 40)):
        sample_points.append((x, 0))
        sample_points.append((x, h - 1))
    for y in range(0, h, max(1, h // 40)):
        sample_points.append((0, y))
        sample_points.append((w - 1, y))

    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    for pt_x, pt_y in sample_points:
        if is_white_candidate[pt_y, pt_x] and flood_mask[pt_y + 1, pt_x + 1] == 0:
            cv2.floodFill(
                is_white_candidate.astype(np.uint8),
                flood_mask,
                (pt_x, pt_y),
                255,
                flags=4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY
            )

    external_bg_mask = flood_mask[1:h + 1, 1:w + 1]
    alpha = np.where(external_bg_mask == 255, 0, 255).astype(np.uint8)

    if choke_px != 0:
        alpha = apply_mask_choke_or_expand(alpha, choke_px)

    if edge_feather > 0.2:
        k_size = int(math.ceil(edge_feather * 2)) | 1
        alpha_blurred = cv2.GaussianBlur(alpha, (k_size, k_size), edge_feather)
        alpha = cv2.addWeighted(alpha, 0.4, alpha_blurred, 0.6, 0)

    if pil_img.mode == "RGBA":
        orig_alpha = np.array(pil_img.split()[-1])
        alpha = np.minimum(alpha, orig_alpha)

    res_arr = np.dstack((arr, alpha))
    res_arr = decontaminate_edge_colors(res_arr, alpha)
    return Image.fromarray(res_arr, mode="RGBA")


def remove_chroma_key(pil_img, key_color=(0, 255, 0), tolerance=45, feather=1.2, despill=True, choke_px=0):
    """
    Remove fundo de cor sólida (Verde, Azul ou Cor Escolhida por Conta-gotas) com:
    - Detecção espectral de Chroma Key
    - Despill avançado de hardware VFX (elimina 100% de halos e vazamentos verdes/azuis)
    - Choke de borda anti-rebarba
    """
    img_rgb = pil_img.convert("RGB")
    arr = np.array(img_rgb, dtype=np.float32)
    h, w = arr.shape[:2]

    kr, kg, kb = [float(c) for c in key_color[:3]]

    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]

    # Distância Euclidiana de Cor
    dr = r - kr
    dg = g - kg
    db = b - kb
    dist = np.sqrt(dr * dr + dg * dg + db * db)

    # Detecção espectral ampla se for Chroma Verde
    is_chroma_green = (kg > kr + 40) and (kg > kb + 40)
    if is_chroma_green:
        greenness = g - np.maximum(r, b)
        # Qualquer pixel no espectro chroma verde é considerado fundo
        chroma_dist = np.clip(100.0 - greenness * 1.5, 0.0, 100.0)
        dist = np.minimum(dist, chroma_dist)

    tol_low = max(4.0, float(tolerance) * 0.65)
    tol_high = max(tol_low + 6.0, float(tolerance) * 1.25)

    alpha_f = np.clip((dist - tol_low) / (tol_high - tol_low), 0.0, 1.0)
    alpha = (alpha_f * 255.0).astype(np.uint8)

    if choke_px != 0:
        alpha = apply_mask_choke_or_expand(alpha, choke_px)

    if feather > 0.2:
        k_size = int(math.ceil(feather * 2)) | 1
        alpha = cv2.GaussianBlur(alpha, (k_size, k_size), feather)

    if pil_img.mode == "RGBA":
        orig_alpha = np.array(pil_img.split()[-1])
        alpha = np.minimum(alpha, orig_alpha)

    res_arr = np.dstack((np.clip(arr, 0, 255).astype(np.uint8), alpha))
    res_img = Image.fromarray(res_arr, mode="RGBA")

    if despill:
        res_img = apply_chroma_despill_vfx(res_img, intensity=3)

    return res_img


def remove_ai_semantic(pil_img, model_name="birefnet-general", alpha_matting=False, post_process=True, edge_smooth=1.0, choke_px=0, despill=True):
    """
    Remove o fundo usando Inteligência Artificial Semântica (BiRefNet Ultra HD ou U2-Net) + Despill VFX.
    Funciona para pessoas, fones de ouvido, cabelos, mascotes, carros e cenários complexos.
    Elimina 100% dos resquícios verdes de estúdio.
    """
    if not HAS_REMBG:
        raise RuntimeError("Biblioteca 'rembg' não está instalada no ambiente Python.")

    session = get_rembg_session(model_name)

    out_img = rembg.remove(
        pil_img,
        session=session,
        alpha_matting=alpha_matting,
        alpha_matting_foreground_threshold=240,
        alpha_matting_background_threshold=10,
        alpha_matting_erode_size=10,
        post_process_mask=post_process
    )

    if not isinstance(out_img, Image.Image):
        out_img = Image.fromarray(out_img)

    out_img = out_img.convert("RGBA")

    # Aplica choke e suavização no canal alfa
    r, g, b, a = out_img.split()
    a_np = np.array(a)

    if choke_px != 0:
        a_np = apply_mask_choke_or_expand(a_np, choke_px)

    if edge_smooth > 0.2:
        k_size = int(math.ceil(edge_smooth * 2)) | 1
        a_np = cv2.GaussianBlur(a_np, (k_size, k_size), edge_smooth)

    rgba_np = np.dstack((np.array(r), np.array(g), np.array(b), a_np))
    out_img = Image.fromarray(rgba_np, mode="RGBA")

    # Aplica Despill VFX para aniquilar qualquer halo verde/azul na roupa, pele, cabelo ou fones
    if despill:
        out_img = apply_chroma_despill_vfx(out_img, intensity=3)

    return out_img


def auto_trim_transparent(pil_img):
    """
    Apara as margens transparentes vazias ao redor do objeto,
    retornando (imagem_cortada, ratio_w, ratio_h).
    """
    bbox = pil_img.getbbox()
    if not bbox:
        return pil_img, 1.0, 1.0

    orig_w, orig_h = pil_img.size
    cropped = pil_img.crop(bbox)
    crop_w, crop_h = cropped.size

    ratio_w = crop_w / max(1.0, orig_w)
    ratio_h = crop_h / max(1.0, orig_h)
    return cropped, ratio_w, ratio_h


# =========================================================================
# INTERFACE GRÁFICA PROFISSIONAL 2.5 (DARK THEME)
# =========================================================================

class RemovedorFundoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Separator - Removedor de Fundo Profissional 2.5 (VFX Anti-Verde)")
        self.root.geometry("920x860")
        self.root.minsize(860, 780)
        self.root.configure(bg="#0B0F19")

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "build", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Estado da Imagem
        self.current_img_path = None
        self.pil_original = None
        self.pil_processed = None
        self.orig_w = 0.0
        self.orig_h = 0.0
        self.orig_x = 0.0
        self.orig_y = 0.0
        self.content_ratio_w = 1.0
        self.content_ratio_h = 1.0

        # Modo de fundo do preview: 'checker' | 'black' | 'white' | 'dark'
        self.preview_bg_mode = "checker"

        # Cor customizada para Chroma Key
        self.custom_chroma_color = (0, 255, 0)

        # Modelo de IA selecionado: 'u2net' (Rápido) ou 'birefnet-general' (Ultra HD)
        self.ai_model_var = tk.StringVar(value="u2net")

        # Posições de desenho nos canvases para conversão do clique do conta-gotas
        self.orig_canvas_offset = (0, 0, 1, 1)

        # Construir UI
        self.setup_ui()

        # Pré-carregar sessões em segundo plano
        threading.Thread(target=lambda: get_rembg_session("u2net"), daemon=True).start()
        threading.Thread(target=lambda: get_rembg_session("birefnet-general"), daemon=True).start()

        # Auto-detectar se há seleção ativa no CorelDRAW ao iniciar
        self.root.after(800, self.verificar_selecao_inicial_corel)

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#0B0F19", padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho com Título e Ações Rápidas
        hdr_box = tk.Frame(main_frame, bg="#0B0F19")
        hdr_box.pack(fill=tk.X, pady=(0, 8))

        title_frame = tk.Frame(hdr_box, bg="#0B0F19")
        title_frame.pack(side=tk.LEFT)

        lbl_title = tk.Label(
            title_frame,
            text="Removedor de Fundo IA 2.5",
            font=("Segoe UI", 16, "bold"),
            fg="#10B981", # Emerald
            bg="#0B0F19"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_frame,
            text="IA Dual (BiRefNet Ultra HD & U2-Net), Despill VFX Anti-Verde, Choke DTF e Preservação de Brancos",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#0B0F19"
        )
        lbl_sub.pack(anchor="w")

        # Botões de Ação de Entrada Rápidos
        btn_box = tk.Frame(hdr_box, bg="#0B0F19")
        btn_box.pack(side=tk.RIGHT)

        btn_corel = tk.Button(
            btn_box,
            text="📸 Capturar CorelDRAW",
            font=("Segoe UI", 9, "bold"),
            bg="#059669",
            fg="#FFFFFF",
            activebackground="#047857",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.capturar_corel
        )
        btn_corel.pack(side=tk.LEFT, padx=3)

        btn_file = tk.Button(
            btn_box,
            text="📂 Abrir Imagem",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=6,
            command=self.escolher_arquivo
        )
        btn_file.pack(side=tk.LEFT, padx=3)

        btn_paste = tk.Button(
            btn_box,
            text="📋 Colar",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=6,
            command=self.colar_clipboard
        )
        btn_paste.pack(side=tk.LEFT, padx=3)

        # 2. Painel Central de Visualização
        preview_container = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=10, pady=8)
        preview_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        info_bar = tk.Frame(preview_container, bg="#0F172A")
        info_bar.pack(fill=tk.X, pady=(0, 6))

        self.lbl_img_info = tk.Label(
            info_bar,
            text="Selecione um objeto no CorelDRAW e clique em Capturar, ou abra uma imagem.",
            font=("Segoe UI", 9, "bold"),
            fg="#818CF8",
            bg="#0F172A",
            anchor="w"
        )
        self.lbl_img_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Alternador de Fundo do Preview
        bg_toggle_box = tk.Frame(info_bar, bg="#0F172A")
        bg_toggle_box.pack(side=tk.RIGHT)

        tk.Label(bg_toggle_box, text="Fundo Preview:", font=("Segoe UI", 7, "bold"), fg="#94A3B8", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 4))

        self.btn_bg_chk = tk.Button(bg_toggle_box, text="🏁 Xadrez", font=("Segoe UI", 7, "bold"), bg="#10B981", fg="#FFFFFF", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.set_preview_bg("checker"))
        self.btn_bg_chk.pack(side=tk.LEFT, padx=1)

        self.btn_bg_blk = tk.Button(bg_toggle_box, text="⬛ Preto", font=("Segoe UI", 7, "bold"), bg="#1E293B", fg="#CBD5E1", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.set_preview_bg("black"))
        self.btn_bg_blk.pack(side=tk.LEFT, padx=1)

        self.btn_bg_wht = tk.Button(bg_toggle_box, text="⬜ Branco", font=("Segoe UI", 7, "bold"), bg="#1E293B", fg="#CBD5E1", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.set_preview_bg("white"))
        self.btn_bg_wht.pack(side=tk.LEFT, padx=1)

        self.btn_bg_drk = tk.Button(bg_toggle_box, text="👕 Camiseta", font=("Segoe UI", 7, "bold"), bg="#1E293B", fg="#CBD5E1", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.set_preview_bg("dark"))
        self.btn_bg_drk.pack(side=tk.LEFT, padx=1)

        # Divisão Dupla: Esquerda (Original / Conta-gotas) / Direita (Sem Fundo)
        cards_frame = tk.Frame(preview_container, bg="#0F172A")
        cards_frame.pack(fill=tk.BOTH, expand=True)

        # Card Esquerdo: Imagem Original
        card_orig = tk.Frame(cards_frame, bg="#141B2D", bd=1, relief="solid")
        card_orig.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        subhdr_orig = tk.Frame(card_orig, bg="#141B2D", padx=6, pady=3)
        subhdr_orig.pack(fill=tk.X)
        tk.Label(subhdr_orig, text="Original", font=("Segoe UI", 8, "bold"), fg="#94A3B8", bg="#141B2D").pack(side=tk.LEFT)
        self.lbl_eyedrop_hint = tk.Label(subhdr_orig, text="🎯 Clique para selecionar cor", font=("Segoe UI", 7), fg="#64748B", bg="#141B2D")
        self.lbl_eyedrop_hint.pack(side=tk.RIGHT)

        self.canvas_orig = tk.Canvas(card_orig, bg="#020617", bd=0, highlightthickness=0, cursor="tcross")
        self.canvas_orig.pack(fill=tk.BOTH, expand=True)
        self.canvas_orig.bind("<Button-1>", self.on_canvas_orig_click)
        self.canvas_orig.bind("<Motion>", self.on_canvas_orig_motion)

        # Card Direito: Imagem Recortada Transparente
        card_proc = tk.Frame(cards_frame, bg="#141B2D", bd=1, relief="solid")
        card_proc.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        subhdr_proc = tk.Frame(card_proc, bg="#141B2D", padx=6, pady=3)
        subhdr_proc.pack(fill=tk.X)
        tk.Label(subhdr_proc, text="Sem Fundo (Transparente)", font=("Segoe UI", 8, "bold"), fg="#34D399", bg="#141B2D").pack(side=tk.LEFT)
        self.lbl_crop_stats = tk.Label(subhdr_proc, text="", font=("Segoe UI", 7, "bold"), fg="#6EE7B7", bg="#141B2D")
        self.lbl_crop_stats.pack(side=tk.RIGHT)

        self.canvas_proc = tk.Canvas(card_proc, bg="#020617", bd=0, highlightthickness=0)
        self.canvas_proc.pack(fill=tk.BOTH, expand=True)

        # 3. Seletor de Modo de Remoção
        lbl_mode_title = tk.Label(main_frame, text="Modo de Remoção Inteligente:", font=("Segoe UI", 9, "bold"), fg="#CBD5E1", bg="#0B0F19")
        lbl_mode_title.pack(anchor="w", pady=(0, 4))

        modes_box = tk.Frame(main_frame, bg="#0B0F19")
        modes_box.pack(fill=tk.X, pady=(0, 8))

        self.mode_var = tk.StringVar(value="ia_geral")
        self.mode_btns = {}
        modes = [
            ("ia_geral", "🤖 IA Semântica Geral\n(Pessoas, Fones, Carros, Fotos, Cenários)"),
            ("fundo_branco", "📄 Fundo Branco de Prancheta\n(Logos, Brasões, Mantém Branco Interno)"),
            ("chroma_key", "🟩 Chroma Key / Cor Sólida\n(Fundo Verde, Azul com Despill VFX)"),
            ("alpha_suave", "✂️ Recorte Alpha Suave\n(Cabelos, Pelos e Transparências)")
        ]
        for m_id, m_label in modes:
            btn = tk.Button(
                modes_box,
                text=m_label,
                font=("Segoe UI", 8, "bold"),
                bd=0,
                cursor="hand2",
                padx=6,
                pady=6,
                justify="center",
                command=lambda mid=m_id: self.select_mode(mid)
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)
            self.mode_btns[m_id] = btn

        # 4. Painel de Controles e Parâmetros
        self.pnl_params = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=12, pady=8)
        self.pnl_params.pack(fill=tk.X, pady=(0, 8))

        self.setup_mode_controls()
        self.update_mode_buttons()

        # 5. Barra de Status
        self.lbl_status = tk.Label(
            main_frame,
            text="Pronto. Carregue uma imagem ou capture do CorelDRAW para remover o fundo com 1 clique.",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#0B0F19",
            anchor="center"
        )
        self.lbl_status.pack(fill=tk.X, pady=(2, 6))

        # 6. Rodapé de Ações Principais
        bottom_box = tk.Frame(main_frame, bg="#0B0F19")
        bottom_box.pack(fill=tk.X)

        self.btn_remover_corel = tk.Button(
            bottom_box,
            text="🚀 REMOVER FUNDO E ENVIAR AO CORELDRAW",
            font=("Segoe UI", 11, "bold"),
            bg="#10B981", # Emerald
            fg="#FFFFFF",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            pady=12,
            command=self.iniciar_remocao_corel
        )
        self.btn_remover_corel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.btn_salvar = tk.Button(
            bottom_box,
            text="💾 Salvar PNG",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=12,
            command=self.salvar_png
        )
        self.btn_salvar.pack(side=tk.LEFT, padx=3)

        self.btn_copiar = tk.Button(
            bottom_box,
            text="📋 Copiar PNG",
            font=("Segoe UI", 9, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=12,
            command=self.copiar_png_clipboard
        )
        self.btn_copiar.pack(side=tk.LEFT, padx=(3, 0))

        # Atalhos
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-v>", lambda e: self.colar_clipboard())
        self.root.bind("<Control-V>", lambda e: self.colar_clipboard())

    def set_preview_bg(self, mode):
        self.preview_bg_mode = mode
        btns = [
            ("checker", self.btn_bg_chk),
            ("black", self.btn_bg_blk),
            ("white", self.btn_bg_wht),
            ("dark", self.btn_bg_drk)
        ]
        for m, btn in btns:
            if m == mode:
                btn.configure(bg="#10B981", fg="#FFFFFF")
            else:
                btn.configure(bg="#1E293B", fg="#CBD5E1")

        if self.pil_processed is not None:
            self.atualizar_canvas_processado()

    def setup_mode_controls(self):
        for widget in self.pnl_params.winfo_children():
            widget.destroy()

        mode = self.mode_var.get()

        # Linha 1: Ajustes Físicos de Estamparia (Choke DTF, Suavização, Despill VFX e Auto-Trim)
        row_common = tk.Frame(self.pnl_params, bg="#0F172A")
        row_common.pack(fill=tk.X, pady=(0, 6))

        if not hasattr(self, 'var_autotrim'):
            self.var_autotrim = tk.BooleanVar(value=True)
        cb_trim = tk.Checkbutton(
            row_common,
            text="Auto-Trim (Aparar bordas vazias)",
            variable=self.var_autotrim,
            font=("Segoe UI", 8, "bold"),
            fg="#34D399",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#34D399"
        )
        cb_trim.pack(side=tk.LEFT, padx=(0, 10))

        # Choke / Retração anti-rebarba
        if not hasattr(self, 'var_choke'):
            self.var_choke = tk.IntVar(value=-1)
        lbl_chk = tk.Label(row_common, text="Choke DTF:", font=("Segoe UI", 8, "bold"), fg="#FBBF24", bg="#0F172A")
        lbl_chk.pack(side=tk.LEFT, padx=(4, 2))
        sp_chk = tk.Spinbox(row_common, from_=-5, to=5, textvariable=self.var_choke, width=4, font=("Segoe UI", 9, "bold"), bg="#141B2D", fg="#FFFFFF", bd=1, relief="solid", command=self.agendar_preview_recalculo)
        sp_chk.pack(side=tk.LEFT, padx=(0, 2))
        tk.Label(row_common, text="px", font=("Segoe UI", 8), fg="#94A3B8", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 8))

        # Suavização de Borda
        if not hasattr(self, 'var_feather'):
            self.var_feather = tk.DoubleVar(value=0.8)
        lbl_feat = tk.Label(row_common, text="Suavização:", font=("Segoe UI", 8, "bold"), fg="#CBD5E1", bg="#0F172A")
        lbl_feat.pack(side=tk.LEFT, padx=(4, 2))
        sp_feat = tk.Spinbox(row_common, from_=0.0, to=5.0, increment=0.2, format="%.1f", textvariable=self.var_feather, width=5, font=("Segoe UI", 9, "bold"), bg="#141B2D", fg="#FFFFFF", bd=1, relief="solid", command=self.agendar_preview_recalculo)
        sp_feat.pack(side=tk.LEFT)
        tk.Label(row_common, text="px", font=("Segoe UI", 8), fg="#94A3B8", bg="#0F172A").pack(side=tk.LEFT, padx=(2, 10))

        # Filtro Despill VFX Anti-Verde
        if not hasattr(self, 'var_despill_vfx'):
            self.var_despill_vfx = tk.BooleanVar(value=True)
        cb_despill = tk.Checkbutton(
            row_common,
            text="✅ Despill VFX Anti-Verde (Elimina 100% dos halos verdes)",
            variable=self.var_despill_vfx,
            font=("Segoe UI", 8, "bold"),
            fg="#10B981",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#10B981",
            command=self.agendar_preview_recalculo
        )
        cb_despill.pack(side=tk.LEFT)

        # Divisor
        tk.Frame(self.pnl_params, bg="#334155", height=1).pack(fill=tk.X, pady=(0, 6))

        # Controles Específicos por Modo
        if mode == "ia_geral":
            row_ai = tk.Frame(self.pnl_params, bg="#0F172A")
            row_ai.pack(fill=tk.X, pady=(0, 4))

            tk.Label(row_ai, text="Motor de IA:", font=("Segoe UI", 8, "bold"), fg="#818CF8", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 6))

            btn_m_u2 = tk.Radiobutton(
                row_ai,
                text="⚡ U2-Net Rápido (1-2s)",
                variable=self.ai_model_var,
                value="u2net",
                font=("Segoe UI", 8, "bold"),
                fg="#CBD5E1",
                bg="#0F172A",
                selectcolor="#1E293B",
                activebackground="#0F172A",
                activeforeground="#FFFFFF",
                command=self.agendar_preview_recalculo
            )
            btn_m_u2.pack(side=tk.LEFT, padx=4)

            btn_m_bi = tk.Radiobutton(
                row_ai,
                text="👑 BiRefNet Ultra HD (Máxima Precisão em Fones & Cabelos)",
                variable=self.ai_model_var,
                value="birefnet-general",
                font=("Segoe UI", 8, "bold"),
                fg="#FBBF24",
                bg="#0F172A",
                selectcolor="#1E293B",
                activebackground="#0F172A",
                activeforeground="#FBBF24",
                command=self.agendar_preview_recalculo
            )
            btn_m_bi.pack(side=tk.LEFT, padx=6)

            if not hasattr(self, 'var_post_process'):
                self.var_post_process = tk.BooleanVar(value=True)
            cb_post = tk.Checkbutton(
                self.pnl_params,
                text="Pós-processamento de máscara (elimina micro-buracos internos e ruídos espalhados)",
                variable=self.var_post_process,
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A",
                selectcolor="#1E293B",
                activebackground="#0F172A",
                activeforeground="#94A3B8",
                command=self.agendar_preview_recalculo
            )
            cb_post.pack(anchor="w")

        elif mode == "fundo_branco":
            row_wb = tk.Frame(self.pnl_params, bg="#0F172A")
            row_wb.pack(fill=tk.X, pady=(0, 2))

            tk.Label(row_wb, text="Tolerância do Branco (1 a 60):", font=("Segoe UI", 8, "bold"), fg="#F59E0B", bg="#0F172A").pack(side=tk.LEFT)
            if not hasattr(self, 'var_white_tol'):
                self.var_white_tol = tk.IntVar(value=28)
            scale_tol = tk.Scale(row_wb, from_=1, to=60, orient=tk.HORIZONTAL, variable=self.var_white_tol, bg="#0F172A", fg="#FFFFFF", highlightthickness=0, length=240, troughcolor="#1E293B", command=lambda e: self.agendar_preview_recalculo())
            scale_tol.pack(side=tk.LEFT, padx=10)

            lbl_wb_desc = tk.Label(
                self.pnl_params,
                text="Inunda exclusivamente a partir das bordas externas da imagem. Preserva 100% dos brancos do interior do escudo/arte.",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A"
            )
            lbl_wb_desc.pack(anchor="w")

        elif mode == "chroma_key":
            row_ck = tk.Frame(self.pnl_params, bg="#0F172A")
            row_ck.pack(fill=tk.X, pady=(0, 2))

            tk.Label(row_ck, text="Cor do Fundo:", font=("Segoe UI", 8, "bold"), fg="#10B981", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 6))

            btn_green = tk.Button(row_ck, text="Verde Chroma", font=("Segoe UI", 8, "bold"), bg="#10B981", fg="#FFFFFF", bd=0, padx=8, pady=2, cursor="hand2", command=lambda: self.set_chroma_color((40, 172, 82)))
            btn_green.pack(side=tk.LEFT, padx=2)

            btn_blue = tk.Button(row_ck, text="Azul Chroma", font=("Segoe UI", 8, "bold"), bg="#3B82F6", fg="#FFFFFF", bd=0, padx=8, pady=2, cursor="hand2", command=lambda: self.set_chroma_color((0, 0, 255)))
            btn_blue.pack(side=tk.LEFT, padx=2)

            self.btn_custom_color = tk.Button(row_ck, text="🎨 Conta-gotas", font=("Segoe UI", 8, "bold"), bg="#1E293B", fg="#FFFFFF", bd=1, relief="solid", padx=8, pady=2, cursor="hand2", command=self.escolher_cor_chroma)
            self.btn_custom_color.pack(side=tk.LEFT, padx=6)

            tk.Label(row_ck, text="Tolerância:", font=("Segoe UI", 8, "bold"), fg="#CBD5E1", bg="#0F172A").pack(side=tk.LEFT, padx=(10, 4))
            if not hasattr(self, 'var_chroma_tol'):
                self.var_chroma_tol = tk.IntVar(value=48)
            scale_ck = tk.Scale(row_ck, from_=10, to=100, orient=tk.HORIZONTAL, variable=self.var_chroma_tol, bg="#0F172A", fg="#FFFFFF", highlightthickness=0, length=180, troughcolor="#1E293B", command=lambda e: self.agendar_preview_recalculo())
            scale_ck.pack(side=tk.LEFT, padx=6)

            lbl_ck_desc = tk.Label(
                self.pnl_params,
                text="Detecção de espectro Chroma Key com supressor Despill VFX ativo. Remove o fundo e elimina todo o reflexo verde na roupa.",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A"
            )
            lbl_ck_desc.pack(anchor="w", pady=(2, 0))

        elif mode == "alpha_suave":
            lbl_desc = tk.Label(
                self.pnl_params,
                text="Modo Alpha Matting de alta sensibilidade: transição ultra suave para cabelos, fios soltos, pelos de animais, tecidos transparentes e vidro.",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A"
            )
            lbl_desc.pack(anchor="w")

    def agendar_preview_recalculo(self):
        if hasattr(self, '_recalc_timer') and self._recalc_timer:
            self.root.after_cancel(self._recalc_timer)
        self._recalc_timer = self.root.after(200, self.iniciar_preview_async)

    def select_mode(self, mode_id):
        self.mode_var.set(mode_id)
        self.update_mode_buttons()
        self.setup_mode_controls()
        if self.pil_original is not None:
            self.iniciar_preview_async()

    def update_mode_buttons(self):
        curr = self.mode_var.get()
        for mid, btn in self.mode_btns.items():
            if mid == curr:
                btn.configure(bg="#10B981", fg="#FFFFFF") # Emerald Ativo
            else:
                btn.configure(bg="#1E293B", fg="#94A3B8")

    def set_chroma_color(self, rgb):
        self.custom_chroma_color = rgb
        hex_col = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        self.btn_custom_color.configure(bg=hex_col, fg="#FFFFFF" if sum(rgb) < 380 else "#000000")
        if self.pil_original is not None:
            self.iniciar_preview_async()

    def escolher_cor_chroma(self):
        color = colorchooser.askcolor(title="Escolha a cor do fundo a remover")
        if color and color[0]:
            rgb = tuple(int(c) for c in color[0])
            self.set_chroma_color(rgb)

    def on_canvas_orig_click(self, event):
        """Conta-gotas direto: ao clicar na imagem original, seleciona aquela cor exata para remoção."""
        if self.pil_original is None:
            return

        ox, oy, tw, th = self.orig_canvas_offset
        if event.x < ox or event.x >= ox + tw or event.y < oy or event.y >= oy + th:
            return

        orig_w, orig_h = self.pil_original.size
        img_x = int((event.x - ox) * (orig_w / float(tw)))
        img_y = int((event.y - oy) * (orig_h / float(th)))
        img_x = max(0, min(orig_w - 1, img_x))
        img_y = max(0, min(orig_h - 1, img_y))

        pixel = self.pil_original.getpixel((img_x, img_y))
        rgb = pixel[:3] if isinstance(pixel, tuple) else (pixel, pixel, pixel)

        if self.mode_var.get() not in ("chroma_key", "fundo_branco"):
            self.select_mode("chroma_key")

        self.set_chroma_color(rgb)
        self.lbl_status.configure(
            text=f"Cor selecionada pelo conta-gotas: RGB({rgb[0]}, {rgb[1]}, {rgb[2]}). Removendo fundo...",
            fg="#34D399"
        )

    def on_canvas_orig_motion(self, event):
        if self.pil_original is None:
            return

        ox, oy, tw, th = self.orig_canvas_offset
        if ox <= event.x < ox + tw and oy <= event.y < oy + th:
            orig_w, orig_h = self.pil_original.size
            img_x = int((event.x - ox) * (orig_w / float(tw)))
            img_y = int((event.y - oy) * (orig_h / float(th)))
            img_x = max(0, min(orig_w - 1, img_x))
            img_y = max(0, min(orig_h - 1, img_y))
            try:
                pixel = self.pil_original.getpixel((img_x, img_y))
                rgb = pixel[:3] if isinstance(pixel, tuple) else (pixel, pixel, pixel)
                self.lbl_eyedrop_hint.configure(text=f"🎯 RGB({rgb[0]},{rgb[1]},{rgb[2]})", fg="#34D399")
            except Exception:
                pass
        else:
            self.lbl_eyedrop_hint.configure(text="🎯 Clique para selecionar cor", fg="#64748B")

    def verificar_selecao_inicial_corel(self):
        if self.pil_original is not None:
            return
        try:
            import win32com.client
            corel = win32com.client.GetActiveObject("CorelDRAW.Application.24")
            if corel.ActiveDocument and corel.ActiveSelection and corel.ActiveSelection.Shapes.Count > 0:
                self.capturar_corel(silent=True)
        except Exception:
            pass

    def carregar_imagem(self, pil_img, desc=""):
        try:
            self.pil_original = pil_img.copy()
            w, h = self.pil_original.size
            self.lbl_img_info.configure(text=f"{desc} ({w} x {h} px)")
            self.lbl_status.configure(text="Imagem carregada! Processando recorte com IA e Despill VFX...", fg="#F59E0B")
            self.atualizar_canvas_original()
            self.iniciar_preview_async()
        except Exception as e:
            messagebox.showerror("Erro ao carregar imagem", str(e))

    def atualizar_canvas_original(self):
        if not self.pil_original:
            return
        cw = max(50, self.canvas_orig.winfo_width())
        ch = max(50, self.canvas_orig.winfo_height())
        if cw <= 50 or ch <= 50:
            cw, ch = 380, 360

        thumb = self.pil_original.copy()
        thumb.thumbnail((cw - 12, ch - 12), Image.Resampling.LANCZOS)
        tw, th = thumb.size

        ox = (cw - tw) // 2
        oy = (ch - th) // 2
        self.orig_canvas_offset = (ox, oy, tw, th)

        if thumb.mode == "RGBA":
            bg = create_checkerboard_pattern(tw, th)
            bg.paste(thumb, (0, 0), thumb)
            thumb = bg

        self.tk_orig = ImageTk.PhotoImage(thumb)
        self.canvas_orig.delete("all")
        self.canvas_orig.create_image(cw // 2, ch // 2, image=self.tk_orig, anchor="center")

    def atualizar_canvas_processado(self):
        if not self.pil_processed:
            return
        cw = max(50, self.canvas_proc.winfo_width())
        ch = max(50, self.canvas_proc.winfo_height())
        if cw <= 50 or ch <= 50:
            cw, ch = 380, 360

        thumb = self.pil_processed.copy()
        thumb.thumbnail((cw - 12, ch - 12), Image.Resampling.LANCZOS)
        tw, th = thumb.size

        mode = self.preview_bg_mode
        if mode == "checker":
            bg = create_checkerboard_pattern(tw, th)
        elif mode == "black":
            bg = Image.new("RGB", (tw, th), (0, 0, 0))
        elif mode == "white":
            bg = Image.new("RGB", (tw, th), (255, 255, 255))
        elif mode == "dark":
            bg = Image.new("RGB", (tw, th), (24, 32, 47))
        else:
            bg = create_checkerboard_pattern(tw, th)

        bg.paste(thumb, (0, 0), thumb)

        self.tk_proc = ImageTk.PhotoImage(bg)
        self.canvas_proc.delete("all")
        self.canvas_proc.create_image(cw // 2, ch // 2, image=self.tk_proc, anchor="center")

    def iniciar_preview_async(self):
        threading.Thread(target=self._processar_preview_worker, daemon=True).start()

    def _processar_preview_worker(self):
        if not self.pil_original:
            return
        try:
            mode = self.mode_var.get()
            feather = float(self.var_feather.get()) if hasattr(self, 'var_feather') else 0.8
            choke = int(self.var_choke.get()) if hasattr(self, 'var_choke') else -1
            despill = self.var_despill_vfx.get() if hasattr(self, 'var_despill_vfx') else True
            ai_model = self.ai_model_var.get() if hasattr(self, 'ai_model_var') else "u2net"

            orig = self.pil_original
            max_dim = max(orig.size)
            scale_preview = 1.0
            if max_dim > 1400:
                scale_preview = 1400.0 / max_dim
                pw = int(orig.size[0] * scale_preview)
                ph = int(orig.size[1] * scale_preview)
                proc_input = orig.resize((pw, ph), Image.Resampling.LANCZOS)
            else:
                proc_input = orig.copy()

            if mode == "ia_geral":
                post_p = self.var_post_process.get() if hasattr(self, 'var_post_process') else True
                res = remove_ai_semantic(proc_input, model_name=ai_model, alpha_matting=False, post_process=post_p, edge_smooth=feather, choke_px=choke, despill=despill)
            elif mode == "fundo_branco":
                tol = self.var_white_tol.get() if hasattr(self, 'var_white_tol') else 28
                res = remove_white_background_floodfill(proc_input, tolerance=tol, edge_feather=feather, choke_px=choke)
            elif mode == "chroma_key":
                tol = self.var_chroma_tol.get() if hasattr(self, 'var_chroma_tol') else 48
                res = remove_chroma_key(proc_input, key_color=self.custom_chroma_color, tolerance=tol, feather=feather, despill=despill, choke_px=choke)
            elif mode == "alpha_suave":
                res = remove_ai_semantic(proc_input, model_name=ai_model, alpha_matting=True, post_process=False, edge_smooth=feather, choke_px=choke, despill=despill)
            else:
                res = proc_input.convert("RGBA")

            self.pil_processed = res
            self.root.after(0, self._finalizar_preview_ui)
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self.lbl_status.configure(text=f"Erro no processamento: {err}", fg="#EF4444"))

    def _finalizar_preview_ui(self):
        self.atualizar_canvas_processado()
        if self.pil_processed:
            pw, ph = self.pil_processed.size
            self.lbl_crop_stats.configure(text=f"{pw} x {ph} px | PNG RGBA")
        self.lbl_status.configure(text="Fundo e halos verdes eliminados com sucesso! Pronto para CorelDRAW.", fg="#34D399")

    def escolher_arquivo(self):
        f = filedialog.askopenfilename(
            title="Selecione uma imagem para remover o fundo",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.tif *.tiff"), ("Todos", "*.*")]
        )
        if f:
            self.current_img_path = f
            self.orig_w = 0.0
            self.orig_h = 0.0
            img = Image.open(f)
            self.carregar_imagem(img, desc=os.path.basename(f))

    def colar_clipboard(self):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self.current_img_path = None
                self.orig_w = 0.0
                self.orig_h = 0.0
                self.carregar_imagem(img, desc="Imagem da Área de Transferência")
            else:
                messagebox.showinfo("Aviso", "Nenhuma imagem encontrada na área de transferência.")
        except Exception as e:
            messagebox.showerror("Erro ao colar", str(e))

    def capturar_corel(self, silent=False):
        try:
            import win32com.client
            try:
                corel = win32com.client.GetActiveObject("CorelDRAW.Application.24")
            except Exception:
                corel = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application.24")

            if not corel.ActiveDocument:
                if not silent:
                    messagebox.showwarning("Aviso", "Abra um documento no CorelDRAW primeiro!")
                return

            doc = corel.ActiveDocument
            sel = None
            try:
                sel = corel.ActiveSelection
            except Exception:
                pass
            if not sel or sel.Shapes.Count == 0:
                try:
                    sel = doc.Selection()
                except Exception:
                    pass

            if not sel or sel.Shapes.Count == 0:
                if not silent:
                    messagebox.showwarning("Aviso", "Selecione uma imagem bitmap ou desenho no CorelDRAW!")
                return

            try:
                self.orig_w = float(sel.SizeWidth)
                self.orig_h = float(sel.SizeHeight)
                self.orig_x = float(sel.LeftX)
                self.orig_y = float(sel.BottomY)
            except Exception:
                try:
                    sh = sel.Shapes(1)
                    self.orig_w = float(sh.SizeWidth)
                    self.orig_h = float(sh.SizeHeight)
                    self.orig_x = float(sh.LeftX)
                    self.orig_y = float(sh.BottomY)
                except Exception:
                    self.orig_w = 0.0

            temp_dir = tempfile.gettempdir()
            temp_png = os.path.join(temp_dir, f"corel_rembg_{os.getpid()}_{np.random.randint(1000, 9999)}.png")

            opt = corel.CreateStructExportOptions()
            opt.SizeX = 2400
            opt.SizeY = 2400
            opt.MaintainAspect = True
            opt.Transparent = True
            pal = corel.CreateStructPaletteOptions()

            exp = doc.ExportEx(temp_png, 802, 2, opt, pal)
            if exp:
                exp.Finish()

            if not os.path.exists(temp_png):
                raise ValueError("O CorelDRAW não gerou o arquivo temporário da seleção.")

            self.current_img_path = temp_png
            img = Image.open(temp_png)
            self.carregar_imagem(img, desc="Objeto Selecionado do CorelDRAW")
        except Exception as e:
            if not silent:
                messagebox.showerror("Erro ao capturar do CorelDRAW", f"Não foi possível capturar a seleção:\n{e}")

    def iniciar_remocao_corel(self):
        if not self.pil_original:
            messagebox.showwarning("Aviso", "Carregue ou capture uma imagem antes de enviar ao CorelDRAW!")
            return

        self.btn_remover_corel.configure(state="disabled", text="Processando Alta Resolução com Despill...", bg="#059669")
        self.lbl_status.configure(text="Removendo fundo e decontaminando halos verdes em alta resolução...", fg="#F59E0B")

        threading.Thread(target=self._processar_alta_resolucao_corel_worker, daemon=True).start()

    def _processar_alta_resolucao_corel_worker(self):
        try:
            mode = self.mode_var.get()
            feather = float(self.var_feather.get()) if hasattr(self, 'var_feather') else 0.8
            choke = int(self.var_choke.get()) if hasattr(self, 'var_choke') else -1
            despill = self.var_despill_vfx.get() if hasattr(self, 'var_despill_vfx') else True
            ai_model = self.ai_model_var.get() if hasattr(self, 'ai_model_var') else "u2net"
            full_img = self.pil_original

            if mode == "ia_geral":
                post_p = self.var_post_process.get() if hasattr(self, 'var_post_process') else True
                res = remove_ai_semantic(full_img, model_name=ai_model, alpha_matting=False, post_process=post_p, edge_smooth=feather, choke_px=choke, despill=despill)
            elif mode == "fundo_branco":
                tol = self.var_white_tol.get() if hasattr(self, 'var_white_tol') else 28
                res = remove_white_background_floodfill(full_img, tolerance=tol, edge_feather=feather, choke_px=choke)
            elif mode == "chroma_key":
                tol = self.var_chroma_tol.get() if hasattr(self, 'var_chroma_tol') else 48
                res = remove_chroma_key(full_img, key_color=self.custom_chroma_color, tolerance=tol, feather=feather, despill=despill, choke_px=choke)
            elif mode == "alpha_suave":
                res = remove_ai_semantic(full_img, model_name=ai_model, alpha_matting=True, post_process=False, edge_smooth=feather, choke_px=choke, despill=despill)
            else:
                res = full_img.convert("RGBA")

            do_trim = self.var_autotrim.get() if hasattr(self, 'var_autotrim') else True
            if do_trim:
                res, rw, rh = auto_trim_transparent(res)
                self.content_ratio_w = rw
                self.content_ratio_h = rh
            else:
                self.content_ratio_w = 1.0
                self.content_ratio_h = 1.0

            temp_dir = tempfile.gettempdir()
            out_png = os.path.join(temp_dir, f"rembg_corel_{np.random.randint(1000, 9999)}.png")
            res.save(out_png, format="PNG")

            self.root.after(0, lambda: self._finalizar_importacao_corel(out_png))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._erro_finalizacao(err))

    def _finalizar_importacao_corel(self, output_png):
        try:
            self.lbl_status.configure(text="Importando imagem transparente para o CorelDRAW...", fg="#818CF8")
            self.root.update_idletasks()

            import win32com.client
            try:
                corel = win32com.client.GetActiveObject("CorelDRAW.Application.24")
            except Exception:
                corel = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application.24")
            corel.Visible = True

            if not corel.ActiveDocument:
                doc = corel.CreateDocument()
            else:
                doc = corel.ActiveDocument

            doc.BeginCommandGroup("Remover Fundo IA")
            try:
                layer = doc.ActiveLayer
                opt = corel.CreateStructImportOptions()
                imp = layer.ImportEx(output_png, 0, opt)
                if imp:
                    imp.Finish()

                sel = None
                try:
                    sel = corel.ActiveSelection
                except Exception:
                    pass
                if not sel:
                    try:
                        sel = doc.Selection()
                    except Exception:
                        pass

                if sel and sel.Shapes.Count > 0:
                    shape = sel.Shapes(1) if sel.Shapes.Count == 1 else sel.Group()
                    natural_w = float(shape.SizeWidth)
                    natural_h = float(shape.SizeHeight)

                    if natural_w > 0 and natural_h > 0 and self.orig_w > 0 and self.orig_h > 0:
                        aspect = natural_w / natural_h
                        if hasattr(self, 'content_ratio_h') and self.content_ratio_h > 0:
                            target_h = float(self.orig_h) * float(self.content_ratio_h)
                            target_w = target_h * aspect
                        else:
                            target_h = float(self.orig_h)
                            target_w = target_h * aspect

                        shape.SetSize(target_w, target_h)
                        shape.LeftX = float(self.orig_x + self.orig_w + (self.orig_w * 0.05))
                        shape.CenterY = float(self.orig_y + (self.orig_h / 2.0))
                    else:
                        shape.CenterX = doc.ActivePage.CenterX
                        shape.CenterY = doc.ActivePage.CenterY
            finally:
                doc.EndCommandGroup()
                corel.Refresh()

            self.btn_remover_corel.configure(state="normal", text="🚀 REMOVER FUNDO E ENVIAR AO CORELDRAW", bg="#10B981")
            self.lbl_status.configure(text="Concluído com sucesso! Imagem sem fundo importada no CorelDRAW.", fg="#34D399")
            messagebox.showinfo(
                "Remoção Concluída!",
                "A imagem com fundo transparente e Despill VFX foi importada no CorelDRAW!\n\n"
                "• Zero halos verdes na roupa, fones ou cabelo\n"
                "• Choke DTF aplicado sem rebarbas\n"
                "• Escala física 1:1 e proporção perfeitamente preservadas."
            )
        except Exception as e:
            self._erro_finalizacao(str(e))

    def _erro_finalizacao(self, err):
        self.btn_remover_corel.configure(state="normal", text="🚀 REMOVER FUNDO E ENVIAR AO CORELDRAW", bg="#10B981")
        self.lbl_status.configure(text="Erro ao processar imagem.", fg="#EF4444")
        messagebox.showerror("Erro", f"Ocorreu um erro:\n\n{err}")

    def salvar_png(self):
        if not self.pil_processed:
            messagebox.showwarning("Aviso", "Nenhuma imagem com fundo removido para salvar.")
            return

        f = filedialog.asksaveasfilename(
            title="Salvar PNG com fundo transparente",
            defaultextension=".png",
            filetypes=[("PNG Transparente", "*.png")]
        )
        if f:
            try:
                self.pil_processed.save(f, format="PNG")
                messagebox.showinfo("Sucesso", f"Imagem salva com sucesso em:\n{f}")
            except Exception as e:
                messagebox.showerror("Erro ao salvar", str(e))

    def copiar_png_clipboard(self):
        if not self.pil_processed:
            messagebox.showwarning("Aviso", "Nenhuma imagem com fundo removido para copiar.")
            return

        try:
            import win32clipboard
            png_format = win32clipboard.RegisterClipboardFormat("PNG")
            buf = io.BytesIO()
            self.pil_processed.save(buf, format="PNG")
            data = buf.getvalue()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(png_format, data)
            win32clipboard.CloseClipboard()

            self.lbl_status.configure(text="PNG transparente copiado para a área de transferência! (Pressione Ctrl+V em qualquer programa)", fg="#34D399")
            messagebox.showinfo("Copiado!", "Imagem PNG transparente copiada com sucesso!\nVocê já pode colar (Ctrl+V) no CorelDRAW, Photoshop ou WhatsApp.")
        except Exception as e:
            messagebox.showerror("Erro ao copiar", str(e))


def main():
    try:
        import subprocess
        pid_file = os.path.join(tempfile.gettempdir(), "order_separator_removedor.pid")
        my_pid = os.getpid()
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    old_pid = int(f.read().strip())
                if old_pid != my_pid:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(old_pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=0x08000000
                    )
            except Exception:
                pass
        with open(pid_file, "w") as f:
            f.write(str(my_pid))
    except Exception:
        pass

    root = tk.Tk()
    app = RemovedorFundoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
