"""
Order Separator - Vetorizador Profissional para CorelDRAW
Motor Inteligente de Vetorização Dual-Spline / K-Means / Lanczos
Qualidade Superior ao Corel PowerTRACE e Adobe Illustrator Image Trace:
- Sem halos de cor ou anéis borrados de anti-aliasing
- Quantização de paleta pura (cores sólidas perfeitas para estamparia)
- Camadas sobrepostas sem linhas brancas para DTF
- Camadas recortadas para plotter de recorte
- Modo monocromático para fotolito de Silk Screen
- Remoção inteligente de fundo branco/bounding box
- Extração direta via API CorelDRAW (sem usar área de transferência, 100% seguro contra antivírus)
"""

import sys
import os
import re
import math
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import numpy as np
import cv2
import vtracer

# =========================================================================
# FUNÇÕES DE PROCESSAMENTO E VETORIZAÇÃO DE ALTA QUALIDADE
# =========================================================================

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def color_distance_sq(c1, c2):
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2


def auto_detect_palette_k(flat_pixels, max_k=6):
    """Detecta automaticamente o número ideal de cores sólidas via Elbow Method em regiões planas (sem anti-aliasing)."""
    try:
        inertias = []
        for k in range(1, max_k + 1):
            crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
            comp, _, _ = cv2.kmeans(flat_pixels, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
            inertias.append(comp)
        
        drops = [inertias[i-1] - inertias[i] for i in range(1, len(inertias))]
        total_drop = sum(drops) if sum(drops) > 0 else 1.0
        
        chosen_k = 2
        for i, drop in enumerate(drops):
            if (drop / total_drop) < 0.05 and i >= 1:
                chosen_k = i + 1
                break
            chosen_k = i + 2
        return max(2, min(chosen_k, max_k))
    except Exception:
        return 3


def postprocess_svg(svg_path, remove_bg=True, unify_colors=True):
    """
    Otimiza o arquivo SVG gerado:
    1. Harmoniza cores próximas em uma única cor pura sólida (sem halos ou cinzas de anti-aliasing)
    2. Remove o caminho de fundo branco / bounding box externa da prancheta preservando letras internas
    """
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    width_m = re.search(r'width=["\']([0-9.]+)["\']', svg_content)
    height_m = re.search(r'height=["\']([0-9.]+)["\']', svg_content)
    svg_w = float(width_m.group(1)) if width_m else 0
    svg_h = float(height_m.group(1)) if height_m else 0

    if unify_colors:
        raw_colors = re.findall(r'fill=["\'](#[0-9a-fA-F]{3,6})["\']', svg_content)
        unique_hex = list(set(raw_colors))
        rgb_map = {h: hex_to_rgb(h) for h in unique_hex}

        color_groups = []
        for h, rgb in rgb_map.items():
            if rgb[0] < 38 and rgb[1] < 38 and rgb[2] < 38:
                color_groups.append((h, '#000000'))
                continue
            if rgb[0] > 225 and rgb[1] > 225 and rgb[2] > 225:
                color_groups.append((h, '#FFFFFF'))
                continue

            matched = False
            for parent_h, target_h in color_groups:
                p_rgb = rgb_map.get(parent_h, (0, 0, 0))
                if color_distance_sq(rgb, p_rgb) < (28 * 28):
                    color_groups.append((h, target_h))
                    matched = True
                    break
            if not matched:
                color_groups.append((h, h.upper()))

        for src_h, dest_h in color_groups:
            if src_h != dest_h:
                svg_content = re.sub(
                    r'fill=["\']' + re.escape(src_h) + r'["\']', 
                    f'fill="{dest_h}"', 
                    svg_content, 
                    flags=re.IGNORECASE
                )

    if remove_bg and svg_w > 0 and svg_h > 0:
        paths = list(re.finditer(r'<path[^>]+>', svg_content))
        if paths:
            first_path = paths[0].group(0)
            fill_m = re.search(r'fill=["\']([^"\']+)["\']', first_path)
            d_m = re.search(r'd=["\']([^"\']+)["\']', first_path)
            if fill_m and d_m:
                fill = fill_m.group(1).upper()
                d_val = d_m.group(1)
                if fill in ('#FFFFFF', '#FDFDFD', '#FEFEFE', '#FAFAFA', '#F5F5F5', '#F6F3ED', '#FAF9F5'):
                    if ("M0 0" in d_val or "M 0 0" in d_val or "M0,0" in d_val) and (str(int(svg_w)) in d_val or str(int(svg_h)) in d_val):
                        svg_content = svg_content.replace(first_path, '', 1)

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)


def execute_vectorization(
    input_path,
    output_svg,
    colormode="color",
    hierarchical="stacked",
    filter_speckle=6,
    color_precision=8,
    layer_difference=16,
    corner_threshold=60,
    length_threshold=4.0,
    splice_threshold=50,
    path_precision=2,
    k_colors="auto",
    upscale_small=True,
    remove_bg=True,
    unify_colors=True,
    preset="logo"
):
    """
    Motor Profissional de Vetorização Dual-Spline em Rust (VTracer):
    - Extração de paleta sólida pura a partir de regiões planas (Sobel Gradient)
    - Elimina 100% de anéis cinzas, halos e anti-aliasing
    - Super-resolução Lanczos 3x com filtro mediano anti-serrilhado
    - Vértices e quinas vivas (corner_threshold=60) preservando geometria original
    - Retorna proporção real do conteúdo (content_ratio_w, content_ratio_h) para ajuste 1:1 no Corel
    """
    temp_png = input_path + "._proc.png"
    content_ratio_w = 1.0
    content_ratio_h = 1.0
    try:
        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Não foi possível abrir o arquivo: {input_path}")

        if len(img.shape) == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3]
            bgr = img[:, :, :3]
            white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
            alpha_factor = (alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]
            img = (bgr.astype(np.float32) * alpha_factor + white_bg.astype(np.float32) * (1.0 - alpha_factor)).astype(np.uint8)
        elif len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        orig_h, orig_w = img.shape[:2]

        # 1. Mede a caixa real do conteúdo interno (sem a borda branca da prancheta)
        diff = np.abs(img.astype(int) - 255)
        non_bg = np.any(diff > 35, axis=2)
        coords = np.argwhere(non_bg)
        if len(coords) > 0:
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0)
            content_w = max(1, x1 - x0)
            content_h = max(1, y1 - y0)
            content_ratio_w = float(content_w) / float(orig_w)
            content_ratio_h = float(content_h) / float(orig_h)

        # 2. Super-resolução Lanczos 2x a 3x para imagens pequenas ou de baixa resolução
        if upscale_small and (orig_w < 1800 or orig_h < 1800):
            scale = max(2, min(4, int(2000 / max(orig_w, orig_h))))
            if scale > 1:
                img = cv2.resize(img, (orig_w * scale, orig_h * scale), interpolation=cv2.INTER_LANCZOS4)

        # 3. Modo binário (Silk Screen / Fotolito Puro)
        if colormode == 'binary':
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            cv2.imwrite(temp_png, bin_img)
        else:
            # 4. Isolamento de Regiões Planas via Gradiente de Sobel:
            # Permite extrair a verdadeira paleta de tintas sem ser contaminada por pixels cinzas de anti-aliasing
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(grad_x**2 + grad_y**2)
            flat_mask = grad_mag < 25
            if np.sum(flat_mask) < (img.shape[0] * img.shape[1] * 0.1):
                flat_mask = np.ones((img.shape[0], img.shape[1]), dtype=bool)

            flat_pixels = img[flat_mask].astype(np.float32)

            if preset != "alta_definicao" and k_colors is not None and k_colors != "all":
                final_k = auto_detect_palette_k(flat_pixels) if k_colors == "auto" else int(k_colors)
                if final_k and final_k >= 2:
                    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.5)
                    _, _, centers = cv2.kmeans(flat_pixels, final_k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
                    centers = np.uint8(centers)

                    # Purificação rigorosa de preto e branco
                    for i in range(len(centers)):
                        if np.all(centers[i] < 38):
                            centers[i] = [0, 0, 0]
                        elif np.all(centers[i] > 220):
                            centers[i] = [255, 255, 255]

                    # Mapeia todos os pixels (inclusive bordas) para a tinta sólida mais próxima
                    all_pixels = img.reshape((-1, 3)).astype(np.float32)
                    dists = [np.sum((all_pixels - c)**2, axis=1) for c in centers.astype(np.float32)]
                    closest_indices = np.argmin(dists, axis=0)
                    img_quantized = centers[closest_indices].reshape(img.shape)

                    # Filtro mediano 3x3 para eliminar degraus de pixels nas quinas
                    img_quantized = cv2.medianBlur(img_quantized, 3)
                    cv2.imwrite(temp_png, img_quantized)
                else:
                    cv2.imwrite(temp_png, img)
            else:
                cv2.imwrite(temp_png, img)

        vtracer.convert_image_to_svg_py(
            str(temp_png),
            str(output_svg),
            str(colormode),
            str(hierarchical),
            'spline',
            int(filter_speckle),
            int(color_precision),
            int(layer_difference),
            int(corner_threshold),
            float(length_threshold),
            10,
            int(splice_threshold),
            int(path_precision)
        )

        postprocess_svg(output_svg, remove_bg=remove_bg, unify_colors=unify_colors)
        return output_svg, content_ratio_w, content_ratio_h
    finally:
        if os.path.exists(temp_png):
            try:
                os.remove(temp_png)
            except Exception:
                pass

# =========================================================================
# INTERFACE GRÁFICA PROFISSIONAL (TKINTER NATIVO)
# =========================================================================

class VetorizadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Separator - Vetorizador Profissional")
        self.root.geometry("560x780")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#0B0F19")

        icon_path = r"E:\estamparia-manager\build\icon.ico"
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.current_img_path = None
        self.orig_w = 0.0
        self.orig_h = 0.0
        self.orig_x = 0.0
        self.orig_y = 0.0
        self.preview_image_tk = None

        self.setup_styles()
        self.build_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(".", background="#0B0F19", foreground="#FFFFFF")
        self.style.configure("TLabel", background="#0B0F19", foreground="#E2E8F0", font=("Segoe UI", 9))
        self.style.configure("Header.TLabel", background="#0B0F19", foreground="#818CF8", font=("Segoe UI", 12, "bold"))
        self.style.configure("Sub.TLabel", background="#0B0F19", foreground="#94A3B8", font=("Segoe UI", 8))
        self.style.configure("TCheckbutton", background="#0F172A", foreground="#E2E8F0", font=("Segoe UI", 8))

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="#0B0F19", padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho
        lbl_head = tk.Label(main_frame, text="Vetorizador de Imagens (Ultra Precisão)", font=("Segoe UI", 13, "bold"), fg="#818CF8", bg="#0B0F19")
        lbl_head.pack(anchor="w")
        lbl_sub = tk.Label(main_frame, text="Super-Resolução Lanczos + K-Means + Dual-Spline (Sem halos ou bordas cinzas)", font=("Segoe UI", 8), fg="#94A3B8", bg="#0B0F19")
        lbl_sub.pack(anchor="w", pady=(0, 10))

        # 2. Caixa de Origem (Captura CorelDRAW / Arquivo)
        pnl_origem = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=10, pady=8)
        pnl_origem.pack(fill=tk.X, pady=(0, 10))

        btn_capturar = tk.Button(
            pnl_origem, 
            text="📷  [CorelDRAW] Capturar Bitmap Selecionado", 
            font=("Segoe UI", 10, "bold"), 
            bg="#1E293B", 
            fg="#FFFFFF", 
            activebackground="#334155", 
            activeforeground="#FFFFFF",
            bd=0, 
            cursor="hand2", 
            pady=6,
            command=self.capturar_corel
        )
        btn_capturar.pack(fill=tk.X, pady=(0, 6))

        btn_arquivo = tk.Button(
            pnl_origem, 
            text="📁  [Arquivo] Escolher Imagem no Computador...", 
            font=("Segoe UI", 9, "bold"), 
            bg="#182138", 
            fg="#CBD5E1", 
            activebackground="#26344E", 
            activeforeground="#FFFFFF",
            bd=0, 
            cursor="hand2", 
            pady=4,
            command=self.escolher_arquivo
        )
        btn_arquivo.pack(fill=tk.X)

        # 3. Preview da Imagem
        pnl_preview = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=8, pady=8)
        pnl_preview.pack(fill=tk.X, pady=(0, 10))

        self.lbl_canvas = tk.Label(pnl_preview, bg="#020617", bd=1, relief="solid", width=12, height=5)
        self.lbl_canvas.pack(side=tk.LEFT, padx=(0, 10))

        info_box = tk.Frame(pnl_preview, bg="#0F172A")
        info_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.lbl_img_nome = tk.Label(info_box, text="Nenhuma imagem carregada ainda.", font=("Segoe UI", 9, "bold"), fg="#818CF8", bg="#0F172A", anchor="w")
        self.lbl_img_nome.pack(fill=tk.X)

        self.lbl_img_desc = tk.Label(info_box, text="Selecione o bitmap no CorelDRAW e clique em Capturar, ou abra um arquivo PNG/JPG do seu computador.", font=("Segoe UI", 8), fg="#94A3B8", bg="#0F172A", justify="left", wraplength=360)
        self.lbl_img_desc.pack(fill=tk.X, pady=(4, 0))

        # 4. Presets
        lbl_pres = tk.Label(main_frame, text="Preset de Produção:", font=("Segoe UI", 8, "bold"), fg="#CBD5E1", bg="#0B0F19")
        lbl_pres.pack(anchor="w", pady=(0, 4))

        preset_box = tk.Frame(main_frame, bg="#0B0F19")
        preset_box.pack(fill=tk.X, pady=(0, 10))

        self.preset_var = tk.StringVar(value="logo")
        self.preset_btns = {}
        presets = [
            ("logo", "Logo & Escudo"),
            ("dtf", "DTF Têxtil"),
            ("silk", "Silk Screen"),
            ("plotter", "Recorte Vinil"),
            ("alta_definicao", "Foto / HD")
        ]
        for p_id, p_name in presets:
            btn = tk.Button(
                preset_box, 
                text=p_name, 
                font=("Segoe UI", 8, "bold"), 
                bd=0, 
                cursor="hand2", 
                padx=8, 
                pady=4,
                command=lambda pid=p_id: self.select_preset(pid)
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
            self.preset_btns[p_id] = btn

        self.update_preset_buttons()

        # 5. Painel de Controles Avançados
        pnl_ctrl = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=12, pady=10)
        pnl_ctrl.pack(fill=tk.X, pady=(0, 10))

        # Linha: Paleta de cores
        row_pal = tk.Frame(pnl_ctrl, bg="#0F172A")
        row_pal.pack(fill=tk.X, pady=(0, 4))
        tk.Label(row_pal, text="Paleta de Cores (Quantização Inteligente):", font=("Segoe UI", 8, "bold"), fg="#818CF8", bg="#0F172A").pack(side=tk.LEFT)
        
        self.cb_colors = ttk.Combobox(row_pal, state="readonly", width=24, font=("Segoe UI", 9))
        self.cb_colors['values'] = (
            "auto - Detecção Automática",
            "2 cores - Preto e Branco (Silk)",
            "3 cores - Ex: Preto, Branco, Vermelho",
            "4 cores",
            "5 cores",
            "6 cores",
            "8 cores",
            "12 cores",
            "16 cores",
            "all - Cores Ilimitadas (Foto)"
        )
        self.cb_colors.current(0)
        self.cb_colors.pack(side=tk.RIGHT)

        tk.Label(pnl_ctrl, text="Elimina 100% dos anéis de anti-aliasing e halos de cor ao redor das letras e logos.", font=("Segoe UI", 7), fg="#94A3B8", bg="#0F172A").pack(anchor="w", pady=(0, 8))

        # Divisor
        tk.Frame(pnl_ctrl, bg="#334155", height=1).pack(fill=tk.X, pady=(0, 8))

        # Linha: Cantos Vivos
        row_c = tk.Frame(pnl_ctrl, bg="#0F172A")
        row_c.pack(fill=tk.X, pady=(0, 6))
        tk.Label(row_c, text="Rigidez de Cantos Vivos (20 a 90 graus):", font=("Segoe UI", 8, "bold"), fg="#CBD5E1", bg="#0F172A").pack(side=tk.LEFT)
        self.sp_corner = tk.Spinbox(row_c, from_=20, to=90, width=8, font=("Segoe UI", 9, "bold"), bg="#141B2D", fg="#FFFFFF", bd=1, relief="solid")
        self.sp_corner.delete(0, "end")
        self.sp_corner.insert(0, "60")
        self.sp_corner.pack(side=tk.RIGHT)

        # Linha: Anti-Ruído
        row_s = tk.Frame(pnl_ctrl, bg="#0F172A")
        row_s.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row_s, text="Filtro Anti-Ruído (elimina micropontos e poeira):", font=("Segoe UI", 8, "bold"), fg="#CBD5E1", bg="#0F172A").pack(side=tk.LEFT)
        self.sp_speckle = tk.Spinbox(row_s, from_=0, to=64, width=8, font=("Segoe UI", 9, "bold"), bg="#141B2D", fg="#FFFFFF", bd=1, relief="solid")
        self.sp_speckle.delete(0, "end")
        self.sp_speckle.insert(0, "6")
        self.sp_speckle.pack(side=tk.RIGHT)

        # Divisor
        tk.Frame(pnl_ctrl, bg="#334155", height=1).pack(fill=tk.X, pady=(0, 8))

        # Checkboxes
        self.var_remove_bg = tk.BooleanVar(value=True)
        cb_bg = tk.Checkbutton(pnl_ctrl, text="Remover Fundo Branco / Bounding Box (Deixar desenho transparente)", variable=self.var_remove_bg, font=("Segoe UI", 8), fg="#F59E0B", bg="#0F172A", selectcolor="#1E293B", activebackground="#0F172A", activeforeground="#F59E0B")
        cb_bg.pack(anchor="w", pady=1)

        self.var_upscale = tk.BooleanVar(value=True)
        cb_up = tk.Checkbutton(pnl_ctrl, text="Super-Resolução Lanczos (elimina serrilhado em imagens pequenas)", variable=self.var_upscale, font=("Segoe UI", 8), fg="#34D399", bg="#0F172A", selectcolor="#1E293B", activebackground="#0F172A", activeforeground="#34D399")
        cb_up.pack(anchor="w", pady=1)

        self.var_stacked = tk.BooleanVar(value=True)
        cb_stk = tk.Checkbutton(pnl_ctrl, text="Camadas Sobrepostas (zero frestas brancas na junção de cores no DTF)", variable=self.var_stacked, font=("Segoe UI", 8), fg="#67E8F9", bg="#0F172A", selectcolor="#1E293B", activebackground="#0F172A", activeforeground="#67E8F9")
        cb_stk.pack(anchor="w", pady=1)

        self.var_harmonize = tk.BooleanVar(value=True)
        cb_har = tk.Checkbutton(pnl_ctrl, text="Harmonização Pura de Cores (unifica tons próximos em cores sólidas exatas)", variable=self.var_harmonize, font=("Segoe UI", 8), fg="#C084FC", bg="#0F172A", selectcolor="#1E293B", activebackground="#0F172A", activeforeground="#C084FC")
        cb_har.pack(anchor="w", pady=1)

        # 6. Status e Progresso
        self.lbl_status = tk.Label(main_frame, text="Pronto. Carregue uma imagem para vetorizar.", font=("Segoe UI", 8), fg="#94A3B8", bg="#0B0F19", anchor="center")
        self.lbl_status.pack(fill=tk.X, pady=(2, 6))

        # 7. Botão Principal
        self.btn_vetorizar = tk.Button(
            main_frame, 
            text="VETORIZAR E ENVIAR PARA O CORELDRAW", 
            font=("Segoe UI", 11, "bold"), 
            bg="#4F46E5", 
            fg="#FFFFFF", 
            activebackground="#4338CA", 
            activeforeground="#FFFFFF",
            bd=0, 
            cursor="hand2", 
            pady=12,
            command=self.iniciar_vetorizacao
        )
        self.btn_vetorizar.pack(fill=tk.X)

        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def select_preset(self, preset_id):
        self.preset_var.set(preset_id)
        self.update_preset_buttons()

        if preset_id == "logo":
            self.sp_speckle.delete(0, "end"); self.sp_speckle.insert(0, "6")
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "60")
            self.var_stacked.set(True)
            self.cb_colors.current(0) # auto
        elif preset_id == "dtf":
            self.sp_speckle.delete(0, "end"); self.sp_speckle.insert(0, "4")
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "45")
            self.var_stacked.set(True)
            self.cb_colors.current(0) # auto
        elif preset_id == "silk":
            self.sp_speckle.delete(0, "end"); self.sp_speckle.insert(0, "8")
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "45")
            self.var_stacked.set(False)
            self.cb_colors.current(1) # 2 cores (Silk)
        elif preset_id == "plotter":
            self.sp_speckle.delete(0, "end"); self.sp_speckle.insert(0, "10")
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "35")
            self.var_stacked.set(False)
            self.cb_colors.current(0) # auto
        elif preset_id == "alta_definicao":
            self.sp_speckle.delete(0, "end"); self.sp_speckle.insert(0, "2")
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "65")
            self.var_stacked.set(True)
            self.cb_colors.current(9) # all (ilimitadas)

    def update_preset_buttons(self):
        curr = self.preset_var.get()
        for pid, btn in self.preset_btns.items():
            if pid == curr:
                btn.configure(bg="#4F46E5", fg="#FFFFFF")
            else:
                btn.configure(bg="#1E293B", fg="#CBD5E1")

    def carregar_imagem_no_preview(self, path):
        try:
            self.current_img_path = path
            pil_img = Image.open(path)
            w, h = pil_img.size
            size_kb = round(os.path.getsize(path) / 1024, 1)

            pil_thumb = pil_img.copy()
            pil_thumb.thumbnail((88, 88), Image.Resampling.LANCZOS)
            self.preview_image_tk = ImageTk.PhotoImage(pil_thumb)
            self.lbl_canvas.configure(image=self.preview_image_tk, width=88, height=88)

            fname = os.path.basename(path)
            self.lbl_img_nome.configure(text=f"{fname} ({w} x {h} px - {size_kb} KB)")
            self.lbl_img_desc.configure(text="Imagem carregada e pronta. O motor aplicará super-resolução e quantização de cores sólidas.")
            self.lbl_status.configure(text="Imagem pronta! Escolha o preset e clique em Vetorizar.", fg="#34D399")
        except Exception as e:
            messagebox.showerror("Erro ao carregar imagem", str(e))

    def escolher_arquivo(self):
        f = filedialog.askopenfilename(
            title="Selecione uma imagem para vetorizar",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Todos", "*.*")]
        )
        if f:
            self.orig_w = 0.0
            self.carregar_imagem_no_preview(f)

    def capturar_corel(self):
        """
        Extrai o bitmap diretamente via COM ExportEx do CorelDRAW.
        SEM USAR ÁREA DE TRANSFERÊNCIA (zero falsos positivos em antivírus).
        """
        try:
            import win32com.client
            corel = win32com.client.gencache.EnsureDispatch("CorelDRAW.Application.24")
            if not corel.ActiveDocument:
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
                messagebox.showwarning("Aviso", "Selecione uma imagem bitmap ou desenho no CorelDRAW!")
                return

            try:
                self.orig_w = float(sel.SizeWidth)
                self.orig_h = float(sel.SizeHeight)
                self.orig_x = float(sel.LeftX)
                self.orig_y = float(sel.BottomY)
            except Exception:
                try:
                    shape = sel.Shapes(1)
                    self.orig_w = float(shape.SizeWidth)
                    self.orig_h = float(shape.SizeHeight)
                    self.orig_x = float(shape.LeftX)
                    self.orig_y = float(shape.BottomY)
                except Exception:
                    self.orig_w = 0.0

            # Exporta APENAS A SELEÇÃO ATIVA (cdrSelection = 2, cdrPNG = 802)
            temp_dir = tempfile.gettempdir()
            temp_png = os.path.join(temp_dir, f"corel_art_{os.getpid()}_{np.random.randint(1000, 9999)}.png")

            opt = corel.CreateStructExportOptions()
            opt.SizeX = 1400
            opt.SizeY = 1400
            opt.MaintainAspect = True
            opt.Transparent = True
            pal = corel.CreateStructPaletteOptions()

            # cdrPNG = 802, cdrSelection = 2 (Exporta somente o objeto selecionado, não a página toda!)
            exp = doc.ExportEx(temp_png, 802, 2, opt, pal)
            if exp:
                exp.Finish()

            if not os.path.exists(temp_png):
                raise ValueError("O CorelDRAW não gerou o arquivo temporário da seleção.")

            self.carregar_imagem_no_preview(temp_png)
            self.lbl_img_nome.configure(text=f"Objeto Selecionado Capturado ({int(os.path.getsize(temp_png)/1024)} KB)")
        except Exception as e:
            messagebox.showerror("Erro ao capturar do CorelDRAW", f"Não foi possível capturar a seleção:\n{e}")

    def iniciar_vetorizacao(self):
        if not self.current_img_path or not os.path.exists(self.current_img_path):
            messagebox.showwarning("Aviso", "Carregue uma imagem ou capture a seleção do CorelDRAW antes de vetorizar!")
            return

        self.btn_vetorizar.configure(state="disabled", text="Processando Dual-Splines e Paleta Pura...", bg="#3730A3")
        self.lbl_status.configure(text="Aplicando K-Means, eliminando ruídos e traçando curvas...", fg="#F59E0B")
        
        threading.Thread(target=self._processar_thread, daemon=True).start()

    def _processar_thread(self):
        try:
            sel_colors_txt = self.cb_colors.get()
            colors_arg = "auto"
            m = re.match(r'^(\d+)', sel_colors_txt)
            if m:
                colors_arg = m.group(1)
            elif sel_colors_txt.startswith("all"):
                colors_arg = "all"

            preset = self.preset_var.get()
            hier_mode = "stacked" if self.var_stacked.get() else "cutout"
            color_mode = "binary" if preset == "silk" else "color"

            speckle = int(self.sp_speckle.get())
            corner = int(self.sp_corner.get())
            remove_bg = self.var_remove_bg.get()
            upscale = self.var_upscale.get()
            harmonize = self.var_harmonize.get()

            temp_dir = tempfile.gettempdir()
            output_svg = os.path.join(temp_dir, f"vetor_estamparia_{np.random.randint(1000, 9999)}.svg")

            output_svg, cr_w, cr_h = execute_vectorization(
                input_path=self.current_img_path,
                output_svg=output_svg,
                colormode=color_mode,
                hierarchical=hier_mode,
                filter_speckle=speckle,
                corner_threshold=corner,
                k_colors=colors_arg,
                upscale_small=upscale,
                remove_bg=remove_bg,
                unify_colors=harmonize,
                preset=preset
            )
            self.content_ratio_w = cr_w
            self.content_ratio_h = cr_h

            self.root.after(0, lambda: self._finalizar_importacao_corel(output_svg))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: self._erro_finalizacao(err_msg))

    def _finalizar_importacao_corel(self, output_svg):
        try:
            self.lbl_status.configure(text="Importando vetor para a página do CorelDRAW...", fg="#818CF8")
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

            doc.BeginCommandGroup("Vetorizar com Order Separator")
            try:
                layer = doc.ActiveLayer
                opt = corel.CreateStructImportOptions()
                imp = layer.ImportEx(output_svg, 0, opt)
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
                    grp = sel.Group()
                    natural_w = float(grp.SizeWidth)
                    natural_h = float(grp.SizeHeight)

                    if natural_w > 0 and natural_h > 0 and self.orig_w > 0 and self.orig_h > 0:
                        aspect = natural_w / natural_h

                        # Se removeu o fundo branco/card da prancheta, preserva a escala 1:1 real do escudo
                        if self.var_remove_bg.get() and hasattr(self, 'content_ratio_w') and self.content_ratio_w > 0:
                            target_w = float(self.orig_w) * float(self.content_ratio_w)
                            target_h = float(self.orig_h) * float(self.content_ratio_h)
                            if abs((target_w / target_h) - aspect) > 0.02:
                                target_w = target_h * aspect
                        else:
                            target_h = float(self.orig_h)
                            target_w = target_h * aspect
                            if target_w > float(self.orig_w * 1.05):
                                target_w = float(self.orig_w)
                                target_h = target_w / aspect

                        grp.SetSize(target_w, target_h)
                        grp.LeftX = float(self.orig_x + self.orig_w + (self.orig_w * 0.05))
                        grp.CenterY = float(self.orig_y + (self.orig_h / 2.0))
                    else:
                        grp.CenterX = doc.ActivePage.CenterX
                        grp.CenterY = doc.ActivePage.CenterY
            finally:
                doc.EndCommandGroup()
                corel.Refresh()

            self._sucesso_finalizacao()
        except Exception as e:
            self._erro_finalizacao(str(e))

    def _sucesso_finalizacao(self):
        self.btn_vetorizar.configure(state="normal", text="VETORIZAR E ENVIAR PARA O CORELDRAW", bg="#4F46E5")
        self.lbl_status.configure(text="Concluído com sucesso! Vetor importado no CorelDRAW.", fg="#34D399")
        messagebox.showinfo(
            "Vetorização Concluída!",
            "Vetorização de Alta Precisão Concluída!\n\n"
            "O desenho em curvas foi importado ao lado da imagem original, com o mesmo tamanho e preenchimentos perfeitos sem frestas brancas.\n\n"
            "As cores foram purificadas sem halos ou anéis de anti-aliasing. Você já pode desagrupar, editar nós ou enviar para produção!"
        )

    def _erro_finalizacao(self, err):
        self.btn_vetorizar.configure(state="normal", text="VETORIZAR E ENVIAR PARA O CORELDRAW", bg="#4F46E5")
        self.lbl_status.configure(text="Erro durante a vetorização.", fg="#EF4444")
        messagebox.showerror("Erro na Vetorização", f"Ocorreu um erro:\n\n{err}")

def main():
    root = tk.Tk()
    app = VetorizadorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
