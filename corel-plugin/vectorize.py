"""
Order Separator - Motor Profissional de Vetorização de Imagens (VTracer / Dual-Splines)
Superior ao Corel PowerTRACE e Illustrator Image Trace:
- Sem frestas brancas entre cores (Hierarchical Stacked Layers)
- Cantos vivos preservados (Corner Threshold com restrição angular)
- Eliminação inteligente de ruídos e micropontos (Speckle Filter)
- Redução extrema de nós para corte em plotter e separação rápida
"""

import sys
import os
import argparse
from PIL import Image, ImageFilter, ImageEnhance

def preprocess_image(input_path, output_png_path, denoise=True, upscale_small=True):
    img = Image.open(input_path)
    
    # Preserva canal alfa ou converte para RGBA
    if img.mode not in ('RGBA', 'RGB'):
        img = img.convert('RGBA')
        
    w, h = img.size
    
    # Se imagem for pequena (< 1200px), faz super-resolução Lanczos para eliminar serrilhado antes de vetorizar
    if upscale_small and (w < 1200 or h < 1200):
        scale = max(2, min(4, int(1600 / max(w, h))))
        if scale > 1:
            img = img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
    
    # Leve realce de bordas para melhorar detecção de contornos
    if denoise:
        img = img.filter(ImageFilter.SMOOTH_MORE)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
    img.save(output_png_path, format="PNG")
    return output_png_path

def vectorize_image(
    input_path, 
    output_svg, 
    colormode='color', # 'color' ou 'binary'
    hierarchical='stacked', # 'stacked' (sem frestas brancas) ou 'cutout'
    filter_speckle=4, # ignora manchas/ruídos menores que N pixels
    color_precision=6, # 1-8 bits de precisão de cor
    layer_difference=16, # agrupamento de tons próximos
    corner_threshold=60, # angulo para canto vivo vs curva suave (graus)
    length_threshold=4.0, # comprimento dos segmentos
    splice_threshold=45, # junção de curvas contínuas
    path_precision=2 # casas decimais no SVG (reduz tamanho sem perda)
):
    import vtracer

    # Chamada estritamente POSICIONAL para máxima estabilidade e compatibilidade
    vtracer.convert_image_to_svg_py(
        str(input_path),
        str(output_svg),
        str(colormode),
        str(hierarchical),
        'spline', # modo Bézier Dual-Spline
        int(filter_speckle),
        int(color_precision),
        int(layer_difference),
        int(corner_threshold),
        float(length_threshold),
        10, # max_iterations
        int(splice_threshold),
        int(path_precision)
    )

def main():
    parser = argparse.ArgumentParser(description="Vetorizador Inteligente de Estamparia")
    parser.add_argument("input", help="Caminho da imagem de entrada (PNG, JPG, etc)")
    parser.add_argument("output", help="Caminho do arquivo SVG de saída")
    parser.add_argument("--preset", default="dtf", choices=["dtf", "silk", "logo", "alta_definicao"], help="Preset de estamparia")
    parser.add_argument("--colormode", default=None, choices=["color", "binary"])
    parser.add_argument("--hierarchical", default=None, choices=["stacked", "cutout"])
    parser.add_argument("--speckle", type=int, default=None, help="Filtro de ruído (pixels)")
    parser.add_argument("--precision", type=int, default=None, help="Precisão de cor (1-8)")
    parser.add_argument("--corner", type=int, default=None, help="Limiar de canto vivo (graus)")
    parser.add_argument("--no-upscale", action="store_true", help="Desabilitar super-resolução inicial")

    args = parser.parse_args()

    presets = {
        "dtf": {
            "colormode": "color",
            "hierarchical": "stacked", # Essencial no DTF para evitar linhas brancas no filme
            "filter_speckle": 4,
            "color_precision": 7,
            "layer_difference": 14,
            "corner_threshold": 60,
            "length_threshold": 3.5,
            "splice_threshold": 45,
            "path_precision": 2
        },
        "silk": {
            "colormode": "binary", # Preto e branco puro com curvas perfeitas para gravação de tela
            "hierarchical": "cutout",
            "filter_speckle": 8,
            "color_precision": 4,
            "layer_difference": 32,
            "corner_threshold": 50,
            "length_threshold": 4.0,
            "splice_threshold": 50,
            "path_precision": 2
        },
        "logo": {
            "colormode": "color",
            "hierarchical": "stacked",
            "filter_speckle": 6,
            "color_precision": 6, # Cores chapadas / flats
            "layer_difference": 24,
            "corner_threshold": 45, # Cantos bem vivos e geométricos
            "length_threshold": 4.0,
            "splice_threshold": 45,
            "path_precision": 2
        },
        "alta_definicao": {
            "colormode": "color",
            "hierarchical": "stacked",
            "filter_speckle": 2,
            "color_precision": 8,
            "layer_difference": 8,
            "corner_threshold": 70,
            "length_threshold": 2.5,
            "splice_threshold": 35,
            "path_precision": 2
        }
    }

    config = presets.get(args.preset, presets["dtf"]).copy()

    if args.colormode: config["colormode"] = args.colormode
    if args.hierarchical: config["hierarchical"] = args.hierarchical
    if args.speckle is not None: config["filter_speckle"] = args.speckle
    if args.precision is not None: config["color_precision"] = args.precision
    if args.corner is not None: config["corner_threshold"] = args.corner

    temp_png = args.input + "._proc.png"
    try:
        proc_path = preprocess_image(args.input, temp_png, upscale_small=(not args.no_upscale))
        vectorize_image(proc_path, args.output, **config)
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
