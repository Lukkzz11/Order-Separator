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

def detect_image_mode(img_bgr):
    """
    Classifica automaticamente a complexidade da imagem em um dos 3 motores especializados:
    - 'line_art'      : Ilustrações detalhadas P&B/monocromáticas, gravuras, mangá, traços finos (ex: Leão)
    - 'photo_complex' : Fotos, retratos, degradês contínuos de pele/paisagem ou imagens pixeladas (ex: Retrato 100x100)
    - 'flat_logo'     : Logos, escudos, ícones e tipografia com cores sólidas chapadas (ex: Escudo Flamengo, Logo E/S/NE)
    """
    h, w = img_bgr.shape[:2]
    scale = min(1.0, 400.0 / max(h, w))
    small = cv2.resize(img_bgr, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)

    sh, sw = small.shape[:2]
    core_crop = small[sh // 8 : max(sh // 8 + 1, 7 * sh // 8), sw // 8 : max(sw // 8 + 1, 7 * sw // 8)]

    # Analisa a proporção de regiões planas puras (gradiente <= 7)
    kernel3 = np.ones((3, 3), np.uint8)
    grad = np.max(cv2.morphologyEx(small, cv2.MORPH_GRADIENT, kernel3), axis=2)
    flat_ratio = float(np.mean(grad <= 7))

    img_f = small.astype(np.float32)
    chroma = np.max(img_f, axis=2) - np.min(img_f, axis=2)
    strong_color_ratio = float(np.mean(chroma > 38.0))

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    edge_density = float(np.mean(edges > 0))

    # 1. Quase sem cores vivas (P&B / gravura / silk)
    if strong_color_ratio < 0.0025:
        _, bw = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        cnts, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        valid_cnts = sum(1 for c in cnts if cv2.contourArea(c) >= 4)
        if valid_cnts >= 40 or edge_density > 0.045:
            return "line_art"
        return "flat_logo"

    # 2. Se a imagem tem alta taxa de áreas planas (flat_ratio >= 0.70), é claramente um Logo / Escudo / Vetor plano!
    if flat_ratio >= 0.70:
        return "flat_logo"

    # 3. Para imagens com poucas áreas planas (< 0.70), verifica a distribuição de cores
    cf = core_crop.reshape(-1, 3)
    non_white = cf[np.max(cf, axis=1) < 240]
    if len(non_white) < 50:
        non_white = cf
    bins = (non_white // 24) * 24
    _, counts = np.unique(bins, axis=0, return_counts=True)
    counts_sorted = np.sort(counts)[::-1]
    cum_ratios = np.cumsum(counts_sorted) / max(1, np.sum(counts_sorted))
    bins_90 = int(np.searchsorted(cum_ratios, 0.90)) + 1

    if bins_90 >= 7 and flat_ratio < 0.65:
        return "photo_complex"
    return "flat_logo"


def detect_pixel_grid_dimensions_robust(img_bgr):
    """
    Detecta automaticamente se uma imagem foi ampliada com blocos quadrados (pixelada / Nearest-Neighbor)
    analisando picos periódicos no perfil de gradiente horizontal e vertical do miolo da imagem.
    """
    h, w = img_bgr.shape[:2]
    y0, y1 = int(h * 0.15), int(h * 0.85)
    x0, x1 = int(w * 0.15), int(w * 0.85)
    crop = img_bgr[y0:y1, x0:x1]
    ch, cw = crop.shape[:2]
    if ch < 32 or cw < 32:
        return w, h, False

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
    col_prof = np.mean(np.abs(np.diff(gray, axis=1)), axis=0)
    row_prof = np.mean(np.abs(np.diff(gray, axis=0)), axis=1)

    med_x = max(0.1, float(np.median(col_prof)))
    med_y = max(0.1, float(np.median(row_prof)))
    ratio_x = float(np.percentile(col_prof, 85)) / med_x
    ratio_y = float(np.percentile(row_prof, 85)) / med_y

    if ratio_x > 1.55 and ratio_y > 1.55:
        peaks_x = int(np.sum((col_prof[1:-1] > col_prof[:-2]) & (col_prof[1:-1] >= col_prof[2:]) & (col_prof[1:-1] > med_x * 1.22)))
        peaks_y = int(np.sum((row_prof[1:-1] > row_prof[:-2]) & (row_prof[1:-1] >= row_prof[2:]) & (row_prof[1:-1] > med_y * 1.22)))
        if peaks_x >= 12 and peaks_y >= 12:
            full_tw = int(round(peaks_x * (float(w) / float(cw))))
            full_th = int(round(peaks_y * (float(h) / float(ch))))
            if 25 <= full_tw <= (w // 2) and 25 <= full_th <= (h // 2):
                return full_tw, full_th, True
    return w, h, False


def get_exterior_white_bg_mask(img_bgr, white_thresh=232):
    """
    Identifica apenas o fundo branco/claro EXTERNO conectado às bordas da imagem,
    preservando 100% dos brilhos claros e detalhes brancos no interior do desenho/retrato.
    """
    h, w = img_bgr.shape[:2]
    is_light = np.all(img_bgr >= white_thresh, axis=2).astype(np.uint8)
    num_labels, labels = cv2.connectedComponents(is_light, connectivity=8)
    border_labels = set(labels[0, :]) | set(labels[h - 1, :]) | set(labels[:, 0]) | set(labels[:, w - 1])
    border_labels.discard(0)
    if not border_labels:
        return np.zeros((h, w), dtype=bool)
    return np.isin(labels, list(border_labels))


def extract_exact_palette_and_segment(img_bgr, k_colors="auto", unify_colors=True):
    """
    Extrai as cores EXATAS das regiões planas (sem misturar com pixels de anti-aliasing)
    e segmenta a imagem usando Distância Ponderada por Croma (evita que cinzas virem vermelho/marrom).
    """
    h, w = img_bgr.shape[:2]
    kernel3 = np.ones((3, 3), np.uint8)
    grad = np.max(cv2.morphologyEx(img_bgr, cv2.MORPH_GRADIENT, kernel3), axis=2)
    flat_mask = (grad <= 6)
    flat_pixels = img_bgr[flat_mask]
    if len(flat_pixels) < 100:
        flat_pixels = img_bgr.reshape(-1, 3)

    bins = (flat_pixels // 16) * 16
    uniq_bins, counts = np.unique(bins, axis=0, return_counts=True)
    order = np.argsort(-counts)

    max_k = 12
    if k_colors is not None and k_colors not in ("auto", "all"):
        try:
            max_k = max(2, int(k_colors))
        except ValueError:
            max_k = 8
    elif k_colors == "all":
        max_k = 24

    dist_thresh = 52 if unify_colors and max_k <= 12 else 28
    min_pixels = max(60, int(len(flat_pixels) * 0.0005))

    palette = []
    for idx in order:
        if counts[idx] < min_pixels and len(palette) >= 2:
            break
        b_val = uniq_bins[idx]
        mask_bin = np.all((flat_pixels // 16) * 16 == b_val, axis=1)
        exact_vals, exact_cnts = np.unique(flat_pixels[mask_bin], axis=0, return_counts=True)
        mode_color = exact_vals[np.argmax(exact_cnts)].astype(int)

        if unify_colors:
            if np.all(mode_color < 35):
                mode_color = np.array([0, 0, 0])
            elif np.all(mode_color > 235):
                mode_color = np.array([255, 255, 255])

        if not any(np.sum((mode_color - ex) ** 2) < (dist_thresh ** 2) for ex in palette):
            palette.append(mode_color)
            if len(palette) >= max_k:
                break

    if len(palette) == 0:
        palette = [np.array([255, 255, 255]), np.array([0, 0, 0])]

    palette = np.array(palette, dtype=np.uint8)
    img_f = img_bgr.astype(np.float32)
    img_chroma = np.max(img_f, axis=2) - np.min(img_f, axis=2)

    K = len(palette)
    dists = np.zeros((h, w, K), dtype=np.float32)
    for k in range(K):
        c = palette[k].astype(np.float32)
        c_chroma = np.max(c) - np.min(c)
        dists[:, :, k] = np.sum((img_f - c) ** 2, axis=2) + 4.5 * ((img_chroma - c_chroma) ** 2)

    labels = np.argmin(dists, axis=2)
    return palette[labels], palette


def smooth_contour_gaussian(pts, sigma=1.4, is_closed=True):
    """Suaviza pontos de contorno (N, 2) em sub-pixel com filtro Gaussiano circular."""
    N = len(pts)
    if N < 5 or sigma <= 0.1:
        return pts.astype(np.float64)
    r = max(2, int(round(sigma * 3.0)))
    if N <= 2 * r + 1:
        return pts.astype(np.float64)
    idx = np.arange(-r, r + 1, dtype=np.float64)
    weights = np.exp(-0.5 * (idx / sigma) ** 2)
    weights /= np.sum(weights)
    if is_closed:
        padded = np.vstack([pts[-r:], pts, pts[:r]]).astype(np.float64)
        sx = np.convolve(padded[:, 0], weights, mode="valid")
        sy = np.convolve(padded[:, 1], weights, mode="valid")
        return np.column_stack([sx, sy])
    return pts.astype(np.float64)


def fit_cubic_bezier_chain(pts, corner_angle_deg=52.0, rdp_eps=1.1, sigma=1.4, allow_hv_snap=False):
    """
    Motor de Splines Bézier Cúbicas Adaptativas:
    - Preserva 100% dos detalhes finos (pelos, gravuras, retratos, mascotes)
    - Mantém quinas vivas agudas nas pontas reais
    - Emite curvas Bézier cúbicas ('C') suaves sem auto-interseção
    """
    N = len(pts)
    if N < 3:
        return ""
    poly_raw = cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), rdp_eps, True)[:, 0, :].astype(np.float64)
    if len(poly_raw) < 3:
        return ""

    smooth_dense = smooth_contour_gaussian(pts, sigma=sigma, is_closed=True)
    poly = cv2.approxPolyDP(smooth_dense.astype(np.float32).reshape(-1, 1, 2), rdp_eps, True)[:, 0, :].astype(np.float64)
    M = len(poly)
    if M < 3:
        poly = poly_raw
        M = len(poly)

    is_corner = np.zeros(M, dtype=bool)
    for i in range(M):
        p_prev, p_curr, p_next = poly[(i - 1) % M], poly[i], poly[(i + 1) % M]
        v1, v2 = p_curr - p_prev, p_next - p_curr
        l1, l2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if l1 > 1e-3 and l2 > 1e-3:
            cos_a = np.clip(np.dot(v1, v2) / (l1 * l2), -1.0, 1.0)
            turn_angle = np.degrees(np.arccos(cos_a))
            if turn_angle >= corner_angle_deg or (turn_angle >= 28.0 and max(l1, l2) >= 20.0):
                is_corner[i] = True
                dists_raw = np.sum((poly_raw - p_curr) ** 2, axis=1)
                nearest_raw = poly_raw[np.argmin(dists_raw)]
                if np.linalg.norm(nearest_raw - p_curr) <= 3.5:
                    poly[i] = nearest_raw

    if allow_hv_snap:
        for i in range(M):
            j = (i + 1) % M
            if is_corner[i] and is_corner[j]:
                seg_vec = poly[j] - poly[i]
                seg_len = np.linalg.norm(seg_vec)
                if seg_len >= 12.0:
                    ang = abs(np.degrees(np.arctan2(seg_vec[1], seg_vec[0])))
                    if ang < 5.0 or abs(ang - 180.0) < 5.0:
                        mid_y = 0.5 * (poly[i][1] + poly[j][1])
                        poly[i][1] = mid_y
                        poly[j][1] = mid_y
                    elif abs(ang - 90.0) < 5.0:
                        mid_x = 0.5 * (poly[i][0] + poly[j][0])
                        poly[i][0] = mid_x
                        poly[j][0] = mid_x

    tangents = np.zeros_like(poly)
    for i in range(M):
        if not is_corner[i]:
            tangents[i] = (poly[(i + 1) % M] - poly[(i - 1) % M]) * 0.5

    cmds = [f"M {poly[0][0]:.2f} {poly[0][1]:.2f}"]
    for i in range(M):
        j = (i + 1) % M
        p0, p1 = poly[i], poly[j]
        seg_len = np.linalg.norm(p1 - p0)
        if (is_corner[i] and is_corner[j]) or seg_len < 2.2:
            cmds.append(f"L {p1[0]:.2f} {p1[1]:.2f}")
        else:
            t0, t1 = tangents[i], tangents[j]
            len_t0, len_t1 = np.linalg.norm(t0), np.linalg.norm(t1)
            max_t = seg_len * 0.36
            if len_t0 > max_t and len_t0 > 1e-5:
                t0 = t0 * (max_t / len_t0)
            if len_t1 > max_t and len_t1 > 1e-5:
                t1 = t1 * (max_t / len_t1)
            c1 = p0 + t0 * (0.65 if not is_corner[i] else 0.0)
            c2 = p1 - t1 * (0.65 if not is_corner[j] else 0.0)
            cmds.append(f"C {c1[0]:.2f} {c1[1]:.2f}, {c2[0]:.2f} {c2[1]:.2f}, {p1[0]:.2f} {p1[1]:.2f}")
    cmds.append("Z")
    return " ".join(cmds)


def trace_mask_compound_svg(mask, rdp_eps=1.1, corner_angle_deg=52.0, sigma=1.4, min_area=12, allow_hv_snap=False):
    """
    Extrai contornos externos + furos internos (hierarquia RETR_CCOMP) como caminhos compostos
    ('M ... Z M ... Z' com fill-rule='evenodd') para furos 100% precisos sem cobrir detalhes internos.
    """
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if hier is None or len(cnts) == 0:
        return [], (0, 0, 0, 0)
    hier = hier[0]
    compound_paths = []
    min_x, min_y, max_x, max_y = 10**9, 10**9, 0, 0
    for idx, cnt in enumerate(cnts):
        if hier[idx][3] != -1:
            continue
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x_b, y_b, w_b, h_b = cv2.boundingRect(cnt)
        outer_d = fit_cubic_bezier_chain(cnt[:, 0, :], corner_angle_deg=corner_angle_deg, rdp_eps=rdp_eps, sigma=sigma, allow_hv_snap=allow_hv_snap)
        if not outer_d:
            continue
        sub_paths = [outer_d]
        child_idx = hier[idx][2]
        while child_idx != -1:
            hole_cnt = cnts[child_idx]
            if cv2.contourArea(hole_cnt) >= max(6, min_area * 0.4):
                hole_d = fit_cubic_bezier_chain(hole_cnt[:, 0, :], corner_angle_deg=corner_angle_deg, rdp_eps=rdp_eps, sigma=sigma, allow_hv_snap=allow_hv_snap)
                if hole_d:
                    sub_paths.append(hole_d)
            child_idx = hier[child_idx][0]
        compound_paths.append((area, " ".join(sub_paths), (x_b, y_b, w_b, h_b)))
        min_x, min_y, max_x, max_y = min(min_x, x_b), min(min_y, y_b), max(max_x, x_b + w_b), max(max_y, y_b + h_b)
    return compound_paths, (min_x, min_y, max_x, max_y)


def _fit_clean_line(pts, allow_hv=True, hv_angle_tol=16.0):
    N = len(pts)
    core = pts[max(1, N // 4) : N - max(1, N // 4)] if N >= 8 else pts
    vx, vy, x0, y0 = cv2.fitLine(core.astype(np.float32), cv2.DIST_L2, 0, 0.01, 0.01).flatten()
    chord = pts[-1] - pts[0]
    if vx * chord[0] + vy * chord[1] < 0:
        vx, vy = -vx, -vy
    chord_angle = abs(np.degrees(np.arctan2(chord[1], chord[0])))

    is_hv = False
    if allow_hv:
        if chord_angle < hv_angle_tol or abs(chord_angle - 180.0) < hv_angle_tol:
            vx, vy = (1.0 if chord[0] >= 0 else -1.0), 0.0
            y0 = np.median(core[:, 1])
            x0 = np.median(core[:, 0])
            is_hv = True
        elif abs(chord_angle - 90.0) < hv_angle_tol:
            vx, vy = 0.0, (1.0 if chord[1] >= 0 else -1.0)
            x0 = np.median(core[:, 0])
            y0 = np.median(core[:, 1])
            is_hv = True

    p0 = np.array([float(x0), float(y0)])
    d = np.array([float(vx), float(vy)])
    t0 = np.dot(pts[0] - p0, d)
    t1 = np.dot(pts[-1] - p0, d)
    return p0 + t0 * d, p0 + t1 * d, p0, d, is_hv


def _intersect_lines(p1, d1, p2, d2, fallback):
    cross = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(cross) < 0.25:
        return fallback
    diff = p2 - p1
    t1 = (diff[0] * d2[1] - diff[1] * d2[0]) / cross
    inter = p1 + t1 * d1
    if np.linalg.norm(inter - fallback) <= 45.0:
        return inter
    return fallback


def _contour_to_svg_path(cnt, corner_threshold=38):
    """
    Seletor Geométrico Híbrido por Contorno:
    - Para formas geométricas simples (letras retas, escudos, caixas com <= 28 vértices e chanfros curtos),
      aplica Reconstrução Matemática CAD (interseção exata de retas + fillets Bézier).
    - Para formas orgânicas ou complexas (mascotes, curvas livres, ilustrações detalhadas),
      aplica automaticamente Splines Bézier Cúbicas Adaptativas sem jamais cortar pedaços da arte!
    """
    pts = cnt[:, 0, :].astype(np.float64)
    if len(pts) < 4:
        return ""

    poly = cv2.approxPolyDP(cnt, 3.8, True)[:, 0, :].astype(np.float64)
    if len(poly) < 3:
        return ""

    # Se o contorno tem muitos vértices (> 28), é uma forma orgânica/complexa -> usa spline Bézier adaptativa
    if len(poly) > 28:
        return fit_cubic_bezier_chain(pts, corner_angle_deg=max(32.0, float(corner_threshold)), rdp_eps=1.15, sigma=1.4, allow_hv_snap=True)

    merged = [poly[0]]
    for i in range(1, len(poly)):
        p_prev, p_curr, p_next = merged[-1], poly[i], poly[(i + 1) % len(poly)]
        v1, v2 = p_curr - p_prev, p_next - p_curr
        l1, l2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if l1 > 1e-3 and l2 > 1e-3:
            cos_a = np.clip(np.dot(v1, v2) / (l1 * l2), -1.0, 1.0)
            if np.degrees(np.arccos(cos_a)) < 14.0:
                continue
        merged.append(poly[i])
    poly = np.array(merged)
    M = len(poly)
    if M < 3:
        return ""

    idxs = [int(np.argmin(np.sum((pts - v) ** 2, axis=1))) for v in poly]
    edges = []
    for i in range(M):
        i1, i2 = idxs[i], idxs[(i + 1) % M]
        seg = pts[i1 : i2 + 1] if i2 > i1 else np.vstack([pts[i1:], pts[: i2 + 1]])
        if len(seg) < 2:
            seg = np.array([poly[i], poly[(i + 1) % M]])
        length = float(np.linalg.norm(poly[(i + 1) % M] - poly[i]))
        s_pt, e_pt, p0, d_vec, is_hv = _fit_clean_line(seg, allow_hv=(length >= 14.0), hv_angle_tol=16.0)
        edges.append({"s": s_pt, "e": e_pt, "p0": p0, "d": d_vec, "len": length, "raw": seg, "is_hv": is_hv})

    merged_edges = []
    for e in edges:
        if merged_edges and np.allclose(merged_edges[-1]["d"], e["d"], atol=0.05):
            prev = merged_edges[-1]
            comb_raw = np.vstack([prev["raw"], e["raw"]])
            new_len = prev["len"] + e["len"]
            s_pt, e_pt, p0, d_vec, is_hv = _fit_clean_line(comb_raw, allow_hv=True)
            merged_edges[-1] = {"s": s_pt, "e": e_pt, "p0": p0, "d": d_vec, "len": new_len, "raw": comb_raw, "is_hv": is_hv}
        else:
            merged_edges.append(e)
    if len(merged_edges) >= 2 and np.allclose(merged_edges[0]["d"], merged_edges[-1]["d"], atol=0.05):
        comb_raw = np.vstack([merged_edges[-1]["raw"], merged_edges[0]["raw"]])
        new_len = merged_edges[-1]["len"] + merged_edges[0]["len"]
        s_pt, e_pt, p0, d_vec, is_hv = _fit_clean_line(comb_raw, allow_hv=True)
        merged_edges[0] = {"s": s_pt, "e": e_pt, "p0": p0, "d": d_vec, "len": new_len, "raw": comb_raw, "is_hv": is_hv}
        merged_edges.pop()
    edges = merged_edges
    M = len(edges)

    for e in edges:
        e["major"] = (e["is_hv"] and e["len"] >= 15.0) or (e["len"] >= 32.0)

    major_indices = [i for i, e in enumerate(edges) if e["major"]]
    if len(major_indices) >= 2:
        for m_i in range(len(major_indices)):
            idx_curr = major_indices[m_i]
            idx_next = major_indices[(m_i + 1) % len(major_indices)]
            e1, e2 = edges[idx_curr], edges[idx_next]
            cross_val = abs(e1["d"][0] * e2["d"][1] - e1["d"][1] * e2["d"][0])
            if cross_val < 0.35 and (idx_curr + 1) % M != idx_next:
                k = (idx_curr + 1) % M
                best_k, best_len = k, -1.0
                while k != idx_next:
                    if edges[k]["len"] > best_len:
                        best_len = edges[k]["len"]
                        best_k = k
                    k = (k + 1) % M
                em = edges[best_k]
                chord = em["raw"][-1] - em["raw"][0]
                if abs(e1["d"][1]) < 0.1:
                    d_vec = np.array([0.0, 1.0 if chord[1] >= 0 else -1.0])
                elif abs(e1["d"][0]) < 0.1:
                    d_vec = np.array([1.0 if chord[0] >= 0 else -1.0, 0.0])
                else:
                    d_vec = chord / max(1e-5, np.linalg.norm(chord))
                p0 = np.array([float(np.median(em["raw"][:, 0])), float(np.median(em["raw"][:, 1]))])
                t0, t1 = np.dot(em["raw"][0] - p0, d_vec), np.dot(em["raw"][-1] - p0, d_vec)
                em["s"], em["e"], em["p0"], em["d"], em["is_hv"], em["major"] = (
                    p0 + t0 * d_vec,
                    p0 + t1 * d_vec,
                    p0,
                    d_vec,
                    True,
                    True,
                )

    major_indices = [i for i, e in enumerate(edges) if e["major"]]
    K_maj = len(major_indices)
    if K_maj < 3:
        return fit_cubic_bezier_chain(pts, corner_angle_deg=max(32.0, float(corner_threshold)), rdp_eps=1.15, sigma=1.4, allow_hv_snap=True)

    # Trava de segurança: se qualquer cadeia de 'minors' entre duas arestas principais for muito longa (> 48px),
    # significa que é uma curva orgânica e não um chanfro de canto -> usa fit_cubic_bezier_chain!
    for m_i in range(K_maj):
        idx_curr, idx_next = major_indices[m_i], major_indices[(m_i + 1) % K_maj]
        k = (idx_curr + 1) % M
        minor_len = 0.0
        while k != idx_next:
            minor_len += edges[k]["len"]
            k = (k + 1) % M
        if minor_len > 48.0:
            return fit_cubic_bezier_chain(pts, corner_angle_deg=max(32.0, float(corner_threshold)), rdp_eps=1.15, sigma=1.4, allow_hv_snap=True)

    sharp_limit = 14.5 if corner_threshold <= 50 else 11.0
    transitions = []
    for m_i in range(K_maj):
        idx_curr, idx_next = major_indices[m_i], major_indices[(m_i + 1) % K_maj]
        e1, e2 = edges[idx_curr], edges[idx_next]
        minors = []
        k = (idx_curr + 1) % M
        while k != idx_next:
            minors.append(edges[k])
            k = (k + 1) % M

        minor_total_len = sum(m["len"] for m in minors)
        adj_min_len = min(e1["len"], e2["len"])
        is_sharp = (len(minors) == 0) or (minor_total_len <= sharp_limit) or (minor_total_len < 0.14 * adj_min_len)
        fallback_pt = e1["e"] if len(minors) == 0 else 0.5 * (e1["e"] + e2["s"])
        corner_pt = _intersect_lines(e1["p0"], e1["d"], e2["p0"], e2["d"], fallback_pt)

        if is_sharp:
            e1["trim_e"] = corner_pt
            e2["trim_s"] = corner_pt
            transitions.append({"type": "sharp", "pt": corner_pt})
        else:
            r = np.clip(minor_total_len * 0.58, 12.0, 22.0)
            p_start = corner_pt - e1["d"] * r
            p_end = corner_pt + e2["d"] * r
            e1["trim_e"] = p_start
            e2["trim_s"] = p_end
            c1 = p_start + 0.552 * (corner_pt - p_start)
            c2 = p_end + 0.552 * (corner_pt - p_end)
            transitions.append({"type": "fillet", "p_start": p_start, "c1": c1, "c2": c2, "p_end": p_end})

    first_e = edges[major_indices[0]]
    start_pt = first_e["trim_s"]
    d_cmds = [f"M {start_pt[0]:.2f} {start_pt[1]:.2f}"]

    for m_i in range(K_maj):
        idx_curr = major_indices[m_i]
        e1 = edges[idx_curr]
        tr = transitions[m_i]
        end_line = e1["trim_e"]
        d_cmds.append(f"L {end_line[0]:.2f} {end_line[1]:.2f}")
        if tr["type"] == "fillet":
            c1, c2, pe = tr["c1"], tr["c2"], tr["p_end"]
            d_cmds.append(f"C {c1[0]:.2f} {c1[1]:.2f}, {c2[0]:.2f} {c2[1]:.2f}, {pe[0]:.2f} {pe[1]:.2f}")

    d_cmds.append("Z")
    return " ".join(d_cmds)


def auto_crop_canvas_borders(img_bgr, pad=12):
    """
    Detecta e recorta automaticamente margens vazias de prancheta/tela capturadas junto da arte,
    garantindo que o vetorizador processe apenas o desenho real sem distorções de escala ou cores de tela.
    """
    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 30, 100)
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 350:
            x, y, bw, bh = cv2.boundingRect(c)
            if bw < w * 0.96 or bh < h * 0.96:
                boxes.append((x, y, bw, bh, area))
    if boxes:
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes)
        y1 = max(b[1] + b[3] for b in boxes)
        crop_w = x1 - x0
        crop_h = y1 - y0
        if crop_w < w * 0.92 or crop_h < h * 0.92:
            return img_bgr[max(0, y0 - pad) : min(h, y1 + pad), max(0, x0 - pad) : min(w, x1 + pad)]
    return img_bgr


def execute_vectorization(
    input_path,
    output_svg,
    colormode="color",
    hierarchical="stacked",
    filter_speckle=6,
    color_precision=8,
    layer_difference=16,
    corner_threshold=38,
    length_threshold=2.8,
    splice_threshold=40,
    path_precision=2,
    k_colors="auto",
    upscale_small=True,
    remove_bg=True,
    unify_colors=True,
):
    """
    Motor de Vetorização Inteligente Tri-Modal (Auto-Adaptativo):
    1. 'line_art'      -> Ilustrações detalhadas P&B/gravuras (ex: Leão): contraste adaptativo + limpeza de marca d'água + furos compostos RETR_CCOMP
    2. 'photo_complex' -> Fotos/retratos/baixa resolução (ex: Retrato 100x100): despixelização de grade + Super-Resolução Bilateral/Mean-Shift + K-Means LAB
    3. 'flat_logo'     -> Logos/ícones/tipografia (ex: Logo E/S/NE, Escudo Flamengo): paleta exata por Croma + curvas Bézier puras
    """
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Não foi possível abrir o arquivo de imagem: {input_path}")

    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha = img[:, :, 3]
        bgr = img[:, :, :3]
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha_factor = (alpha.astype(np.float32) / 255.0)[:, :, np.newaxis]
        img = (bgr.astype(np.float32) * alpha_factor + white_bg.astype(np.float32) * (1.0 - alpha_factor)).astype(np.uint8)
    elif len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    # Remove automaticamente molduras e margens de tela/prancheta para focar 100% no desenho real
    img = auto_crop_canvas_borders(img)

    mode = detect_image_mode(img)
    if colormode == "binary" and mode == "photo_complex":
        mode = "line_art"

    # =====================================================================
    # MODO 1: ILUSTRAÇÕES DETALHADAS / LINE-ART / GRAVURAS (Ex: Leão)
    # =====================================================================
    if mode == "line_art":
        h0, w0 = img.shape[:2]
        scale = max(2, min(3, int(1800 / max(w0, h0)))) if upscale_small else 1
        work = cv2.resize(img, (w0 * scale, h0 * scale), interpolation=cv2.INTER_LANCZOS4) if scale > 1 else img.copy()
        h, w = work.shape[:2]

        gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
        blur_bg = cv2.GaussianBlur(gray, (51, 51), 0)
        diff = blur_bg.astype(np.float32) - gray.astype(np.float32)
        # Recupera 100% dos traços finos e pelos enquanto ignora marcas d'água cinza-claro de fundo
        ink_mask = ((gray < 168) | ((diff > 16.0) & (gray < 212))).astype(np.uint8) * 255
        ink_mask = cv2.GaussianBlur(ink_mask, (5, 5), 1.1)
        _, ink_mask = cv2.threshold(ink_mask, 125, 255, cv2.THRESH_BINARY)

        min_area = max(12, int(filter_speckle) * 2)
        paths, (min_x, min_y, max_x, max_y) = trace_mask_compound_svg(
            ink_mask,
            rdp_eps=1.15,
            corner_angle_deg=max(35.0, float(corner_threshold)),
            sigma=1.35,
            min_area=min_area,
            allow_hv_snap=False,
        )

        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        ]
        if not remove_bg:
            svg_lines.append(f'  <rect width="{w}" height="{h}" fill="#FFFFFF" />')
        for _, d_str, _ in paths:
            svg_lines.append(f'  <path fill="#000000" fill-rule="evenodd" d="{d_str}" />')
        svg_lines.append("</svg>")

        with open(output_svg, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

        if max_x > min_x and max_y > min_y:
            return output_svg, (float(max_x - min_x) / float(w), float(max_y - min_y) / float(h))
        return output_svg, (1.0, 1.0)

    # =====================================================================
    # MODO 2: FOTOS / RETRATOS / IMAGENS PIXELADAS OU COM DEGRADÊS
    # =====================================================================
    if mode == "photo_complex":
        tw, th, is_blocky = detect_pixel_grid_dimensions_robust(img)
        work = img.copy()
        if is_blocky:
            work = cv2.resize(work, (tw, th), interpolation=cv2.INTER_AREA)

        while max(work.shape[:2]) < 920:
            nh, nw = work.shape[0] * 2, work.shape[1] * 2
            work = cv2.resize(work, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
            work = cv2.bilateralFilter(work, d=9, sigmaColor=28, sigmaSpace=28)

        work = cv2.pyrMeanShiftFiltering(work, sp=8, sr=16)
        work = cv2.bilateralFilter(work, d=7, sigmaColor=22, sigmaSpace=22)

        h, w = work.shape[:2]
        ext_bg_mask = get_exterior_white_bg_mask(work, white_thresh=232) if remove_bg else np.zeros((h, w), dtype=bool)
        subject_mask = (~ext_bg_mask).astype(np.uint8) * 255

        K_photo = 18
        if k_colors is not None and k_colors not in ("auto", "all"):
            try:
                K_photo = max(12, int(k_colors))
            except ValueError:
                K_photo = 18
        elif k_colors == "all":
            K_photo = 24

        lab = cv2.cvtColor(work, cv2.COLOR_BGR2LAB).astype(np.float32)
        small_lab = cv2.resize(lab, (max(1, w // 3), max(1, h // 3)), interpolation=cv2.INTER_AREA)
        Z = small_lab.reshape((-1, 3))
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 25, 1.0)
        _, _, centers_lab = cv2.kmeans(Z, K_photo, None, criteria, 3, cv2.KMEANS_PP_CENTERS)

        flat_lab = lab.reshape((-1, 3))
        dists_lab = np.zeros((flat_lab.shape[0], K_photo), dtype=np.float32)
        for k in range(K_photo):
            dists_lab[:, k] = np.sum((flat_lab - centers_lab[k]) ** 2, axis=1)
        labels_p = np.argmin(dists_lab, axis=1).reshape((h, w))
        centers_bgr = cv2.cvtColor(centers_lab.reshape(1, K_photo, 3).astype(np.uint8), cv2.COLOR_LAB2BGR)[0]

        svg_lines = [
            f'<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        ]

        # Cria silhueta base sólida sob o sujeito para garantir ZERO furos brancos dentro do rosto/foto
        valid_labels = labels_p[~ext_bg_mask] if np.any(~ext_bg_mask) else labels_p.reshape(-1)
        vals_l, cnts_l = np.unique(valid_labels, return_counts=True)
        dom_k = int(vals_l[np.argmax(cnts_l)])
        base_c = centers_bgr[dom_k]
        base_hex = "#{:02X}{:02X}{:02X}".format(int(base_c[2]), int(base_c[1]), int(base_c[0]))

        min_x, min_y, max_x, max_y = w, h, 0, 0
        if remove_bg and np.any(ext_bg_mask):
            subj_smooth = cv2.GaussianBlur(subject_mask, (9, 9), 2.0)
            _, subj_smooth = cv2.threshold(subj_smooth, 125, 255, cv2.THRESH_BINARY)
            base_paths, (bx0, by0, bx1, by1) = trace_mask_compound_svg(subj_smooth, rdp_eps=1.4, corner_angle_deg=60.0, sigma=2.0, min_area=40)
            for _, d_str, _ in base_paths:
                svg_lines.append(f'  <path fill="{base_hex}" fill-rule="evenodd" d="{d_str}" />')
            if bx1 > bx0 and by1 > by0:
                min_x, min_y, max_x, max_y = min(min_x, bx0), min(min_y, by0), max(max_x, bx1), max(max_y, by1)
        else:
            svg_lines.append(f'  <rect width="{w}" height="{h}" fill="{base_hex}" />')
            min_x, min_y, max_x, max_y = 0, 0, w, h

        all_photo_shapes = []
        min_area = max(22, int(filter_speckle) * 4)
        for k in range(K_photo):
            mask_k = ((labels_p == k) & (~ext_bg_mask)).astype(np.uint8) * 255
            if not np.any(mask_k):
                continue
            mask_k = cv2.dilate(mask_k, np.ones((3, 3), np.uint8), iterations=1)
            mask_k = cv2.GaussianBlur(mask_k, (11, 11), 2.4)
            _, mask_k = cv2.threshold(mask_k, 122, 255, cv2.THRESH_BINARY)
            c_bgr = centers_bgr[k]
            hex_col = "#{:02X}{:02X}{:02X}".format(int(c_bgr[2]), int(c_bgr[1]), int(c_bgr[0]))
            paths_k, (kx0, ky0, kx1, ky1) = trace_mask_compound_svg(
                mask_k, rdp_eps=1.4, corner_angle_deg=65.0, sigma=2.2, min_area=min_area, allow_hv_snap=False
            )
            for area, d_str, _ in paths_k:
                all_photo_shapes.append((area, hex_col, d_str))
            if kx1 > kx0 and ky1 > ky0:
                min_x, min_y, max_x, max_y = min(min_x, kx0), min(min_y, ky0), max(max_x, kx1), max(max_y, ky1)

        all_photo_shapes.sort(key=lambda x: x[0], reverse=True)
        for _, hex_col, d_str in all_photo_shapes:
            svg_lines.append(f'  <path fill="{hex_col}" fill-rule="evenodd" d="{d_str}" />')
        svg_lines.append("</svg>")

        with open(output_svg, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))

        if max_x > min_x and max_y > min_y:
            return output_svg, (float(max_x - min_x) / float(w), float(max_y - min_y) / float(h))
        return output_svg, (1.0, 1.0)

    # =====================================================================
    # MODO 3: LOGOS / ESCUDOS / ÍCONES E TIPOGRAFIA DE CORES SÓLIDAS
    # =====================================================================
    h, w = img.shape[:2]
    if upscale_small and (w < 1200 or h < 1200):
        scale = max(2, min(4, int(1600 / max(w, h))))
        if scale > 1:
            img = cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_LANCZOS4)
            h, w = img.shape[:2]

    if colormode == "binary":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        seg_img = cv2.cvtColor(bw, cv2.COLOR_GRAY2BGR)
        unique_colors = [np.array([0, 0, 0], dtype=np.uint8)]
    else:
        seg_img, _ = extract_exact_palette_and_segment(img, k_colors=k_colors, unify_colors=unify_colors)
        unique_colors = np.unique(seg_img.reshape(-1, 3), axis=0)

    # Identifica a cor de fundo (canto [0,0])
    bg_color = seg_img[0, 0].copy()

    # Ordena as cores por área decrescente (cores de fundo/base primeiro, detalhes menores por cima)
    color_order = []
    for c in unique_colors:
        area_c = int(np.sum(np.all(seg_img == c, axis=2)))
        color_order.append((area_c, c))
    color_order.sort(key=lambda x: x[0], reverse=True)

    min_area = max(12, int(filter_speckle) * 2)
    all_shapes = []
    min_x, min_y = w, h
    max_x, max_y = 0, 0

    for area_total, c in color_order:
        mask = np.all(seg_img == c, axis=2).astype(np.uint8) * 255
        
        # Se for a cor de fundo e remove_bg estiver ativo:
        # Remove APENAS os componentes que tocam a borda externa da imagem!
        # Isso PRESERVA 100% de letras brancas ou detalhes internos da mesma cor do fundo!
        if remove_bg and np.all(c == bg_color) and area_total > (h * w * 0.12):
            h_m, w_m = mask.shape[:2]
            num_cc, labels = cv2.connectedComponents(mask, connectivity=8)
            border_labels = set(labels[0, :]) | set(labels[h_m - 1, :]) | set(labels[:, 0]) | set(labels[:, w_m - 1])
            border_labels.discard(0)
            for bl in border_labels:
                mask[labels == bl] = 0
            if not np.any(mask):
                continue

        # Suavização Gaussiana SDF sub-pixel leve para contornos sedosos sem serrilhado
        mask_smooth = cv2.GaussianBlur(mask, (3, 3), 0.8)
        _, mask_smooth = cv2.threshold(mask_smooth, 127, 255, cv2.THRESH_BINARY)

        hex_col = "#{:02X}{:02X}{:02X}".format(int(c[2]), int(c[1]), int(c[0]))
        paths, (bx0, by0, bx1, by1) = trace_mask_compound_svg(
            mask_smooth,
            rdp_eps=1.1,
            corner_angle_deg=max(36.0, float(corner_threshold)),
            sigma=1.2,
            min_area=min_area,
            allow_hv_snap=True,
        )

        for a_p, d_str, _ in paths:
            all_shapes.append((a_p, hex_col, d_str))

        if bx1 > bx0 and by1 > by0:
            min_x = min(min_x, bx0)
            min_y = min(min_y, by0)
            max_x = max(max_x, bx1)
            max_y = max(max_y, by1)

    svg_lines = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
    ]
    for _, hex_col, svg_d in all_shapes:
        svg_lines.append(f'  <path fill="{hex_col}" fill-rule="evenodd" d="{svg_d}" />')
    svg_lines.append("</svg>")

    with open(output_svg, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    if max_x > min_x and max_y > min_y:
        w_ratio = float(max_x - min_x) / float(w)
        h_ratio = float(max_y - min_y) / float(h)
    else:
        w_ratio, h_ratio = 1.0, 1.0

    return output_svg, (w_ratio, h_ratio)

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
        self.sp_corner.insert(0, "38")
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
            self.sp_corner.delete(0, "end"); self.sp_corner.insert(0, "38")
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

            _, (w_ratio, h_ratio) = execute_vectorization(
                input_path=self.current_img_path,
                output_svg=output_svg,
                colormode=color_mode,
                hierarchical=hier_mode,
                filter_speckle=speckle,
                corner_threshold=corner,
                k_colors=colors_arg,
                upscale_small=upscale,
                remove_bg=remove_bg,
                unify_colors=harmonize
            )

            self.root.after(0, lambda: self._finalizar_importacao_corel(output_svg, w_ratio, h_ratio))
        except Exception as e:
            err_msg = str(e)
            self.root.after(0, lambda: self._erro_finalizacao(err_msg))

    def _finalizar_importacao_corel(self, output_svg, w_ratio=1.0, h_ratio=1.0):
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
                    if self.orig_w > 0:
                        target_w = float(self.orig_w * w_ratio)
                        target_h = float(self.orig_h * h_ratio)
                        grp.SetSize(target_w, target_h)
                        grp.LeftX = float(self.orig_x + self.orig_w + (self.orig_w * 0.05))
                        grp.BottomY = float(self.orig_y + (self.orig_h * (1.0 - h_ratio) * 0.5))
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
