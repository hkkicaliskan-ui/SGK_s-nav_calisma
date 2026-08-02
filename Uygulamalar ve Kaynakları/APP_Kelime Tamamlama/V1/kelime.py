import os
import re
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import RIGHT


class ModernAutoSuggestEditorPro:
    """
    TextCraft Pro v3 — Akıllı İçerik Editörü, Otomatik Tamamlama & Log Yöneticisi
    """
    COLORS = {
        "bg_dark": "#1e1e2e",
        "bg_sidebar": "#181825",
        "bg_editor": "#11111b",
        "bg_card": "#313244",
        "text_main": "#cdd6f4",
        "text_muted": "#a6adc8",
        "accent": "#89b4fa",
        "accent_hover": "#b4befe",
        "border": "#45475a",
        "popup_bg": "#1e1e2e",
        "popup_sel": "#45475a"
    }

    def __init__(self, root):
        self.root = root
        self.root.title("TextCraft Pro v3 — Akıllı Editör & Log Yöneticisi")
        self.root.geometry("1150x750")
        self.root.minsize(950, 650)
        self.root.configure(bg=self.COLORS["bg_dark"])

        # Klasör ve Dosya Yolları
        self.logs_dir = "logs"
        self.word_logs_dir = os.path.join(self.logs_dir, "kelime_kayitlari")
        os.makedirs(self.word_logs_dir, exist_ok=True)

        self.activity_log_file = os.path.join(self.logs_dir, "sistem_aktiviteleri.log")
        self.pool_file_path = "kelime_havuzu.txt"

        # Değişkenler
        self.current_file_path = None
        self.word_pool = set()
        self.min_char_length = tk.IntVar(value=2)
        self.auto_learn_on_save = tk.BooleanVar(value=True)

        # Kurulumlar
        self._setup_styles()
        self._setup_ui()
        self._ensure_sample_pool()
        self.load_word_pool()
        
        # Olay Bağlantıları ve Sağ Tık Menüsü
        self._create_context_menu()
        self._bind_events()

        self._log_activity("UYGULAMA_BASLATILDI", "TextCraft Pro oturumu başlatıldı.")

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.style.configure(".", background=self.COLORS["bg_dark"], foreground=self.COLORS["text_main"], font=("Segoe UI", 10))
        self.style.configure("Sidebar.TFrame", background=self.COLORS["bg_sidebar"])
        self.style.configure("Card.TFrame", background=self.COLORS["bg_card"], relief="flat")
        self.style.configure("Status.TFrame", background=self.COLORS["bg_sidebar"])

        self.style.configure("Primary.TButton", background=self.COLORS["accent"], foreground="#11111b", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        self.style.map("Primary.TButton", background=[("active", self.COLORS["accent_hover"])])

        self.style.configure("Secondary.TButton", background=self.COLORS["bg_card"], foreground=self.COLORS["text_main"], font=("Segoe UI", 9), borderwidth=0, padding=6)
        self.style.map("Secondary.TButton", background=[("active", self.COLORS["border"])])

        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground=self.COLORS["text_main"], background=self.COLORS["bg_sidebar"])
        self.style.configure("Muted.TLabel", font=("Segoe UI", 9), foreground=self.COLORS["text_muted"], background=self.COLORS["bg_sidebar"])
        self.style.configure("Status.TLabel", font=("Segoe UI", 9), foreground=self.COLORS["text_muted"], background=self.COLORS["bg_sidebar"])

    def _setup_ui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- 1. SOL PANEL (Sidebar) ---
        sidebar = ttk.Frame(main_container, style="Sidebar.TFrame", width=300)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
        sidebar.pack_propagate(False)

        ttk.Label(sidebar, text="⚡ TextCraft Pro", style="Header.TLabel").pack(anchor="w", padx=18, pady=(20, 3))
        ttk.Label(sidebar, text="Akıllı Editör & Loglama Sistemi", style="Muted.TLabel").pack(anchor="w", padx=18, pady=(0, 15))

        # Tamamlama Ayarları
        card_settings = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        card_settings.pack(fill=tk.X, padx=15, pady=5)

        ttk.Label(card_settings, text="TAMAMLAMA AYARLARI", font=("Segoe UI", 8, "bold"), foreground=self.COLORS["accent"], background=self.COLORS["bg_card"]).pack(anchor="w", pady=(0, 8))

        lbl_threshold = ttk.Label(card_settings, text=f"Tetikleme Sınırı: {self.min_char_length.get()} Harf", font=("Segoe UI", 9), background=self.COLORS["bg_card"])
        lbl_threshold.pack(anchor="w")

        def on_slider_change(val):
            v = int(float(val))
            self.min_char_length.set(v)
            lbl_threshold.config(text=f"Tetikleme Sınırı: {v} Harf")

        slider = ttk.Scale(card_settings, from_=1, to=5, value=self.min_char_length.get(), command=on_slider_change)
        slider.pack(fill=tk.X, pady=(4, 0))

        chk_learn = tk.Checkbutton(
            card_settings,
            text="Kaydederken Kelimeleri\nHavuza Otomatik Ekle",
            variable=self.auto_learn_on_save,
            bg=self.COLORS["bg_card"],
            fg=self.COLORS["text_main"],
            activebackground=self.COLORS["bg_card"],
            activeforeground=self.COLORS["accent"],
            selectcolor=self.COLORS["bg_dark"],
            font=("Segoe UI", 9),
            justify="left"
        )
        chk_learn.pack(anchor="w", pady=(10, 0))

        # Havuz ve Log Yönetimi Kartı
        card_pool = ttk.Frame(sidebar, style="Card.TFrame", padding=12)
        card_pool.pack(fill=tk.X, padx=15, pady=12)

        ttk.Label(card_pool, text="HAVUZ VE LOG YÖNETİMİ", font=("Segoe UI", 8, "bold"), foreground=self.COLORS["accent"], background=self.COLORS["bg_card"]).pack(anchor="w", pady=(0, 8))

        self.lbl_pool_info = ttk.Label(card_pool, text="Yükleniyor...", font=("Segoe UI", 9), foreground=self.COLORS["text_muted"], background=self.COLORS["bg_card"])
        self.lbl_pool_info.pack(anchor="w", pady=(0, 10))

        ttk.Button(card_pool, text="📁 Havuz Dosyası Seç", style="Secondary.TButton", command=self.select_pool_file).pack(fill=tk.X, pady=2)
        ttk.Button(card_pool, text="🔄 Havuzu Yenile", style="Secondary.TButton", command=self.load_word_pool).pack(fill=tk.X, pady=2)
        ttk.Button(card_pool, text="🔍 Kelime Havuzunu Gör", style="Secondary.TButton", command=self.open_pool_viewer).pack(fill=tk.X, pady=2)
        ttk.Button(card_pool, text="📜 Aktivite Loglarını Aç", style="Secondary.TButton", command=self.open_activity_log).pack(fill=tk.X, pady=2)
        ttk.Button(card_pool, text="📂 Kelime Rapor Klasörü", style="Secondary.TButton", command=self.open_word_logs_folder).pack(fill=tk.X, pady=2)

        # --- 2. SAĞ PANEL (Editör Paneli) ---
        editor_container = ttk.Frame(main_container)
        editor_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Üst Araç Çubuğu (Dosya İşlemleri + Kopyala/Yapıştır)
        toolbar = ttk.Frame(editor_container, padding=(15, 10))
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="📄 Yeni", style="Secondary.TButton", command=self.new_file).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(toolbar, text="📂 Aç", style="Secondary.TButton", command=self.open_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="💾 Kaydet", style="Primary.TButton", command=self.save_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="💾 Farklı Kaydet", style="Secondary.TButton", command=self.save_file_as).pack(side=tk.LEFT, padx=4)

        # Kopyala / Yapıştır / Kes Butonları
        ttk.Button(toolbar, text="✂️ Kes", style="Secondary.TButton", command=self.cut_text).pack(side=tk.LEFT, padx=(15, 2))
        ttk.Button(toolbar, text="📋 Kopyala", style="Secondary.TButton", command=self.copy_text).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📌 Yapıştır", style="Secondary.TButton", command=self.paste_text).pack(side=tk.LEFT, padx=2)

        self.lbl_file_status = ttk.Label(toolbar, text="Yeni Belge", font=("Segoe UI", 9, "italic"), foreground=self.COLORS["text_muted"])
        self.lbl_file_status.pack(side=tk.RIGHT, padx=10)

        # Metin Editör Alanı
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.text_area = tk.Text(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 12),
            bg=self.COLORS["bg_editor"],
            fg=self.COLORS["text_main"],
            insertbackground=self.COLORS["accent"],
            selectbackground=self.COLORS["popup_sel"],
            selectforeground=self.COLORS["text_main"],
            relief="flat",
            padx=15,
            pady=15,
            undo=True
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, command=self.text_area.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_area.configure(yscrollcommand=scrollbar.set)

        # Alt Durum Çubuğu
        statusbar = ttk.Frame(editor_container, style="Status.TFrame", padding=(15, 6))
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_stats = ttk.Label(statusbar, text="Karakter: 0 | Kelime: 0 | Benzersiz Kelime: 0", style="Status.TLabel")
        self.lbl_stats.pack(side=tk.LEFT)

        self.lbl_last_action = ttk.Label(statusbar, text="Hazır", style="Status.TLabel")
        self.lbl_last_action.pack(side=RIGHT)

        # Otomatik Tamamlama Pop-up Kutusu
        self.popup = tk.Listbox(
            self.root,
            font=("Segoe UI", 10),
            bg=self.COLORS["popup_bg"],
            fg=self.COLORS["text_main"],
            selectbackground=self.COLORS["accent"],
            selectforeground="#11111b",
            highlightthickness=1,
            highlightbackground=self.COLORS["border"],
            relief="flat"
        )
        self.popup_visible = False

    def _create_context_menu(self):
        """Sağ Tık Kopyala - Yapıştır - Kes Menüsü"""
        self.context_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=self.COLORS["bg_card"],
            fg=self.COLORS["text_main"],
            activebackground=self.COLORS["accent"],
            activeforeground="#11111b"
        )
        self.context_menu.add_command(label="✂️ Kes (Ctrl+X)", command=self.cut_text)
        self.context_menu.add_command(label="📋 Kopyala (Ctrl+C)", command=self.copy_text)
        self.context_menu.add_command(label="📌 Yapıştır (Ctrl+V)", command=self.paste_text)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Tümünü Seç (Ctrl+A)", command=self.select_all_text)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def cut_text(self):
        self.text_area.event_generate("<<Cut>>")
        self._update_stats()

    def copy_text(self):
        self.text_area.event_generate("<<Copy>>")

    def paste_text(self):
        self.text_area.event_generate("<<Paste>>")
        self._update_stats()

    def select_all_text(self):
        self.text_area.tag_add("sel", "1.0", "end")

    def _bind_events(self):
        self.text_area.bind("<KeyRelease>", self.on_key_release)
        self.text_area.bind("<Key>", self.on_key_press)
        self.popup.bind("<ButtonRelease-1>", self.insert_selected_word)
        self.root.bind("<Configure>", lambda e: self.hide_popup())

        # Sağ Tık Bağlantısı (Windows: Button-3, Mac: Button-2)
        self.text_area.bind("<Button-3>", self.show_context_menu)
        self.text_area.bind("<Button-2>", self.show_context_menu)

    def _log_activity(self, event_type, details):
        """Genel sistem aktivite log dosyasına yazar."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{event_type}] {details}\n"
        try:
            with open(self.activity_log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Aktivite log yazma hatası: {e}")

    def _ensure_sample_pool(self):
        if not os.path.exists(self.pool_file_path):
            sample_words = [
                "gösteri", "gösterge", "göstermek", "görsel", "gökyüzü", "görev", "geliştirme",
                "otomasyon", "uygulama", "python", "yazılım", "teknoloji", "algoritma",
                "performans", "optimizasyon", "profesyonel", "dokümantasyon", "mimarisi"
            ]
            with open(self.pool_file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(sample_words))

    def load_word_pool(self):
        if not os.path.exists(self.pool_file_path):
            self.lbl_pool_info.config(text="Dosya Bulunamadı!")
            return

        try:
            with open(self.pool_file_path, "r", encoding="utf-8") as f:
                words = [line.strip().lower() for line in f if line.strip()]
                self.word_pool = set(words)
            
            file_name = os.path.basename(self.pool_file_path)
            self.lbl_pool_info.config(text=f"• {len(self.word_pool)} Aktif Kelime\n• {file_name}")
            self.lbl_last_action.config(text=f"Havuz yüklendi: {len(self.word_pool)} kelime")
        except Exception as e:
            messagebox.showerror("Hata", f"Kelime havuzu okunamadı:\n{e}")

    def select_pool_file(self):
        selected = filedialog.askopenfilename(
            title="Kelime Havuzu Dosyası Seç",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if selected:
            self.pool_file_path = selected
            self.load_word_pool()
            self._log_activity("HAVUZ_DEGISTIRILDI", f"Yeni havuz dosyası yüklendi: {selected}")

    def get_current_word_info(self):
        cursor_pos = self.text_area.index(tk.INSERT)
        line, col = cursor_pos.split(".")
        line_text = self.text_area.get(f"{line}.0", cursor_pos)

        match = re.search(r'([a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+)$', line_text)
        if match:
            current_word = match.group(1)
            start_col = match.start()
            return current_word, f"{line}.{start_col}", cursor_pos
        return "", cursor_pos, cursor_pos

    def show_popup(self, matches, position_index):
        self.popup.delete(0, tk.END)
        for w in sorted(matches)[:8]:
            self.popup.insert(tk.END, f"  {w}")

        self.popup.select_set(0)

        bbox = self.text_area.bbox(position_index)
        if bbox:
            x, y, _, height = bbox
            self.popup.place(x=x + 15, y=y + height + 45, width=220, height=min(len(matches) * 22 + 10, 160))
            self.popup.lift()
            self.popup_visible = True

    def hide_popup(self):
        if self.popup_visible:
            self.popup.place_forget()
            self.popup_visible = False

    def on_key_release(self, event):
        self._update_stats()

        if event.keysym in ("Up", "Down", "Return", "Tab", "Escape", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return

        current_word, start_idx, cursor_idx = self.get_current_word_info()
        min_len = self.min_char_length.get()

        if len(current_word) >= min_len:
            prefix = current_word.lower()
            matches = [w for w in self.word_pool if w.startswith(prefix) and w != prefix]

            if matches:
                self.show_popup(matches, start_idx)
            else:
                self.hide_popup()
        else:
            self.hide_popup()

    def on_key_press(self, event):
        if not self.popup_visible:
            return

        if event.keysym == "Down":
            sel = self.popup.curselection()
            if sel:
                nxt = (sel[0] + 1) % self.popup.size()
                self.popup.select_clear(0, tk.END)
                self.popup.select_set(nxt)
                self.popup.see(nxt)
            return "break"

        elif event.keysym == "Up":
            sel = self.popup.curselection()
            if sel:
                prv = (sel[0] - 1) % self.popup.size()
                self.popup.select_clear(0, tk.END)
                self.popup.select_set(prv)
                self.popup.see(prv)
            return "break"

        elif event.keysym in ("Return", "Tab"):
            self.insert_selected_word()
            return "break"

        elif event.keysym == "Escape":
            self.hide_popup()
            return "break"

    def insert_selected_word(self, event=None):
        if not self.popup_visible:
            return

        sel = self.popup.curselection()
        if not sel:
            return

        selected_word = self.popup.get(sel[0]).strip()
        current_word, start_idx, cursor_idx = self.get_current_word_info()

        self.text_area.delete(start_idx, cursor_idx)
        self.text_area.insert(start_idx, selected_word + " ")
        self.hide_popup()

    def _update_stats(self):
        content = self.text_area.get("1.0", tk.END).strip()
        char_count = len(content)
        words = re.findall(r'[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+', content.lower())
        word_count = len(words)
        unique_word_count = len(set(words))

        self.lbl_stats.config(text=f"Karakter: {char_count} | Kelime: {word_count} | Benzersiz Kelime: {unique_word_count}")

    def _sync_words_to_pool_and_log(self, text_content, saved_file_path):
        """
        1. Belgedeki kelimeleri havuza aktarır.
        2. Aktivite log kaydı oluşturur.
        3. Eklenen kelimeleri 'eklenen_kelimeler_YYYY-MM-DD_HH-MM-SS.txt' ismiyle saklar.
        """
        words_in_doc = set(re.findall(r'[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+', text_content.lower()))
        valid_words = {w for w in words_in_doc if len(w) >= 2 and not w.isdigit()}
        new_words = valid_words - self.word_pool

        if new_words:
            sorted_new_words = sorted(list(new_words))
            self.word_pool.update(new_words)

            # 1. Ana Kelime Havuzunu Güncelle
            try:
                sorted_pool = sorted(list(self.word_pool))
                with open(self.pool_file_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(sorted_pool))
                self.load_word_pool()
            except Exception as e:
                messagebox.showwarning("Havuz Hata", f"Havuz güncellenemedi: {e}")

            # 2. Tarih & Saat Adlandırmalı Özel Kelime Raporu Dosyası Oluştur
            now = datetime.datetime.now()
            time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
            word_log_filename = f"eklenen_kelimeler_{time_str}.txt"
            word_log_path = os.path.join(self.word_logs_dir, word_log_filename)

            try:
                with open(word_log_path, "w", encoding="utf-8") as wf:
                    wf.write("=== EKLENEN KELİME RAPORU ===\n")
                    wf.write(f"Tarih / Saat : {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    wf.write(f"Kaynak Belge : {os.path.basename(saved_file_path)}\n")
                    wf.write(f"Yeni Kelime Sayısı : {len(sorted_new_words)}\n")
                    wf.write("="*35 + "\n\n")
                    wf.write("\n".join(sorted_new_words))
            except Exception as e:
                print(f"Kelime rapor dosyası oluşturma hatası: {e}")

            # 3. Genel Aktivite Loguna Kayıt At
            self._log_activity(
                "HAVUZA_KELIME_EKLENDI",
                f"Belge: '{os.path.basename(saved_file_path)}' -> {len(sorted_new_words)} adet yeni kelime eklendi. Rapor Dosyası: {word_log_filename}"
            )
            return len(sorted_new_words), word_log_filename
        
        return 0, None

    def new_file(self):
        if messagebox.askyesno("Yeni Belge", "Mevcut metin temizlenecek. Devam edilsin mi?"):
            self.text_area.delete("1.0", tk.END)
            self.current_file_path = None
            self.lbl_file_status.config(text="Yeni Belge")
            self.lbl_last_action.config(text="Yeni belge oluşturuldu")
            self._log_activity("YENI_BELGE", "Yeni boş belge oluşturuldu.")

    def open_file(self):
        file_path = filedialog.askopenfilename(
            title="Metin Belgesi Aç",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", content)
                self.current_file_path = file_path
                self.lbl_file_status.config(text=os.path.basename(file_path))
                self.lbl_last_action.config(text="Belge yüklendi")
                self._update_stats()
                self._log_activity("BELGE_ACILDI", f"Açılan dosya: {file_path}")
            except Exception as e:
                messagebox.showerror("Hata", f"Dosya okunamadı:\n{e}")

    def save_file(self):
        if not self.current_file_path:
            self.save_file_as()
        else:
            self._execute_save(self.current_file_path)

    def save_file_as(self):
        file_path = filedialog.asksaveasfilename(
            title="Belgeyi Kaydet",
            defaultextension=".txt",
            filetypes=[("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.current_file_path = file_path
            self._execute_save(file_path)

    def _execute_save(self, file_path):
        try:
            content = self.text_area.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            self.lbl_file_status.config(text=os.path.basename(file_path))
            self._log_activity("BELGE_KAYDEDILDI", f"Belge kaydedildi: {file_path}")

            # Otomatik kelime çıkarma ve loglama
            added_count, word_log_file = 0, None
            if self.auto_learn_on_save.get():
                added_count, word_log_file = self._sync_words_to_pool_and_log(content, file_path)

            msg = "Dosya başarıyla kaydedildi."
            if added_count > 0:
                msg += f"\n\n• {added_count} yeni kelime havuza eklendi!\n• Kelime Raporu Dosyası: {word_log_file}"

            self.lbl_last_action.config(text=f"Kaydedildi ({added_count} yeni kelime eklendi)")
            messagebox.showinfo("Kayıt Başarılı", msg)

        except Exception as e:
            messagebox.showerror("Hata", f"Kaydetme esnasında hata oluştu:\n{e}")

    def open_pool_viewer(self):
        win = tk.Toplevel(self.root)
        win.title("Kelime Havuzu İnceleyici")
        win.geometry("400x500")
        win.configure(bg=self.COLORS["bg_dark"])

        ttk.Label(win, text="Aktif Kelime Havuzu", font=("Segoe UI", 12, "bold"), foreground=self.COLORS["accent"]).pack(pady=10)

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        listbox = tk.Listbox(
            frame,
            bg=self.COLORS["bg_editor"],
            fg=self.COLORS["text_main"],
            selectbackground=self.COLORS["accent"],
            selectforeground="#11111b",
            font=("Consolas", 10),
            relief="flat"
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sc = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        sc.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=sc.set)

        for w in sorted(list(self.word_pool)):
            listbox.insert(tk.END, f"  {w}")

    def open_activity_log(self):
        if not os.path.exists(self.activity_log_file):
            messagebox.showinfo("Bilgi", "Henüz aktivite log kaydı yok.")
            return

        win = tk.Toplevel(self.root)
        win.title("Sistem Aktivite Logları")
        win.geometry("700x450")
        win.configure(bg=self.COLORS["bg_dark"])

        ttk.Label(win, text="📜 Aktivite Log Geçmişi", font=("Segoe UI", 12, "bold"), foreground=self.COLORS["accent"]).pack(pady=10)

        txt_log = tk.Text(win, bg=self.COLORS["bg_editor"], fg=self.COLORS["text_main"], font=("Consolas", 9), relief="flat", padding=10)
        txt_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        with open(self.activity_log_file, "r", encoding="utf-8") as f:
            txt_log.insert("1.0", f.read())
        txt_log.config(state="disabled")

    def open_word_logs_folder(self):
        path = os.path.abspath(self.word_logs_dir)
        try:
            os.startfile(path)
        except AttributeError:
            import subprocess
            subprocess.call(["open" if os.name == "posix" else "xdg-open", path])

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernAutoSuggestEditorPro(root)
    root.mainloop()