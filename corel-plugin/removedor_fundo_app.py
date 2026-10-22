"""
Order Separator - Removedor de Fundo Profissional 2.6 para CorelDRAW
Motor Inteligente de Remoção de Fundo com IA U2-Net DirectML RTX + Guided Filter O(1),
Fundo Branco de Prancheta com Anti-Halo de Juba/Pelos, Chroma Key com Despill de Hardware VFX,
Conta-gotas Interativo no Canvas, Choke/Sangria DTF e Eliminação Total de Halos Verdes e Brancos.
100% Offline, Leve (<150MB RAM), Rápido, Gratuito e Sem Limites.
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
import json
import time

# Importação condicional do rembg
try:
    import rembg
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

# Sessões ONNX mantidas em cache para inferência instantânea na GPU DirectML (NVIDIA RTX)
GLOBAL_REMBG_SESSIONS = {}
ACTIVE_HARDWARE_INFO = "Detectando..."

SUPPORTED_AI_MODELS = {
    "u2net": {
        "id": "u2net",
        "nome": "⚡ U2-Net Geral (Ultrarrápido 20ms - Padrão)",
        "badge": "Recomendado para Uso Geral"
    },
    "isnet-general-use": {
        "id": "isnet-general-use",
        "nome": "🦁 IS-Net DIS (Ultra Precisão / Pelos, Juba & Fios)",
        "badge": "Pelos, Cabelos e Fibras Finas"
    },
    "isnet-anime": {
        "id": "isnet-anime",
        "nome": "🎨 IS-Net 2D (Logos, Desenhos, Mascotes e Vetores)",
        "badge": "Escudos e Ilustrações"
    },
    "bria-rmbg": {
        "id": "bria-rmbg",
        "nome": "💎 BRIA RMBG 1.4 (Alta Definição / Roupas & Estamparia)",
        "badge": "Estúdio de Moda & Roupas"
    }
}

CURRENT_SELECTED_MODEL = "u2net"

def get_rembg_session(model_name="u2net"):
    global GLOBAL_REMBG_SESSIONS, ACTIVE_HARDWARE_INFO
    if not HAS_REMBG:
        return None
    if model_name not in GLOBAL_REMBG_SESSIONS:
        try:
            GLOBAL_REMBG_SESSIONS[model_name] = rembg.new_session(model_name, providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
            ACTIVE_HARDWARE_INFO = f"⚡ GPU DirectML RTX ({model_name})"
        except Exception:
            try:
                GLOBAL_REMBG_SESSIONS[model_name] = rembg.new_session(model_name)
                ACTIVE_HARDWARE_INFO = f"CPU Multithread ({model_name})"
            except Exception:
                if model_name != "u2net":
                    return get_rembg_session("u2net")
                return None
    return GLOBAL_REMBG_SESSIONS.get(model_name)


# =========================================================================
# MOTOR DE CONTEXTO DE ESTAMPARIA E RAIO-X INTELIGENTE DA ARTE
# =========================================================================

FABRIC_COLORS_MAP = {
    "PRETA": (18, 18, 20),
    "PRETO": (18, 18, 20),
    "BRANCA": (245, 245, 248),
    "BRANCO": (245, 245, 248),
    "ROXA": (88, 28, 135),
    "ROXO": (88, 28, 135),
    "VERMELHA": (185, 28, 28),
    "VERMELHO": (185, 28, 28),
    "AZUL": (29, 78, 216),
    "AZUL MARINHO": (15, 23, 42),
    "MARINHO": (15, 23, 42),
    "VERDE": (21, 128, 61),
    "AMARELA": (234, 179, 8),
    "AMARELO": (234, 179, 8),
    "CINZA": (100, 116, 139),
    "MESCLA": (148, 163, 184),
    "LARANJA": (234, 88, 12),
    "ROSA": (219, 39, 119),
    "BORDO": (120, 20, 40),
    "VINHO": (120, 20, 40)
}

def load_estamparia_context():
    """Carrega todos os pedidos e clientes para fornecer contexto de produção à IA."""
    db_paths = [
        os.path.join(os.environ.get('APPDATA', ''), 'estamparia-manager', 'db_estamparia.json'),
        os.path.join(os.environ.get('APPDATA', ''), 'Order Separator', 'db_estamparia.json'),
    ]
    for p in db_paths:
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                    return db.get('pedidos', []), db.get('clientes', [])
            except Exception:
                pass
    return [], []

def analyze_image_context(pil_img):
    """
    Analisa características da imagem para Raio-X de Estamparia:
    - DPI e tamanho físico em centímetros @ 300 DPI
    - Sugestão contextual do melhor modelo IA (U2-Net, IS-Net DIS, IS-Net 2D)
    - Sugestão contextual do modo de recorte
    - Alerta de qualidade para impressão DTF / Silk
    """
    w, h = pil_img.size
    cm_w = round((w / 300.0) * 2.54, 1)
    cm_h = round((h / 300.0) * 2.54, 1)

    if cm_w <= 12:
        classificacao = "Peito / Bolso (~10cm)"
    elif cm_w <= 22:
        classificacao = "Frente A4 (~20cm)"
    elif cm_w <= 32:
        classificacao = "Costas A3 (~30cm)"
    else:
        classificacao = "Bobina Total / Painel (40-58cm)"

    rgb_img = pil_img.convert("RGB")
    arr = np.array(rgb_img)
    borda_topo = arr[:4, :, :]
    borda_base = arr[-4:, :, :]
    borda_esq = arr[:, :4, :]
    borda_dir = arr[:, -4:, :]
    borda_pixels = np.vstack([borda_topo.reshape(-1, 3), borda_base.reshape(-1, 3), borda_esq.reshape(-1, 3), borda_dir.reshape(-1, 3)])

    r_mean = np.mean(borda_pixels[:, 0])
    g_mean = np.mean(borda_pixels[:, 1])
    b_mean = np.mean(borda_pixels[:, 2])

    sugestao_modo = "ia_geral"
    sugestao_modelo = "u2net"
    motivo_sugestao = "IA Geral Semântica equilibrada"

    if g_mean > r_mean + 28 and g_mean > b_mean + 28:
        sugestao_modo = "chroma_key"
        motivo_sugestao = "Fundo Verde Chroma Key detectado nas bordas externas."
    elif r_mean > 238 and g_mean > 238 and b_mean > 238:
        sugestao_modo = "fundo_branco"
        motivo_sugestao = "Prancheta/fundo branco uniforme detectado nas bordas."
    else:
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap_var > 350:
            sugestao_modo = "alpha_suave"
            sugestao_modelo = "isnet-general-use"
            motivo_sugestao = "Fios/pelos finos detectados (IS-Net DIS + Guided Filter recomendado)."
        else:
            unique_colors_sample = len(np.unique(borda_pixels // 32, axis=0))
            if unique_colors_sample <= 3:
                sugestao_modelo = "isnet-anime"
                motivo_sugestao = "Arte gráfica / escudo com cores planas (IS-Net 2D recomendado)."

    alerta_qualidade = None
    if w < 900 or h < 900:
        alerta_qualidade = f"⚠️ Resolução baixa ({w}x{h} px = {cm_w}x{cm_h} cm @ 300DPI). Sugerido rodar Upscale 4x IA."

    return {
        "dim_px": f"{w} x {h} px",
        "dim_cm": f"{cm_w} x {cm_h} cm @ 300 DPI",
        "classificacao": classificacao,
        "sugestao_modo": sugestao_modo,
        "sugestao_modelo": sugestao_modelo,
        "motivo": motivo_sugestao,
        "alerta": alerta_qualidade
    }


# =========================================================================
# MOTORES DE PROCESSAMENTO DE IMAGEM E REMOÇÃO DE FUNDO 2.6
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


def analyze_image_background(arr_rgb):
    """
    Analisa o perímetro da imagem (bordas externas) para detectar automaticamente
    se o fundo original é Branco/Claro, Chroma Key Verde, Chroma Key Azul ou Outro.
    Permite acionar a decontaminação cirúrgica exata sem adivinhação do usuário.
    """
    h, w = arr_rgb.shape[:2]
    bw = max(2, min(w, h) // 30)
    top = arr_rgb[:bw, :]
    bottom = arr_rgb[-bw:, :]
    left = arr_rgb[:, :bw]
    right = arr_rgb[:, -bw:]

    border_pixels = np.concatenate([
        top.reshape(-1, 3), bottom.reshape(-1, 3),
        left.reshape(-1, 3), right.reshape(-1, 3)
    ], axis=0).astype(np.float32)

    r = border_pixels[:, 0]
    g = border_pixels[:, 1]
    b = border_pixels[:, 2]

    lum = (r + g + b) / 3.0
    chroma = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)

    is_white_border = (lum > 215.0) & (chroma < 25.0)
    sum_c = r + g + b + 1e-4
    ng = g / sum_c
    is_green_border = (ng > 0.43) & (g - np.maximum(r, b) > 12.0)
    nb = b / sum_c
    is_blue_border = (nb > 0.43) & (b - np.maximum(r, g) > 12.0)

    return {
        'is_white_bg': bool(np.mean(is_white_border) > 0.45),
        'is_green_bg': bool(np.mean(is_green_border) > 0.35),
        'is_blue_bg': bool(np.mean(is_blue_border) > 0.35)
    }


def fast_guided_filter(guide_rgb, src_mask, radius=4, eps=1e-3):
    """
    Filtro Guiado O(1) ultra-rápido (<30ms) em NumPy/OpenCV.
    Alinha perfeitamente a máscara de probabilidade do U2-Net aos fios finos de cabelo,
    juba de leão, pelos de animais e fibras da imagem original de alta resolução,
    eliminando contornos borrados sem sobrecarregar a memória RAM.
    """
    guide = cv2.cvtColor(guide_rgb, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    p = src_mask.astype(np.float32) / 255.0
    ksize = (radius * 2 + 1, radius * 2 + 1)

    mean_I = cv2.boxFilter(guide, -1, ksize)
    mean_p = cv2.boxFilter(p, -1, ksize)
    corr_Ip = cv2.boxFilter(guide * p, -1, ksize)
    corr_II = cv2.boxFilter(guide * guide, -1, ksize)

    var_I = corr_II - mean_I * mean_I
    cov_Ip = corr_Ip - mean_I * mean_p

    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I

    mean_a = cv2.boxFilter(a, -1, ksize)
    mean_b = cv2.boxFilter(b, -1, ksize)

    q = mean_a * guide + mean_b
    return np.clip(q * 255.0, 0, 255).astype(np.uint8)


def decontaminate_white_fringe(rgb, alpha, bg_val=255.0):
    """
    Elimina 100% de halos brancos, névoas e manchas claras ao redor de pelos de leão,
    cabelos, fibras e detalhes finos:
    1. Reduz e zera qualquer névoa/ruído de baixa confiança em pixels quase brancos.
    2. Realiza Unpremultiplication para recuperar o tom puro dos fios (juba dourada/castanha).
    3. Expande e mescla as cores sólidas do núcleo (alpha >= 220) para o bordo semi-transparente.
    4. Limita a luminância do bordo para impedir que fios fiquem com brilho esbranquiçado.
    """
    a_f = (alpha.astype(np.float32) / 255.0)[:, :, None]
    rgb_f = rgb.astype(np.float32)
    solid_mask = (alpha >= 220)

    # 1. Limpeza de névoa fantasma em pixels de fundo branco/quase branco
    lum = (rgb_f[:, :, 0] + rgb_f[:, :, 1] + rgb_f[:, :, 2]) / 3.0
    max_c = np.maximum(np.maximum(rgb_f[:, :, 0], rgb_f[:, :, 1]), rgb_f[:, :, 2])
    min_c = np.minimum(np.minimum(rgb_f[:, :, 0], rgb_f[:, :, 1]), rgb_f[:, :, 2])
    chroma = max_c - min_c

    is_white_bg_speck = (lum > 215.0) & (chroma < 24.0) & (alpha < 130)
    alpha_clean = np.where(is_white_bg_speck, np.clip((alpha.astype(np.float32) - 35.0) * 0.4, 0.0, 255.0), alpha.astype(np.float32))
    alpha_clean = np.where(alpha_clean < 14.0, 0.0, alpha_clean).astype(np.uint8)
    a_f = (alpha_clean.astype(np.float32) / 255.0)[:, :, None]

    # 2. Extensão multi-escala das cores sólidas internas
    solid_f = solid_mask.astype(np.float32)[:, :, None]
    b_rgb = cv2.boxFilter(rgb_f * solid_f, -1, (7, 7), normalize=False)
    b_w = cv2.boxFilter(solid_f, -1, (7, 7), normalize=False)[:, :, None]

    need_broader = (b_w < 0.05) & (alpha_clean[:, :, None] > 0) & (alpha_clean[:, :, None] < 220)
    if np.any(need_broader):
        b_rgb2 = cv2.boxFilter(rgb_f * solid_f, -1, (19, 19), normalize=False)
        b_w2 = cv2.boxFilter(solid_f, -1, (19, 19), normalize=False)[:, :, None]
        b_rgb = np.where(need_broader, b_rgb2, b_rgb)
        b_w = np.where(need_broader, b_w2, b_w)

    ext_rgb = np.where(b_w > 0.05, b_rgb / np.maximum(b_w, 1e-4), rgb_f)

    # 3. Unpremultiplication exata
    unprem_rgb = np.clip((rgb_f - bg_val * (1.0 - a_f)) / np.maximum(a_f, 0.05), 0.0, 255.0)

    # 4. Mesclagem adaptativa: em alpha alto usa unprem, em alpha baixo usa cor sólida estendida
    blend = np.clip((a_f - 0.25) / 0.45, 0.0, 1.0)
    clean_rgb = blend * unprem_rgb + (1.0 - blend) * ext_rgb

    # Garante que a luminância da borda semi-transparente não ultrapasse a cor do sujeito
    clean_lum = np.mean(clean_rgb, axis=2, keepdims=True)
    ext_lum = np.mean(ext_rgb, axis=2, keepdims=True)
    clean_rgb = np.where((alpha_clean[:, :, None] < 220) & (clean_lum > ext_lum + 10.0), ext_rgb, clean_rgb)

    res_rgba = np.dstack((np.clip(clean_rgb, 0, 255).astype(np.uint8), alpha_clean))
    return res_rgba


def apply_chroma_despill_vfx(img_rgba, intensity=3.0):
    """
    Filtro Hollywood VFX de Despill e Eliminação Total de Halos Verdes e Azuis:
    1. Elimina faixas/manchas de fundo verde residual (incluindo sombras escuras e cantos).
    2. Decontamina o reflexo verde da luz que rebate na roupa, terno, cabelo, pele e fones.
    3. Converte a rebarba verde em tom neutro perfeitamente integrado ao sujeito (terno escuro / cabelo).
    """
    arr = np.array(img_rgba, dtype=np.float32)
    r = arr[:, :, 0]
    g = arr[:, :, 1]
    b = arr[:, :, 2]
    a = arr[:, :, 3]

    sum_c = r + g + b + 1e-4
    ng = g / sum_c
    nb = b / sum_c

    # 1. Limpeza de Fundo Verde Residual Puro e em Sombras
    excess_g = g - np.maximum(r, b)
    is_pure_chroma_green = (ng > 0.44) & (excess_g > 14.0)
    a = np.where(is_pure_chroma_green, 0.0, a)

    # Elimina pixels de borda com resquício esverdeado evidente
    edge_green = (ng > 0.40) & (excess_g > 5.0) & (a > 0.0)
    a = np.where(edge_green, np.clip(a - 35.0 * intensity, 0.0, 255.0), a)

    # Limpeza de Fundo Azul Residual Puro (Blue Screen)
    excess_b = b - np.maximum(r, g)
    is_pure_chroma_blue = (nb > 0.44) & (excess_b > 16.0)
    a = np.where(is_pure_chroma_blue, 0.0, a)

    edge_blue = (nb > 0.40) & (excess_b > 6.0) & (a > 0.0)
    a = np.where(edge_blue, np.clip(a - 35.0 * intensity, 0.0, 255.0), a)

    # 2. Despill nas Bordas e no Primeiro Plano
    # Substitui o excesso verde pela média neutra entre R e B
    limit_g = np.minimum(np.maximum(r, b), 0.5 * (r + b) + 2.0)
    has_green_spill = (g > limit_g) & (a > 0.0)
    g = np.where(has_green_spill, limit_g, g)

    # Despill Azul
    limit_b = np.minimum(np.maximum(r, g), 0.5 * (r + g) + 2.0)
    has_blue_spill = (b > limit_b) & (a > 0.0)
    b = np.where(has_blue_spill, limit_b, b)

    res = np.dstack((np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255), np.clip(a, 0, 255))).astype(np.uint8)
    return Image.fromarray(res, mode="RGBA")


def decontaminate_edge_colors(img_rgba_np, alpha_np):
    """
    Decontamina as cores das bordas semi-transparentes:
    Neutraliza o tom do fundo removido nos pixels de borda, puxando a cor sólida interna mais próxima.
    """
    edge_mask = (alpha_np > 5) & (alpha_np < 235)
    if not np.any(edge_mask):
        return img_rgba_np

    rgb = img_rgba_np[:, :, :3].astype(np.float32)
    solid_mask = (alpha_np >= 235).astype(np.float32)[:, :, None]

    if np.count_nonzero(solid_mask) > 50:
        b_rgb = cv2.boxFilter(rgb * solid_mask, -1, (7, 7), normalize=False)
        b_w = cv2.boxFilter(solid_mask, -1, (7, 7), normalize=False)[:, :, None]

        need_broader = (b_w < 0.05) & edge_mask[:, :, None]
        if np.any(need_broader):
            b_rgb2 = cv2.boxFilter(rgb * solid_mask, -1, (17, 17), normalize=False)
            b_w2 = cv2.boxFilter(solid_mask, -1, (17, 17), normalize=False)[:, :, None]
            b_rgb = np.where(need_broader, b_rgb2, b_rgb)
            b_w = np.where(need_broader, b_w2, b_w)

        inpaint_color = np.where(b_w > 0.05, b_rgb / np.maximum(b_w, 1e-4), rgb)
        blend_factor = (alpha_np.astype(np.float32) / 255.0)[:, :, None]
        rgb = np.where(edge_mask[:, :, None], inpaint_color * (1.0 - blend_factor) + rgb * blend_factor, rgb)

    res = np.dstack((np.clip(rgb, 0, 255).astype(np.uint8), alpha_np))
    return res


def remove_white_background_floodfill(pil_img, tolerance=28, edge_feather=1.0, choke_px=0, defringe=True):
    """
    Remove o fundo branco externo (canvas/bounding box de prancheta)
    através de floodfill conectado exclusivamente pelas bordas externas da imagem.
    PRESERVA 100% DOS BRANCOS INTERNOS (olhos, dentes, camisas, faixas brancas).
    Aplica Anti-Halo de prancheta para bordas 100% nítidas.
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
    # Rastreia todo o perímetro contínuo das 4 bordas
    for x in range(0, w, 2):
        sample_points.append((x, 0))
        sample_points.append((x, h - 1))
    for y in range(0, h, 2):
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

    if defringe:
        res_arr = decontaminate_white_fringe(arr, alpha, bg_val=255.0)
    else:
        res_arr = np.dstack((arr, alpha))
        res_arr = decontaminate_edge_colors(res_arr, alpha)

    return Image.fromarray(res_arr, mode="RGBA")


def remove_fake_png_checkerboard(pil_img, tolerance=30, edge_feather=0.8, choke_px=0):
    """
    Remove quadriculado falso de transparência da web (Google Images / Falso PNG).
    Muitas imagens baixadas do Google vêm com xadrez cinza e branco desenhado nos pixels.
    Esta função rastreia o xadrez conectando pelas bordas externas da imagem através de
    floodfill inteligente, eliminando 100% dos quadrados externos sem apagar o interior da arte,
    preservando 100% de remos, âncoras, escudos, letras e detalhes brancos internos.
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

    # Xadrez web do Google alterna entre cinza claro (~180-220) e branco (~240-255)
    # com saturação (croma) praticamente nula (tons neutros)
    lum_thresh = max(130, 220 - int(tolerance * 1.6))
    max_chroma = max(12, int(tolerance * 0.75))

    is_checker_candidate = (lum >= lum_thresh) & (chroma <= max_chroma)

    sample_points = []
    for x in range(0, w, 2):
        sample_points.append((x, 0))
        sample_points.append((x, h - 1))
    for y in range(0, h, 2):
        sample_points.append((0, y))
        sample_points.append((w - 1, y))

    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    for pt_x, pt_y in sample_points:
        if is_checker_candidate[pt_y, pt_x] and flood_mask[pt_y + 1, pt_x + 1] == 0:
            cv2.floodFill(
                is_checker_candidate.astype(np.uint8),
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
    - Distância perceptual Delta-E em espaço de cor CIELAB
    - Detecção espectral de Chroma Key (eliminando 100% de sombras e cantos verdes)
    - Despill avançado de hardware VFX (elimina 100% de reflexos verdes/azuis no sujeito)
    - Choke de borda anti-rebarba e decontaminação de cores
    """
    img_rgb = pil_img.convert("RGB")
    arr_rgb = np.array(img_rgb, dtype=np.uint8)
    h, w = arr_rgb.shape[:2]

    kr, kg, kb = [int(c) for c in key_color[:3]]
    key_arr = np.array([[[kr, kg, kb]]], dtype=np.uint8)

    # Distância perceptual uniforme em espaço CIELAB
    img_lab = cv2.cvtColor(arr_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    key_lab = cv2.cvtColor(key_arr, cv2.COLOR_RGB2LAB)[0, 0].astype(np.float32)
    dist = np.sqrt(np.sum((img_lab - key_lab)**2, axis=2))

    r = arr_rgb[:, :, 0].astype(np.float32)
    g = arr_rgb[:, :, 1].astype(np.float32)
    b = arr_rgb[:, :, 2].astype(np.float32)
    sum_c = r + g + b + 1e-4

    is_key_green = (kg > kr + 20) and (kg > kb + 20)
    is_key_blue = (kb > kr + 20) and (kb > kg + 20)

    if is_key_green:
        excess_g = g - np.maximum(r, b)
        # Qualquer pixel no espectro chroma verde (mesmo em sombras escuras) tem distância forçada para 0
        chroma_dist = np.clip(60.0 - excess_g * 2.5, 0.0, 100.0)
        dist = np.minimum(dist, chroma_dist)
    elif is_key_blue:
        excess_b = b - np.maximum(r, g)
        chroma_dist = np.clip(60.0 - excess_b * 2.5, 0.0, 100.0)
        dist = np.minimum(dist, chroma_dist)

    tol_low = max(4.0, float(tolerance) * 0.5)
    tol_high = max(tol_low + 6.0, float(tolerance) * 1.15)

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

    res_arr = np.dstack((arr_rgb, alpha))
    res_arr = decontaminate_edge_colors(res_arr, alpha)
    res_img = Image.fromarray(res_arr, mode="RGBA")

    if despill:
        res_img = apply_chroma_despill_vfx(res_img, intensity=3.0)

    return res_img


def remove_ai_semantic(pil_img, model_name="u2net", alpha_matting=False, post_process=True, edge_smooth=1.0, choke_px=0, despill=True, defringe_white=True):
    """
    Remove o fundo usando Inteligência Artificial Semântica (U2-Net / IS-Net DIS / IS-Net 2D / BRIA com DirectML RTX) +
    Refino de Fios/Pelos Guided Filter + Despill VFX + Anti-Halo Branco.
    Funciona para pessoas, leões, animais, fones, cabelos e cenários complexos.
    Garante zero resíduos brancos ou verdes na juba e nas bordas.
    """
    if not HAS_REMBG:
        raise RuntimeError("Biblioteca 'rembg' não está instalada no ambiente Python.")

    session = get_rembg_session(model_name)

    # Executa remoção neural inicial com o modelo selecionado via DirectML
    out_img = rembg.remove(
        pil_img,
        session=session,
        alpha_matting=False,
        post_process_mask=post_process
    )

    if not isinstance(out_img, Image.Image):
        out_img = Image.fromarray(out_img)

    out_img = out_img.convert("RGBA")
    orig_rgb = np.array(pil_img.convert("RGB"))
    r, g, b, a = out_img.split()
    a_np = np.array(a)

    # 1. Refinamento de Pelos e Fios com Filtro Guiado O(1) de Alta Resolução
    # Captura os fios finos da juba do leão e cabelo sem névoa branca
    if alpha_matting:
        # Modo Alpha Suave: sensibilidade máxima para cabelos e transparências
        a_np = fast_guided_filter(orig_rgb, a_np, radius=6, eps=1e-4)
    else:
        # Modo IA Geral: fidelidade e bordas limpas
        a_np = fast_guided_filter(orig_rgb, a_np, radius=4, eps=1e-3)

    # 2. Análise do Fundo Original
    bg_info = analyze_image_background(orig_rgb)

    # 3. Eliminação de Halo Branco em Pelos e Juba (Lion Defringe)
    if defringe_white and (bg_info['is_white_bg'] or np.mean(orig_rgb) > 190):
        rgba_clean = decontaminate_white_fringe(orig_rgb, a_np, bg_val=255.0)
        curr_rgb = rgba_clean[:, :, :3]
        a_np = rgba_clean[:, :, 3]
    else:
        curr_rgb = np.dstack((np.array(r), np.array(g), np.array(b)))

    # 4. Aplica Choke DTF anti-rebarba
    if choke_px != 0:
        a_np = apply_mask_choke_or_expand(a_np, choke_px)

    # 5. Suavização de borda controlada
    if edge_smooth > 0.2:
        k_size = int(math.ceil(edge_smooth * 2)) | 1
        a_np = cv2.GaussianBlur(a_np, (k_size, k_size), edge_smooth)

    # 6. Decontaminação de cor geral da borda
    rgba_np = np.dstack((curr_rgb, a_np))
    rgba_np = decontaminate_edge_colors(rgba_np, a_np)
    out_img = Image.fromarray(rgba_np, mode="RGBA")

    # 7. Despill VFX Anti-Verde/Azul se fundo for chroma ou despill solicitado
    if despill or bg_info['is_green_bg'] or bg_info['is_blue_bg']:
        out_img = apply_chroma_despill_vfx(out_img, intensity=3.0)

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
# INTERFACE GRÁFICA PROFISSIONAL 2.6 (DARK THEME)
# =========================================================================

class RemovedorFundoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Separator - Removedor de Fundo Profissional 2.6 (VFX Anti-Verde & Anti-Halo Pelos)")
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

        # Modo de fundo do preview: 'checker' | 'black' | 'white' | 'dark' | 'order_fabric'
        self.preview_bg_mode = "checker"

        # Cor customizada para Chroma Key
        self.custom_chroma_color = (0, 255, 0)

        # Contexto de Pedidos e Clientes de Estamparia
        self.pedidos_carregados, self.clientes_carregados = load_estamparia_context()
        self.pedido_selecionado = None
        self.cor_tecido_preview = None
        self.var_ai_model = tk.StringVar(value="u2net")

        # Posições de desenho nos canvases para conversão do clique do conta-gotas
        self.orig_canvas_offset = (0, 0, 1, 1)

        # Construir UI
        self.setup_ui()

        # Pré-carregar sessão U2-Net leve em segundo plano
        threading.Thread(target=get_rembg_session, daemon=True).start()

        # Suporte a carregamento direto via argumento CLI (ex: vindo do Upscaler ou Corel)
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            try:
                img = Image.open(sys.argv[1])
                self.root.after(200, lambda: self.carregar_imagem(img, desc=os.path.basename(sys.argv[1])))
            except Exception:
                self.root.after(800, self.verificar_selecao_inicial_corel)
        else:
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
            text="Removedor de Fundo IA 2.6",
            font=("Segoe UI", 16, "bold"),
            fg="#10B981", # Emerald
            bg="#0B0F19"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_frame,
            text="IA U2-Net Leve & Rápida (⚡ GPU DirectML RTX Ativa), Guided Filter, Despill VFX, Anti-Halo Branco de Pelos e Choke DTF",
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

        # 1.1 Barra de Contexto de Pedido & Raio-X Diagnóstico de Estamparia
        ctx_frame = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=10, pady=6)
        ctx_frame.pack(fill=tk.X, pady=(0, 6))

        ctx_top = tk.Frame(ctx_frame, bg="#0F172A")
        ctx_top.pack(fill=tk.X)

        tk.Label(ctx_top, text="📦 Contexto do Pedido:", font=("Segoe UI", 8, "bold"), fg="#A78BFA", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 6))

        ped_list = ["-- Nenhum Pedido Vinculado (Modo Livre) --"]
        for p in self.pedidos_carregados:
            ped_list.append(f"#{p.get('numeroPedido', '?')} - {p.get('clienteNome', '')} ({p.get('corTecido', 'Camisa')} - {p.get('descricaoEstampa', '')[:20]})")

        self.cbo_pedidos = ttk.Combobox(ctx_top, values=ped_list, state="readonly", width=42, font=("Segoe UI", 8, "bold"))
        self.cbo_pedidos.current(0)
        self.cbo_pedidos.pack(side=tk.LEFT, padx=(0, 8))
        self.cbo_pedidos.bind("<<ComboboxSelected>>", self.on_pedido_selecionado)

        self.lbl_pedido_badge = tk.Label(ctx_top, text="", font=("Segoe UI", 8), fg="#CBD5E1", bg="#0F172A")
        self.lbl_pedido_badge.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_salvar_pasta_pedido = tk.Button(
            ctx_top,
            text="📁 Salvar na Pasta do Pedido",
            font=("Segoe UI", 8, "bold"),
            bg="#312E81",
            fg="#C7D2FE",
            activebackground="#4338CA",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=8,
            pady=3,
            command=self.salvar_na_pasta_do_pedido
        )
        self.btn_salvar_pasta_pedido.pack(side=tk.RIGHT)

        self.lbl_raio_x = tk.Label(
            ctx_frame,
            text="💡 Raio-X da Estampa: Carregue uma imagem para a IA analisar DPI, tamanho de estampa e sugerir o melhor modelo neural.",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="#0F172A",
            anchor="w"
        )
        self.lbl_raio_x.pack(fill=tk.X, pady=(4, 0))

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

        self.btn_bg_ord = tk.Button(bg_toggle_box, text="👕 Tecido Pedido", font=("Segoe UI", 7, "bold"), bg="#581C87", fg="#FFFFFF", bd=0, padx=6, pady=2, cursor="hand2", command=lambda: self.set_preview_bg("order_fabric"))
        # Inicialmente não empacotado até selecionar pedido com cor

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
            ("falso_png", "🏁 Falso PNG / Xadrez Web\n(Quadriculado do Google, Salva Logos & Remos)"),
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
            text="🚀 ENVIAR AO CORELDRAW",
            font=("Segoe UI", 10, "bold"),
            bg="#10B981", # Emerald
            fg="#FFFFFF",
            activebackground="#059669",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            pady=12,
            command=self.iniciar_remocao_corel
        )
        self.btn_remover_corel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        self.btn_upscaler = tk.Button(
            bottom_box,
            text="⚡ Upscale 4x IA",
            font=("Segoe UI", 8.5, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=12,
            command=self.abrir_no_upscaler
        )
        self.btn_upscaler.pack(side=tk.LEFT, padx=2)

        self.btn_vetorizar = tk.Button(
            bottom_box,
            text="📐 Vetorizar IA",
            font=("Segoe UI", 8.5, "bold"),
            bg="#312E81",
            fg="#C7D2FE",
            activebackground="#3730A3",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=12,
            command=self.abrir_no_vetorizador
        )
        self.btn_vetorizar.pack(side=tk.LEFT, padx=2)

        self.btn_salvar = tk.Button(
            bottom_box,
            text="💾 Salvar PNG",
            font=("Segoe UI", 8.5, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=12,
            command=self.salvar_png
        )
        self.btn_salvar.pack(side=tk.LEFT, padx=2)

        self.btn_copiar = tk.Button(
            bottom_box,
            text="📋 Copiar",
            font=("Segoe UI", 8.5, "bold"),
            bg="#1E293B",
            fg="#E2E8F0",
            activebackground="#334155",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=12,
            command=self.copiar_png_clipboard
        )
        self.btn_copiar.pack(side=tk.LEFT, padx=(2, 0))

        # Atalhos
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-v>", lambda e: self.colar_clipboard())
        self.root.bind("<Control-V>", lambda e: self.colar_clipboard())

    def abrir_no_upscaler(self):
        target = self.pil_processed if self.pil_processed is not None else self.pil_original
        if target is None:
            messagebox.showwarning("Aviso", "Carregue ou processe uma imagem primeiro!")
            return
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"os_cutout_for_upscaler_{int(time.time())}.png")
            target.save(tmp, format="PNG")
            py = "C:\\Python314\\pythonw.exe" if os.path.exists("C:\\Python314\\pythonw.exe") else "pythonw.exe"
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "upscaler_ai_app.py")
            import subprocess
            subprocess.Popen([py, script, tmp], creationflags=0x08000000)
            self.lbl_status.configure(text="Recorte enviado para o Upscaler IA Ultra HD!", fg="#38BDF8")
        except Exception as e:
            messagebox.showerror("Erro ao abrir no Upscaler", str(e))

    def abrir_no_vetorizador(self):
        target = self.pil_processed if self.pil_processed is not None else self.pil_original
        if target is None:
            messagebox.showwarning("Aviso", "Carregue ou processe uma imagem primeiro!")
            return
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"os_cutout_for_vetorizador_{int(time.time())}.png")
            target.save(tmp, format="PNG")
            py = "C:\\Python314\\pythonw.exe" if os.path.exists("C:\\Python314\\pythonw.exe") else "pythonw.exe"
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vetorizador_app.py")
            import subprocess
            subprocess.Popen([py, script, tmp], creationflags=0x08000000)
            self.lbl_status.configure(text="Recorte enviado para o Vetorizador IA!", fg="#818CF8")
        except Exception as e:
            messagebox.showerror("Erro ao abrir no Vetorizador", str(e))

    def on_pedido_selecionado(self, event=None):
        idx = self.cbo_pedidos.current()
        if idx <= 0:
            self.pedido_selecionado = None
            self.lbl_pedido_badge.configure(text="")
            self.btn_bg_ord.pack_forget()
            return

        pedido = self.pedidos_carregados[idx - 1]
        self.pedido_selecionado = pedido
        cliente_nome = pedido.get('clienteNome', 'Cliente')
        cor_tecido = (pedido.get('corTecido') or '').upper().strip()
        desc_estampa = pedido.get('descricaoEstampa', '')

        info_txt = f"Cliente: {cliente_nome} | Cor: {cor_tecido or 'Padrão'} | {pedido.get('totalPecas', '')} peças"
        self.lbl_pedido_badge.configure(text=info_txt, fg="#A78BFA")

        if cor_tecido in FABRIC_COLORS_MAP:
            self.cor_tecido_preview = FABRIC_COLORS_MAP[cor_tecido]
            self.btn_bg_ord.configure(text=f"👕 Tecido ({cor_tecido.title()})", state="normal")
            self.btn_bg_ord.pack(side=tk.LEFT, padx=1)
            is_dark = sum(self.cor_tecido_preview) < 320
            if is_dark:
                if hasattr(self, 'var_choke'):
                    self.var_choke.set(-1)
                if hasattr(self, 'var_defringe_white'):
                    self.var_defringe_white.set(True)
            else:
                if hasattr(self, 'var_choke'):
                    self.var_choke.set(0)
                if hasattr(self, 'var_defringe_white'):
                    self.var_defringe_white.set(False)
            self.set_preview_bg("order_fabric")
        else:
            self.cor_tecido_preview = None
            self.btn_bg_ord.pack_forget()

        if self.pil_original is None and pedido.get('imagens') and len(pedido['imagens']) > 0:
            first_img = pedido['imagens'][0]
            img_path = first_img.get('caminhoSalvo') or first_img.get('caminho')
            if img_path and os.path.isfile(img_path):
                try:
                    img = Image.open(img_path)
                    self.carregar_imagem(img, desc=f"Pedido #{pedido.get('numeroPedido')} - {os.path.basename(img_path)}")
                except Exception:
                    pass

    def salvar_na_pasta_do_pedido(self):
        if not self.pedido_selecionado:
            messagebox.showwarning("Aviso", "Selecione um pedido primeiro no seletor de contexto!")
            return
        if self.pil_processed is None:
            messagebox.showwarning("Aviso", "Nenhuma imagem recortada disponível para salvar!")
            return

        cliente_id = self.pedido_selecionado.get('clienteId')
        cliente = next((c for c in self.clientes_carregados if c.get('id') == cliente_id), None)
        pasta_dest = ""
        if cliente and cliente.get('pastaDiretorio') and os.path.exists(cliente['pastaDiretorio']):
            pasta_dest = cliente['pastaDiretorio']
        elif self.pedido_selecionado.get('clientePasta') and os.path.exists(self.pedido_selecionado['clientePasta']):
            pasta_dest = self.pedido_selecionado['clientePasta']

        if not pasta_dest:
            messagebox.showwarning("Aviso", "O cliente deste pedido não possui uma pasta válida cadastrada no sistema.")
            return

        num_ped = self.pedido_selecionado.get('numeroPedido', '0000')
        desc_limpa = re.sub(r'[\\/:*?"<>|]', '_', self.pedido_selecionado.get('descricaoEstampa', 'Arte')).strip()
        nome_arquivo = f"Arte_Recorte_#{num_ped}_{desc_limpa}_{int(time.time())}.png"
        caminho_final = os.path.join(pasta_dest, nome_arquivo)

        try:
            self.pil_processed.save(caminho_final, format="PNG")
            messagebox.showinfo("Salvo com Sucesso!", f"Arte recortada com IA salva diretamente na pasta do cliente:\n\n{caminho_final}")
            self.lbl_status.configure(text=f"Salvo na pasta do cliente: {nome_arquivo}", fg="#34D399")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def set_preview_bg(self, mode):
        self.preview_bg_mode = mode
        btns = [
            ("checker", self.btn_bg_chk),
            ("black", self.btn_bg_blk),
            ("white", self.btn_bg_wht),
            ("dark", self.btn_bg_drk),
            ("order_fabric", getattr(self, 'btn_bg_ord', None))
        ]
        for m, btn in btns:
            if btn is None:
                continue
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
            text="✅ Despill VFX Anti-Verde",
            variable=self.var_despill_vfx,
            font=("Segoe UI", 8, "bold"),
            fg="#10B981",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#10B981",
            command=self.agendar_preview_recalculo
        )
        cb_despill.pack(side=tk.LEFT, padx=(0, 6))

        # Filtro Anti-Halo Branco / Pelos e Juba de Leão
        if not hasattr(self, 'var_defringe_white'):
            self.var_defringe_white = tk.BooleanVar(value=True)
        cb_defringe = tk.Checkbutton(
            row_common,
            text="🦁 Anti-Halo Branco / Pelos",
            variable=self.var_defringe_white,
            font=("Segoe UI", 8, "bold"),
            fg="#F59E0B",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#F59E0B",
            command=self.agendar_preview_recalculo
        )
        cb_defringe.pack(side=tk.LEFT)

        # Divisor
        tk.Frame(self.pnl_params, bg="#334155", height=1).pack(fill=tk.X, pady=(0, 6))

        # Controles Específicos por Modo
        if mode in ("ia_geral", "alpha_suave"):
            row_models = tk.Frame(self.pnl_params, bg="#0F172A")
            row_models.pack(fill=tk.X, pady=(0, 6))

            tk.Label(row_models, text="🧠 Modelo de IA Neural:", font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 6))

            if not hasattr(self, 'var_ai_model'):
                self.var_ai_model = tk.StringVar(value="u2net")

            for m_key, m_info in SUPPORTED_AI_MODELS.items():
                rb_m = tk.Radiobutton(
                    row_models,
                    text=m_info["nome"],
                    variable=self.var_ai_model,
                    value=m_key,
                    font=("Segoe UI", 7.5, "bold"),
                    fg="#38BDF8",
                    bg="#0F172A",
                    selectcolor="#1E293B",
                    activebackground="#0F172A",
                    activeforeground="#38BDF8",
                    command=self.agendar_preview_recalculo
                )
                rb_m.pack(side=tk.LEFT, padx=2)

        if mode == "ia_geral":
            lbl_desc = tk.Label(
                self.pnl_params,
                text="Rede neural profunda com DirectML GPU RTX + Guided Filter e Despill VFX: recorta pessoas, fones, cabelos, produtos e cenários com velocidade instantânea e zero halos verdes ou brancos.",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A",
                wraplength=800,
                justify="left"
            )
            lbl_desc.pack(anchor="w", pady=(0, 4))

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

        elif mode == "falso_png":
            row_fp = tk.Frame(self.pnl_params, bg="#0F172A")
            row_fp.pack(fill=tk.X, pady=(0, 2))

            tk.Label(row_fp, text="Sensibilidade do Xadrez (10 a 60):", font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#0F172A").pack(side=tk.LEFT)
            if not hasattr(self, 'var_checker_tol'):
                self.var_checker_tol = tk.IntVar(value=30)
            scale_tol = tk.Scale(row_fp, from_=10, to=60, orient=tk.HORIZONTAL, variable=self.var_checker_tol, bg="#0F172A", fg="#FFFFFF", highlightthickness=0, length=240, troughcolor="#1E293B", command=lambda e: self.agendar_preview_recalculo())
            scale_tol.pack(side=tk.LEFT, padx=10)

            lbl_fp_desc = tk.Label(
                self.pnl_params,
                text="Elimina 100% do xadrez falso da web/Google Images a partir das bordas externas. Salva remos, âncoras e detalhes finos sem apagar o interior do logo.",
                font=("Segoe UI", 8),
                fg="#94A3B8",
                bg="#0F172A"
            )
            lbl_fp_desc.pack(anchor="w")

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
                text="Modo Alpha Matting com Guided Filter O(1): transição ultra suave para pelos de leão, animais, cabelos finos, tecidos e vidro, com eliminação ativa de névoas e halos brancos.",
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

            # Raio-X Contextual Inteligente da Estampa
            try:
                diag = analyze_image_context(pil_img)
                diag_txt = f"🔍 Raio-X: {diag['dim_px']} ({diag['dim_cm']}) • {diag['classificacao']} • Sugestão IA: {diag['motivo']}"
                if diag['alerta']:
                    diag_txt += f" | {diag['alerta']}"
                self.lbl_raio_x.configure(text=diag_txt, fg="#38BDF8")
            except Exception:
                pass

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
        elif mode == "order_fabric":
            bg_col = self.cor_tecido_preview if self.cor_tecido_preview else (88, 28, 135)
            bg = Image.new("RGB", (tw, th), bg_col)
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
            ai_model = self.var_ai_model.get() if hasattr(self, 'var_ai_model') else 'u2net'
            feather = float(self.var_feather.get()) if hasattr(self, 'var_feather') else 0.8
            choke = int(self.var_choke.get()) if hasattr(self, 'var_choke') else -1
            despill = self.var_despill_vfx.get() if hasattr(self, 'var_despill_vfx') else True
            defringe = self.var_defringe_white.get() if hasattr(self, 'var_defringe_white') else True

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
                res = remove_ai_semantic(proc_input, model_name=ai_model, alpha_matting=False, post_process=post_p, edge_smooth=feather, choke_px=choke, despill=despill, defringe_white=defringe)
            elif mode == "falso_png":
                tol = self.var_checker_tol.get() if hasattr(self, 'var_checker_tol') else 30
                res = remove_fake_png_checkerboard(proc_input, tolerance=tol, edge_feather=feather, choke_px=choke)
            elif mode == "fundo_branco":
                tol = self.var_white_tol.get() if hasattr(self, 'var_white_tol') else 28
                res = remove_white_background_floodfill(proc_input, tolerance=tol, edge_feather=feather, choke_px=choke, defringe=defringe)
            elif mode == "chroma_key":
                tol = self.var_chroma_tol.get() if hasattr(self, 'var_chroma_tol') else 48
                res = remove_chroma_key(proc_input, key_color=self.custom_chroma_color, tolerance=tol, feather=feather, despill=despill, choke_px=choke)
            elif mode == "alpha_suave":
                res = remove_ai_semantic(proc_input, model_name=ai_model, alpha_matting=True, post_process=False, edge_smooth=feather, choke_px=choke, despill=despill, defringe_white=defringe)
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
            opt.SizeX = 1600
            opt.SizeY = 1600
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
            ai_model = self.var_ai_model.get() if hasattr(self, 'var_ai_model') else 'u2net'
            feather = float(self.var_feather.get()) if hasattr(self, 'var_feather') else 0.8
            choke = int(self.var_choke.get()) if hasattr(self, 'var_choke') else -1
            despill = self.var_despill_vfx.get() if hasattr(self, 'var_despill_vfx') else True
            defringe = self.var_defringe_white.get() if hasattr(self, 'var_defringe_white') else True
            full_img = self.pil_original

            if mode == "ia_geral":
                post_p = self.var_post_process.get() if hasattr(self, 'var_post_process') else True
                res = remove_ai_semantic(full_img, model_name=ai_model, alpha_matting=False, post_process=post_p, edge_smooth=feather, choke_px=choke, despill=despill, defringe_white=defringe)
            elif mode == "falso_png":
                tol = self.var_checker_tol.get() if hasattr(self, 'var_checker_tol') else 30
                res = remove_fake_png_checkerboard(full_img, tolerance=tol, edge_feather=feather, choke_px=choke)
            elif mode == "fundo_branco":
                tol = self.var_white_tol.get() if hasattr(self, 'var_white_tol') else 28
                res = remove_white_background_floodfill(full_img, tolerance=tol, edge_feather=feather, choke_px=choke, defringe=defringe)
            elif mode == "chroma_key":
                tol = self.var_chroma_tol.get() if hasattr(self, 'var_chroma_tol') else 48
                res = remove_chroma_key(full_img, key_color=self.custom_chroma_color, tolerance=tol, feather=feather, despill=despill, choke_px=choke)
            elif mode == "alpha_suave":
                res = remove_ai_semantic(full_img, model_name=ai_model, alpha_matting=True, post_process=False, edge_smooth=feather, choke_px=choke, despill=despill, defringe_white=defringe)
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
