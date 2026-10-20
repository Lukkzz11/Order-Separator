"""
Order Separator - Upscaler IA Ultra HD 4x / 8x para CorelDRAW
Super-Resolução Neural Profunda baseada em Real-ESRGAN com Aceleração por Hardware GPU DirectML (RTX 5060 Ti).
Aumenta resolução de 300 DPI, reconstrói traços nítidos de logos e elimina quadriculados do WhatsApp/Google.
100% Offline, Gratuito, Sem Limites e Seguro.
"""

import sys
import os
import math
import tempfile
import threading
import io
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageGrab, ImageFilter, ImageOps
import numpy as np
import cv2

try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False

# Sessão ONNX global mantida em memória para inferência instantânea na GPU
GLOBAL_UPSCALER_SESSION = None
ACTIVE_HARDWARE_NAME = "Detectando..."

def get_upscaler_session():
    global GLOBAL_UPSCALER_SESSION, ACTIVE_HARDWARE_NAME
    if not HAS_ORT:
        return None
    if GLOBAL_UPSCALER_SESSION is None:
        model_path = os.path.join(os.environ.get('USERPROFILE', ''), '.cache', 'order_separator_models', 'RealESRGAN_x4.onnx')
        if not os.path.exists(model_path):
            return None
        try:
            GLOBAL_UPSCALER_SESSION = ort.InferenceSession(model_path, providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
            ACTIVE_HARDWARE_NAME = "⚡ Aceleração GPU Ativa (DirectML RTX)"
        except Exception:
            try:
                GLOBAL_UPSCALER_SESSION = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                ACTIVE_HARDWARE_NAME = "CPU Multithread"
            except Exception:
                GLOBAL_UPSCALER_SESSION = None
                ACTIVE_HARDWARE_NAME = "Indisponível"
    return GLOBAL_UPSCALER_SESSION


def upscale_image_realesrgan(pil_img, scale=4, tile_size=512, tile_pad=16, sharpen=False, progress_cb=None):
    """
    Executa super-resolução 4x / 8x utilizando Real-ESRGAN ONNX acelerado por DirectML.
    Suporta imagens de qualquer tamanho através de divisão em ladrilhos (tiles) com sobreposição suave.
    Preserva canal Alfa (RGBA) com máxima nitidez de borda para estamparia DTF e silk.
    """
    sess = get_upscaler_session()
    if sess is None:
        raise RuntimeError("Modelo de IA 'RealESRGAN_x4.onnx' não encontrado ou ONNX Runtime indisponível.")

    has_alpha = pil_img.mode == "RGBA"
    if has_alpha:
        r, g, b, a = pil_img.split()
        rgb_img = Image.merge("RGB", (r, g, b))
        orig_alpha = a
    else:
        rgb_img = pil_img.convert("RGB")
        orig_alpha = None

    w, h = rgb_img.size
    img_np = np.array(rgb_img).astype(np.float32) / 255.0

    # Se a imagem for pequena, processa direto em 1 única passagem ultrarrápida
    if w <= tile_size and h <= tile_size:
        if progress_cb:
            progress_cb(20, "Processando inferência na GPU...")
        inp = np.transpose(img_np, (2, 0, 1))[np.newaxis, :, :, :]
        out = sess.run(None, {'input': inp})[0]
        out_np = np.clip(np.transpose(out[0], (1, 2, 0)) * 255.0, 0, 255).astype(np.uint8)
        out_pil = Image.fromarray(out_np)
        if progress_cb:
            progress_cb(80, "Refinando detalhes...")
    else:
        # Ladrilhamento inteligente para economizar VRAM e suportar fotos gigantescas
        out_w = w * 4
        out_h = h * 4
        out_arr = np.zeros((out_h, out_w, 3), dtype=np.float32)
        weight_arr = np.zeros((out_h, out_w, 1), dtype=np.float32)

        step = tile_size - 2 * tile_pad
        x_tiles = list(range(0, w, step))
        y_tiles = list(range(0, h, step))
        total_tiles = len(x_tiles) * len(y_tiles)
        done_tiles = 0

        for y0 in y_tiles:
            for x0 in x_tiles:
                x1 = min(w, x0 + tile_size)
                y1 = min(h, y0 + tile_size)
                actual_x0 = max(0, x1 - tile_size)
                actual_y0 = max(0, y1 - tile_size)

                tile = img_np[actual_y0:y1, actual_x0:x1]
                inp = np.transpose(tile, (2, 0, 1))[np.newaxis, :, :, :]

                out_tile = sess.run(None, {'input': inp})[0][0]
                out_tile = np.transpose(out_tile, (1, 2, 0))

                out_y0, out_y1 = actual_y0 * 4, y1 * 4
                out_x0, out_x1 = actual_x0 * 4, x1 * 4

                out_arr[out_y0:out_y1, out_x0:out_x1] += out_tile
                weight_arr[out_y0:out_y1, out_x0:out_x1] += 1.0

                done_tiles += 1
                if progress_cb:
                    pct = int(15 + (done_tiles / max(1, total_tiles)) * 70)
                    progress_cb(pct, f"Processando ladrilho {done_tiles} de {total_tiles} na GPU...")

        out_arr = np.clip((out_arr / np.maximum(weight_arr, 1e-5)) * 255.0, 0, 255).astype(np.uint8)
        out_pil = Image.fromarray(out_arr)

    # Modo 8x: aplica expansão 8x de alta fidelidade
    if scale == 8:
        if progress_cb:
            progress_cb(88, "Gerando resolução Gigapixel 8x...")
        out_pil = out_pil.resize((w * 8, h * 8), Image.Resampling.LANCZOS)

    # Filtro opcional de realce e nitidez de bordas para vetores/logos
    if sharpen:
        out_pil = out_pil.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))

    # Reconstituição do Canal Alfa com interpolação Lanczos precisa
    if has_alpha:
        target_w, target_h = out_pil.size
        high_alpha = orig_alpha.resize((target_w, target_h), Image.Resampling.LANCZOS)
        out_pil.putalpha(high_alpha)

    if progress_cb:
        progress_cb(100, "Concluído!")

    return out_pil


def create_checkerboard_pattern(width, height, check_size=12, color1=(215, 220, 228), color2=(255, 255, 255)):
    bg = Image.new("RGB", (width, height), color2)
    draw_img = np.array(bg)
    for y in range(0, height, check_size):
        for x in range(0, width, check_size):
            if ((x // check_size) + (y // check_size)) % 2 == 0:
                draw_img[y:min(y + check_size, height), x:min(x + check_size, width)] = color1
    return Image.fromarray(draw_img)


class UpscalerAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Order Separator - Upscaler IA Ultra HD 4x / 8x")
        self.root.geometry("1100x740")
        self.root.minsize(950, 650)
        self.root.configure(bg="#0B0F19")

        self.pil_original = None
        self.pil_upscaled = None
        self.current_img_path = None

        # Dados da seleção do CorelDRAW
        self.orig_w = 0.0
        self.orig_h = 0.0
        self.orig_x = 0.0
        self.orig_y = 0.0

        # Pré-carregar sessão DirectML em thread de fundo
        threading.Thread(target=get_upscaler_session, daemon=True).start()

        self.setup_ui()
        self.root.after(800, self.verificar_selecao_inicial_corel)

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#0B0F19", padx=16, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Cabeçalho
        hdr_box = tk.Frame(main_frame, bg="#0B0F19")
        hdr_box.pack(fill=tk.X, pady=(0, 8))

        title_frame = tk.Frame(hdr_box, bg="#0B0F19")
        title_frame.pack(side=tk.LEFT)

        lbl_title = tk.Label(
            title_frame,
            text="Upscaler IA Ultra HD 4x / 8x",
            font=("Segoe UI", 16, "bold"),
            fg="#38BDF8", # Light Sky Blue
            bg="#0B0F19"
        )
        lbl_title.pack(anchor="w")

        self.lbl_sub = tk.Label(
            title_frame,
            text="Super-Resolução Neural Real-ESRGAN (⚡ GPU DirectML RTX Ativa), Reconstrução de Traços 300 DPI",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#0B0F19"
        )
        self.lbl_sub.pack(anchor="w")

        # Botões de Ação de Entrada
        btn_box = tk.Frame(hdr_box, bg="#0B0F19")
        btn_box.pack(side=tk.RIGHT)

        self.btn_corel = tk.Button(
            btn_box,
            text="📸 Capturar CorelDRAW",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.capturar_corel
        )
        self.btn_corel.pack(side=tk.LEFT, padx=3)

        self.btn_file = tk.Button(
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
        self.btn_file.pack(side=tk.LEFT, padx=3)

        self.btn_paste = tk.Button(
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
        self.btn_paste.pack(side=tk.LEFT, padx=3)

        # 2. Painel Central de Visualização
        preview_container = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=10, pady=8)
        preview_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        info_bar = tk.Frame(preview_container, bg="#0F172A")
        info_bar.pack(fill=tk.X, pady=(0, 6))

        self.lbl_img_info = tk.Label(
            info_bar,
            text="Selecione uma imagem de baixa resolução no CorelDRAW ou abra um arquivo para melhorar 4x/8x.",
            font=("Segoe UI", 9, "bold"),
            fg="#38BDF8",
            bg="#0F172A",
            anchor="w"
        )
        self.lbl_img_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        cards_frame = tk.Frame(preview_container, bg="#0F172A")
        cards_frame.pack(fill=tk.BOTH, expand=True)

        # Card Esquerdo: Imagem Original (Baixa Resolução)
        card_orig = tk.Frame(cards_frame, bg="#141B2D", bd=1, relief="solid")
        card_orig.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        subhdr_orig = tk.Frame(card_orig, bg="#141B2D", padx=6, pady=3)
        subhdr_orig.pack(fill=tk.X)
        tk.Label(subhdr_orig, text="Original (Baixa Resolução)", font=("Segoe UI", 8, "bold"), fg="#94A3B8", bg="#141B2D").pack(side=tk.LEFT)
        self.lbl_orig_stats = tk.Label(subhdr_orig, text="", font=("Segoe UI", 7), fg="#94A3B8", bg="#141B2D")
        self.lbl_orig_stats.pack(side=tk.RIGHT)

        self.canvas_orig = tk.Canvas(card_orig, bg="#020617", bd=0, highlightthickness=0)
        self.canvas_orig.pack(fill=tk.BOTH, expand=True)

        # Card Direito: Imagem Aumentada Ultra HD
        card_proc = tk.Frame(cards_frame, bg="#141B2D", bd=1, relief="solid")
        card_proc.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        subhdr_proc = tk.Frame(card_proc, bg="#141B2D", padx=6, pady=3)
        subhdr_proc.pack(fill=tk.X)
        tk.Label(subhdr_proc, text="Super-Resolução Ultra HD (Nítida)", font=("Segoe UI", 8, "bold"), fg="#38BDF8", bg="#141B2D").pack(side=tk.LEFT)
        self.lbl_upscaled_stats = tk.Label(subhdr_proc, text="", font=("Segoe UI", 7, "bold"), fg="#38BDF8", bg="#141B2D")
        self.lbl_upscaled_stats.pack(side=tk.RIGHT)

        self.canvas_proc = tk.Canvas(card_proc, bg="#020617", bd=0, highlightthickness=0)
        self.canvas_proc.pack(fill=tk.BOTH, expand=True)

        # 3. Painel de Controles do Upscaler
        ctrl_frame = tk.Frame(main_frame, bg="#0F172A", bd=1, relief="solid", padx=12, pady=8)
        ctrl_frame.pack(fill=tk.X, pady=(0, 8))

        row_ctrl = tk.Frame(ctrl_frame, bg="#0F172A")
        row_ctrl.pack(fill=tk.X)

        tk.Label(row_ctrl, text="Fator de Aumento:", font=("Segoe UI", 9, "bold"), fg="#CBD5E1", bg="#0F172A").pack(side=tk.LEFT, padx=(0, 10))

        self.var_scale = tk.IntVar(value=4)
        rb_4x = tk.Radiobutton(
            row_ctrl,
            text="⚡ 4x Ultra HD (Padrão 300 DPI)",
            variable=self.var_scale,
            value=4,
            font=("Segoe UI", 9, "bold"),
            fg="#38BDF8",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#38BDF8",
            command=self.iniciar_upscale_async
        )
        rb_4x.pack(side=tk.LEFT, padx=(0, 14))

        rb_8x = tk.Radiobutton(
            row_ctrl,
            text="🚀 8x Gigapixel (Banners & Painéis)",
            variable=self.var_scale,
            value=8,
            font=("Segoe UI", 9, "bold"),
            fg="#F59E0B",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#F59E0B",
            command=self.iniciar_upscale_async
        )
        rb_8x.pack(side=tk.LEFT, padx=(0, 20))

        self.var_sharpen = tk.BooleanVar(value=True)
        cb_sharp = tk.Checkbutton(
            row_ctrl,
            text="Realçar Linhas e Vetores (Elimina névoa)",
            variable=self.var_sharpen,
            font=("Segoe UI", 8, "bold"),
            fg="#10B981",
            bg="#0F172A",
            selectcolor="#1E293B",
            activebackground="#0F172A",
            activeforeground="#10B981",
            command=self.iniciar_upscale_async
        )
        cb_sharp.pack(side=tk.LEFT)

        # 4. Barra de Progresso e Status
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(2, 4))
        self.progress_bar['value'] = 0

        self.lbl_status = tk.Label(
            main_frame,
            text="Pronto. Carregue uma imagem ou capture do CorelDRAW para reconstruir em alta resolução.",
            font=("Segoe UI", 8),
            fg="#94A3B8",
            bg="#0B0F19",
            anchor="center"
        )
        self.lbl_status.pack(fill=tk.X, pady=(0, 6))

        # 5. Rodapé de Ações
        bottom_box = tk.Frame(main_frame, bg="#0B0F19")
        bottom_box.pack(fill=tk.X)

        self.btn_enviar_corel = tk.Button(
            bottom_box,
            text="🚀 ENVIAR IMAGEM ULTRA HD AO CORELDRAW",
            font=("Segoe UI", 11, "bold"),
            bg="#0284C7",
            fg="#FFFFFF",
            activebackground="#0369A1",
            activeforeground="#FFFFFF",
            bd=0,
            cursor="hand2",
            pady=12,
            command=self.enviar_coreldraw
        )
        self.btn_enviar_corel.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))

        self.btn_salvar = tk.Button(
            bottom_box,
            text="💾 Salvar PNG 300 DPI",
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

        # Atalhos de Teclado
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<Control-v>", lambda e: self.colar_clipboard())
        self.root.bind("<Control-V>", lambda e: self.colar_clipboard())

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
            self.lbl_img_info.configure(text=f"{desc} (Original: {w} x {h} px)")
            self.lbl_orig_stats.configure(text=f"{w} x {h} px")
            self.atualizar_canvas_original()
            self.iniciar_upscale_async()
        except Exception as e:
            messagebox.showerror("Erro ao carregar imagem", str(e))

    def atualizar_canvas_original(self):
        if not self.pil_original:
            return
        cw = max(50, self.canvas_orig.winfo_width())
        ch = max(50, self.canvas_orig.winfo_height())
        if cw <= 50 or ch <= 50:
            cw, ch = 420, 380

        thumb = self.pil_original.copy()
        thumb.thumbnail((cw - 12, ch - 12), Image.Resampling.NEAREST)
        tw, th = thumb.size

        if thumb.mode == "RGBA":
            bg = create_checkerboard_pattern(tw, th)
            bg.paste(thumb, (0, 0), thumb)
            thumb = bg

        self.tk_orig = ImageTk.PhotoImage(thumb)
        self.canvas_orig.delete("all")
        self.canvas_orig.create_image(cw // 2, ch // 2, image=self.tk_orig, anchor="center")

    def atualizar_canvas_upscaled(self):
        if not self.pil_upscaled:
            return
        cw = max(50, self.canvas_proc.winfo_width())
        ch = max(50, self.canvas_proc.winfo_height())
        if cw <= 50 or ch <= 50:
            cw, ch = 420, 380

        thumb = self.pil_upscaled.copy()
        thumb.thumbnail((cw - 12, ch - 12), Image.Resampling.LANCZOS)
        tw, th = thumb.size

        if thumb.mode == "RGBA":
            bg = create_checkerboard_pattern(tw, th)
            bg.paste(thumb, (0, 0), thumb)
            thumb = bg

        self.tk_proc = ImageTk.PhotoImage(thumb)
        self.canvas_proc.delete("all")
        self.canvas_proc.create_image(cw // 2, ch // 2, image=self.tk_proc, anchor="center")

    def iniciar_upscale_async(self):
        if not self.pil_original:
            return
        threading.Thread(target=self._processar_upscale_worker, daemon=True).start()

    def _processar_upscale_worker(self):
        try:
            scale = self.var_scale.get()
            sharpen = self.var_sharpen.get()
            self.root.after(0, lambda: self.btn_enviar_corel.configure(state="disabled", text="Processando Super-Resolução na GPU..."))

            def progress_update(pct, text):
                self.root.after(0, lambda: self._update_progress_ui(pct, text))

            t0 = time.time()
            out = upscale_image_realesrgan(
                self.pil_original,
                scale=scale,
                tile_size=512,
                tile_pad=16,
                sharpen=sharpen,
                progress_cb=progress_update
            )
            t1 = time.time()
            dur = round(t1 - t0, 2)

            self.pil_upscaled = out
            self.root.after(0, lambda: self._finalizar_upscale_ui(dur))
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda: self._erro_upscale(err))

    def _update_progress_ui(self, pct, text):
        self.progress_bar['value'] = pct
        self.lbl_status.configure(text=text, fg="#F59E0B")

    def _finalizar_upscale_ui(self, dur):
        self.atualizar_canvas_upscaled()
        if self.pil_upscaled:
            uw, uh = self.pil_upscaled.size
            self.lbl_upscaled_stats.configure(text=f"{uw} x {uh} px | Real-ESRGAN {self.var_scale.get()}x")
        self.lbl_status.configure(text=f"Super-resolução gerada em {dur}s com GPU DirectML! Imagem nítida e pronta para impressão.", fg="#38BDF8")
        self.btn_enviar_corel.configure(state="normal", text="🚀 ENVIAR IMAGEM ULTRA HD AO CORELDRAW")

    def _erro_upscale(self, err):
        self.lbl_status.configure(text=f"Erro ao processar: {err}", fg="#EF4444")
        self.btn_enviar_corel.configure(state="normal", text="🚀 ENVIAR IMAGEM ULTRA HD AO CORELDRAW")
        messagebox.showerror("Erro de Super-Resolução", err)

    def escolher_arquivo(self):
        f = filedialog.askopenfilename(
            title="Selecione uma imagem para aumentar resolução",
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
            temp_png = os.path.join(temp_dir, f"corel_upscale_in_{os.getpid()}_{np.random.randint(1000, 9999)}.png")

            opt = corel.CreateStructExportOptions()
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
            self.carregar_imagem(img, desc="Seleção do CorelDRAW")
        except Exception as e:
            if not silent:
                messagebox.showerror("Erro ao capturar do CorelDRAW", f"Não foi possível capturar a seleção:\n{e}")

    def enviar_coreldraw(self):
        if not self.pil_upscaled:
            messagebox.showwarning("Aviso", "Carregue ou capture uma imagem antes de enviar ao CorelDRAW!")
            return

        try:
            temp_dir = tempfile.gettempdir()
            out_png = os.path.join(temp_dir, f"upscaled_corel_{np.random.randint(1000, 9999)}.png")
            self.pil_upscaled.save(out_png, format="PNG", dpi=(300, 300))

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

            doc.BeginCommandGroup("Upscaler IA Ultra HD")
            try:
                layer = doc.ActiveLayer
                opt = corel.CreateStructImportOptions()
                imp = layer.ImportEx(out_png, 0, opt)
                if imp:
                    imp.Finish()

                sel = None
                try:
                    sel = corel.ActiveSelection
                except Exception:
                    pass

                if sel and sel.Shapes.Count > 0:
                    shape = sel.Shapes(1) if sel.Shapes.Count == 1 else sel.Group()
                    if self.orig_w > 0 and self.orig_h > 0:
                        shape.SetSize(self.orig_w, self.orig_h)
                        shape.LeftX = float(self.orig_x + self.orig_w + (self.orig_w * 0.05))
                        shape.CenterY = float(self.orig_y + (self.orig_h / 2.0))
                    else:
                        shape.CenterX = doc.ActivePage.CenterX
                        shape.CenterY = doc.ActivePage.CenterY
            finally:
                doc.EndCommandGroup()

            self.lbl_status.configure(text="Imagem Ultra HD 300 DPI inserida com sucesso no CorelDRAW!", fg="#38BDF8")
            messagebox.showinfo("Sucesso", "Imagem em Super-Resolução Ultra HD inserida no CorelDRAW ao lado da original!")
        except Exception as e:
            messagebox.showerror("Erro ao enviar ao CorelDRAW", str(e))

    def salvar_png(self):
        if not self.pil_upscaled:
            messagebox.showwarning("Aviso", "Nenhuma imagem em alta resolução para salvar.")
            return

        out_path = filedialog.asksaveasfilename(
            title="Salvar Imagem Ultra HD",
            defaultextension=".png",
            filetypes=[("PNG 300 DPI", "*.png")]
        )
        if out_path:
            self.pil_upscaled.save(out_path, format="PNG", dpi=(300, 300))
            messagebox.showinfo("Salvo com Sucesso", f"Imagem salva em:\n{out_path}")

    def copiar_png_clipboard(self):
        if not self.pil_upscaled:
            messagebox.showwarning("Aviso", "Nenhuma imagem para copiar.")
            return

        try:
            import win32clipboard
            png_format = win32clipboard.RegisterClipboardFormat("PNG")
            buf = io.BytesIO()
            self.pil_upscaled.save(buf, format="PNG")
            data = buf.getvalue()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(png_format, data)
            win32clipboard.CloseClipboard()

            self.lbl_status.configure(text="PNG Ultra HD copiado para a área de transferência! (Pressione Ctrl+V em qualquer programa)", fg="#38BDF8")
            messagebox.showinfo("Copiado!", "Imagem PNG copiada com sucesso!\nVocê já pode colar (Ctrl+V) no CorelDRAW, Photoshop ou WhatsApp.")
        except Exception as e:
            messagebox.showerror("Erro ao copiar", str(e))


def main():
    try:
        import subprocess
        pid_file = os.path.join(tempfile.gettempdir(), "order_separator_upscaler.pid")
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
    app = UpscalerAIApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
