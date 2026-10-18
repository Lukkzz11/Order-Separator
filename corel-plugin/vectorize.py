"""
Order Separator - Motor Profissional de Vetorização de Imagens
Qualidade Superior ao Corel PowerTRACE e Adobe Illustrator Image Trace:
- Super-resolução e filtro bilateral para eliminação total de halos e anéis de anti-aliasing
- Quantização K-Means de Paleta: agrupa milhares de pixels degradê em cores sólidas puras
- Suporte a DTF (camadas stacked sem frestas brancas) e Plotter/Silk (camadas cutout)
- Remoção inteligente de fundo branco/bounding box
- Harmonização de cores no SVG (unificação de tons próximos em uma única cor pura)
"""

import sys
import os
import argparse
import re
import math
import numpy as np
import cv2
from PIL import Image

def auto_detect_palette_k(img_bgr, max_k=8):
    """Detecta automaticamente o número ideal de cores sólidas via Elbow Method."""
    try:
        small = cv2.resize(img_bgr, (120, 120), interpolation=cv2.INTER_AREA)
        pixels = small.reshape(-1, 3).astype(np.float32)
        
        inertias = []
        for k in range(1, max_k + 1):
            crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
            comp, _, _ = cv2.kmeans(pixels, k, None, crit, 3, cv2.KMEANS_PP_CENTERS)
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
        return 4

def preprocess_image(input_path, output_png_path, k_colors=None, upscale_small=True, is_binary=False):
    """
    Pré-processa a imagem com super-resolução, filtro bilateral e quantização de paleta.
    Elimina 100% dos anéis de anti-aliasing e halos de cor que estragam o PowerTRACE.
    """
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Não foi possível abrir o arquivo de imagem: {input_path}")
    
    # Se tiver canal alfa com fundo transparente, preenche com branco para vetorização
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        bgr = img[:, :, :3]
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha_factor = (alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]
        img = (bgr.astype(np.float32) * alpha_factor + white_bg.astype(np.float32) * (1.0 - alpha_factor)).astype(np.uint8)
    elif len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    h, w = img.shape[:2]

    # 1. Super-Resolução Lanczos para imagens pequenas
    if upscale_small and (w < 1400 or h < 1400):
        scale = max(2, min(4, int(1800 / max(w, h))))
        if scale > 1:
            img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)

    # 2. Modo Binário (Silk Screen / Fotolito Puro)
    if is_binary:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Filtro Gaussiano leve para suavizar bordas
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite(output_png_path, bin_img)
        return output_png_path, None

    # 3. Filtro Bilateral Edge-Preserving (suaviza ruído sem desfocar cantos)
    img_filtered = cv2.bilateralFilter(img, d=7, sigmaColor=50, sigmaSpace=50)

    # 4. Quantização de Cores K-Means
    final_k = None
    if k_colors is not None and k_colors != "all":
        if k_colors == "auto":
            final_k = auto_detect_palette_k(img_filtered)
        else:
            try:
                final_k = int(k_colors)
            except ValueError:
                final_k = 4

        if final_k and final_k >= 2:
            pixels = img_filtered.reshape((-1, 3)).astype(np.float32)
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 0.5)
            _, labels, centers = cv2.kmeans(pixels, final_k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            centers = np.uint8(centers)
            img_quantized = centers[labels.flatten()].reshape(img_filtered.shape)
            
            # Pequeno fechamento morfológico para fechar micro-fissuras
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            img_quantized = cv2.morphologyEx(img_quantized, cv2.MORPH_CLOSE, kernel)
            
            cv2.imwrite(output_png_path, img_quantized)
            return output_png_path, centers

    cv2.imwrite(output_png_path, img_filtered)
    return output_png_path, None

def color_distance_sq(c1, c2):
    """Distância euclidiana quadrática no espaço RGB."""
    return (c1[0]-c2[0])**2 + (c1[1]-c2[1])**2 + (c1[2]-c2[2])**2

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join([c*2 for c in hex_str])
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

def postprocess_svg(svg_path, remove_bg=False, unify_colors=True):
    """
    Otimiza o arquivo SVG gerado:
    1. Harmoniza cores próximas em uma única cor pura (ex: elimina pequenas variações de preto)
    2. Remove o caminho de fundo branco / bounding box da tela caso solicitado
    """
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Extrai largura e altura do SVG
    width_m = re.search(r'width=[\x27\x22]([0-9.]+)[\x27\x22]', svg_content)
    height_m = re.search(r'height=[\x27\x22]([0-9.]+)[\x27\x22]', svg_content)
    svg_w = float(width_m.group(1)) if width_m else 0
    svg_h = float(height_m.group(1)) if height_m else 0

    # 1. Harmonização de cores
    if unify_colors:
        raw_colors = re.findall(r'fill=[\x27\x22](#[0-9a-fA-F]{3,6})[\x27\x22]', svg_content)
        unique_hex = list(set(raw_colors))
        rgb_map = {h: hex_to_rgb(h) for h in unique_hex}

        # Agrupa cores muito próximas (distância < 22)
        color_groups = []
        for h, rgb in rgb_map.items():
            # Casos especiais: quase preto (< 25) ou quase branco (> 245)
            if rgb[0] < 25 and rgb[1] < 25 and rgb[2] < 25:
                color_groups.append((h, '#000000'))
                continue
            if rgb[0] > 245 and rgb[1] > 245 and rgb[2] > 245:
                color_groups.append((h, '#FFFFFF'))
                continue

            matched = False
            for parent_h, target_h in color_groups:
                p_rgb = rgb_map.get(parent_h, (0, 0, 0))
                if color_distance_sq(rgb, p_rgb) < (22 * 22):
                    color_groups.append((h, target_h))
                    matched = True
                    break
            if not matched:
                color_groups.append((h, h.upper()))

        for src_h, dest_h in color_groups:
            if src_h != dest_h:
                svg_content = re.sub(
                    f'fill=[\x27\x22]{re.escape(src_h)}[\x27\x22]', 
                    f'fill="{dest_h}"', 
                    svg_content, 
                    flags=re.IGNORECASE
                )

    # 2. Remoção de Fundo Branco / Bounding Box da Prancheta
    if remove_bg and svg_w > 0 and svg_h > 0:
        # Encontra todos os caminhos
        def should_remove_bg_path(match):
            path_str = match.group(0)
            # Verifica se a cor é branca ou quase branca
            fill_m = re.search(r'fill=[\x27\x22]([^\x27\x22]+)[\x27\x22]', path_str)
            if not fill_m:
                return path_str
            fill = fill_m.group(1).upper()
            if fill not in ('#FFFFFF', '#FDFDFD', '#FEFEFE', '#FAFAFA', '#F5F5F5'):
                return path_str

            # Verifica se o caminho cobre todo o retângulo (M0 0 ... W 0 ... W H ... 0 H)
            d_m = re.search(r'd=[\x27\x22]([^\x27\x22]+)[\x27\x22]', path_str)
            if not d_m:
                return path_str
            d_val = d_m.group(1)
            
            # Se começar em M0 0 e tiver as dimensões máximas de largura e altura
            if "M0 0" in d_val and (str(int(svg_w)) in d_val or str(int(svg_h)) in d_val):
                return "" # Remove o path de fundo!
            return path_str

        # Aplica a remoção apenas no primeiro ou segundo path (o fundo sempre fica na base)
        paths = list(re.finditer(r'<path[^>]+>', svg_content))
        if paths:
            first_path = paths[0].group(0)
            cleaned = should_remove_bg_path(paths[0])
            if not cleaned:
                # Remove o primeiro path
                svg_content = svg_content.replace(first_path, '', 1)

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

def vectorize_image(
    input_path, 
    output_svg, 
    colormode='color',
    hierarchical='stacked',
    filter_speckle=4,
    color_precision=8,
    layer_difference=16,
    corner_threshold=40,
    length_threshold=3.0,
    splice_threshold=45,
    path_precision=2,
    remove_bg=False,
    unify_colors=True
):
    import vtracer

    # Chamada estritamente POSICIONAL para estabilidade no Python 3.14
    vtracer.convert_image_to_svg_py(
        str(input_path),
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

    # Pós-processamento inteligente de harmonização e remoção de fundo
    postprocess_svg(output_svg, remove_bg=remove_bg, unify_colors=unify_colors)

def main():
    parser = argparse.ArgumentParser(description="Vetorizador Inteligente de Estamparia")
    parser.add_argument("input", help="Caminho da imagem de entrada")
    parser.add_argument("output", help="Caminho do arquivo SVG de saída")
    parser.add_argument("--preset", default="logo", choices=["dtf", "silk", "logo", "plotter", "alta_definicao"])
    parser.add_argument("--colors", default="auto", help="Quantidade de cores: auto, 2, 3, 4, 6, 8, 12, 16, all")
    parser.add_argument("--colormode", default=None, choices=["color", "binary"])
    parser.add_argument("--hierarchical", default=None, choices=["stacked", "cutout"])
    parser.add_argument("--speckle", type=int, default=None)
    parser.add_argument("--corner", type=int, default=None)
    parser.add_argument("--remove-bg", action="store_true", help="Remover fundo branco da prancheta")
    parser.add_argument("--no-upscale", action="store_true", help="Desabilitar super-resolução inicial")

    args = parser.parse_args()

    presets = {
        "logo": {
            "colormode": "color",
            "hierarchical": "stacked",
            "filter_speckle": 6,
            "color_precision": 8,
            "layer_difference": 16,
            "corner_threshold": 38, # Cantos vivos geométricos
            "length_threshold": 2.8,
            "splice_threshold": 40,
            "path_precision": 2,
            "default_colors": "auto"
        },
        "dtf": {
            "colormode": "color",
            "hierarchical": "stacked", # Essencial no DTF: sem frestas brancas
            "filter_speckle": 4,
            "color_precision": 8,
            "layer_difference": 14,
            "corner_threshold": 45,
            "length_threshold": 3.2,
            "splice_threshold": 45,
            "path_precision": 2,
            "default_colors": "auto"
        },
        "silk": {
            "colormode": "binary", # Preto e branco puro para fotolito
            "hierarchical": "cutout",
            "filter_speckle": 8,
            "color_precision": 4,
            "layer_difference": 32,
            "corner_threshold": 45,
            "length_threshold": 3.5,
            "splice_threshold": 45,
            "path_precision": 2,
            "default_colors": "2"
        },
        "plotter": {
            "colormode": "color",
            "hierarchical": "cutout", # Recorte de vinil precisa de peças recortadas, não sobrepostas
            "filter_speckle": 10, # Elimina ruídos minúsculos para não rasgar no corte
            "color_precision": 8,
            "layer_difference": 24,
            "corner_threshold": 35,
            "length_threshold": 3.5,
            "splice_threshold": 45,
            "path_precision": 2,
            "default_colors": "auto"
        },
        "alta_definicao": {
            "colormode": "color",
            "hierarchical": "stacked",
            "filter_speckle": 2,
            "color_precision": 8,
            "layer_difference": 8,
            "corner_threshold": 65,
            "length_threshold": 2.2,
            "splice_threshold": 35,
            "path_precision": 2,
            "default_colors": "all"
        }
    }

    config = presets.get(args.preset, presets["logo"]).copy()
    default_colors = config.pop("default_colors", "auto")

    if args.colormode: config["colormode"] = args.colormode
    if args.hierarchical: config["hierarchical"] = args.hierarchical
    if args.speckle is not None: config["filter_speckle"] = args.speckle
    if args.corner is not None: config["corner_threshold"] = args.corner

    colors_mode = args.colors if args.colors is not None else default_colors
    is_binary = (config["colormode"] == "binary")

    temp_png = args.input + "._proc.png"
    try:
        proc_path, _ = preprocess_image(
            args.input, 
            temp_png, 
            k_colors=colors_mode, 
            upscale_small=(not args.no_upscale),
            is_binary=is_binary
        )
        
        vectorize_image(
            proc_path, 
            args.output, 
            remove_bg=args.remove_bg,
            unify_colors=True,
            **config
        )
        print(f"SUCESSO:{args.output}")
    except Exception as e:
        print(f"ERRO:{e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if os.path.exists(temp_png):
            try:
                os.remove(temp_png)
            except:
                pass

if __name__ == "__main__":
    main()
