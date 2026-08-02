import os
import json
import datetime
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
import PyPDF2
import docx

# Arayüz Görünüm Modu
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "flashcard_studio_config.json"
STORAGE_DIR = "app_storage"

class FlashcardStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Flashcard Studio Pro v3 - Word Görünümlü & Kalıcı Vurgulu")
        self.geometry("1280x800")
        self.minsize(1000, 700)

        # Kalıcı Depolama Klasörü Kontrolü
        if not os.path.exists(STORAGE_DIR):
            os.makedirs(STORAGE_DIR)

        # Durum Değişkenleri
        self.excel_file_path = ""
        self.current_doc_path = ""
        self.current_cursor_pos = "1.0"
        
        # UI Bileşenleri Kurulumu
        self.create_widgets()

        # Oturum ve Son Durumu Yükle (Kaldığı yerden devam etme)
        self.load_session()

        # Kapanış Protokolü
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- ÜST PANEL (Header) ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=15, pady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📚 Flashcard Studio Pro v3",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=15, pady=10)

        self.lbl_session_status = ctk.CTkLabel(
            self.header_frame,
            text="🔄 Otomatik Kayıt & Word Görünümü: Aktif",
            text_color="#10B981",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_session_status.pack(side="right", padx=15, pady=10)

        # --- ANA İÇERİK BÖLÜMÜ ---
        self.main_pane = ctk.CTkFrame(self, fg_color="transparent")
        self.main_pane.pack(fill="both", expand=True, padx=15, pady=5)

        # --- SOL PANEL: Word Görünümlü Doküman Alanı ---
        self.left_frame = ctk.CTkFrame(self.main_pane)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.doc_tools_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.doc_tools_frame.pack(fill="x", padx=10, pady=8)

        self.btn_load_doc = ctk.CTkButton(
            self.doc_tools_frame, 
            text="📂 Doküman Aç (.pdf, .docx, .txt)", 
            command=self.load_document
        )
        self.btn_load_doc.pack(side="left", padx=(0, 5))

        self.lbl_doc_info = ctk.CTkLabel(
            self.doc_tools_frame, 
            text="Yüklü Doküman: Yok", 
            text_color="gray",
            anchor="w"
        )
        self.lbl_doc_info.pack(side="left", fill="x", expand=True, padx=5)

        # --- WORD SAYFA SİMÜLASYON KONTEYNERİ ---
        # Koyu Masaüstü Arka Planı Üzerine Beyaz Word Sayfası
        self.word_outer_frame = ctk.CTkFrame(self.left_frame, fg_color="#1E1E1E", corner_radius=6)
        self.word_outer_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Beyaz "A4 Sayfa" Görünümündeki İç Konteyner
        self.word_page_frame = ctk.CTkFrame(self.word_outer_frame, fg_color="#FFFFFF", corner_radius=2, border_width=1, border_color="#D1D5DB")
        self.word_page_frame.pack(fill="both", expand=True, padx=35, pady=20)

        # Word Tipi Metin Kutusu (Siyah Metin, Calibri Font, Kenar Marjinleri)
        self.doc_textbox = ctk.CTkTextbox(
            self.word_page_frame, 
            font=("Calibri", 13), 
            wrap="word",
            text_color="#111827",
            fg_color="#FFFFFF",
            activate_scrollbars=True
        )
        self.doc_textbox.pack(fill="both", expand=True, padx=20, pady=20)

        # Vurgulama Etiket (Tag) Renk Ayarları
        # Ön yüz: Parlak Sarı Vurgu | Arka yüz: Açık Yeşil Vurgu
        self.doc_textbox._textbox.tag_config("front_highlight", background="#FEF08A", foreground="#000000")
        self.doc_textbox._textbox.tag_config("back_highlight", background="#A7F3D0", foreground="#000000")

        # --- SAĞ PANEL: Kartlar, Excel & Loglar ---
        self.right_frame = ctk.CTkFrame(self.main_pane, width=420)
        self.right_frame.pack(side="right", fill="both", expand=False)

        # Excel Dosya Yönetimi
        self.excel_frame = ctk.CTkFrame(self.right_frame)
        self.excel_frame.pack(fill="x", padx=10, pady=10)

        self.btn_excel = ctk.CTkButton(
            self.excel_frame, 
            text="📊 Excel Kayıt Dosyası Seç / Oluştur", 
            command=self.select_excel_file
        )
        self.btn_excel.pack(fill="x", padx=10, pady=5)

        self.lbl_excel_path = ctk.CTkLabel(
            self.excel_frame, 
            text="Seçili Excel: Yok", 
            text_color="gray", 
            wraplength=380
        )
        self.lbl_excel_path.pack(fill="x", padx=10, pady=(0, 5))

        # Kart Ön Yüzü
        self.lbl_front = ctk.CTkLabel(self.right_frame, text="🎴 Ön Yüz (Soru / Terim):", font=ctk.CTkFont(weight="bold"))
        self.lbl_front.pack(anchor="w", padx=12, pady=(5, 0))

        self.txt_front = ctk.CTkTextbox(self.right_frame, height=75)
        self.txt_front.pack(fill="x", padx=12, pady=3)

        self.btn_set_front = ctk.CTkButton(
            self.right_frame, 
            text="🟡 Seçili Metni Ön Yüz Yap ve Vurgula", 
            fg_color="#D97706", 
            hover_color="#B45309",
            command=self.set_front_text
        )
        self.btn_set_front.pack(fill="x", padx=12, pady=2)

        # Kart Arka Yüzü
        self.lbl_back = ctk.CTkLabel(self.right_frame, text="🎯 Arka Yüz (Cevap / Açıklama):", font=ctk.CTkFont(weight="bold"))
        self.lbl_back.pack(anchor="w", padx=12, pady=(10, 0))

        self.txt_back = ctk.CTkTextbox(self.right_frame, height=95)
        self.txt_back.pack(fill="x", padx=12, pady=3)

        self.btn_set_back = ctk.CTkButton(
            self.right_frame, 
            text="🟢 Seçili Metni Arka Yüz Yap ve Vurgula", 
            fg_color="#059669", 
            hover_color="#047857",
            command=self.set_back_text
        )
        self.btn_set_back.pack(fill="x", padx=12, pady=2)

        # Excele Ekle Butonu
        self.btn_add_card = ctk.CTkButton(
            self.right_frame, 
            text="➕ Kartı Excel'e Aktar (Peyderpey)", 
            fg_color="#2563EB", 
            hover_color="#1D4ED8", 
            height=38, 
            font=ctk.CTkFont(size=13, weight="bold"), 
            command=self.add_card_to_excel
        )
        self.btn_add_card.pack(fill="x", padx=12, pady=12)

        # --- ALT PANEL: İŞLEM LOGLARI ---
        self.log_frame = ctk.CTkFrame(self.right_frame)
        self.log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.lbl_log = ctk.CTkLabel(self.log_frame, text="📜 İşlem Kayıtları (Loglar)", font=ctk.CTkFont(weight="bold"))
        self.lbl_log.pack(anchor="w", padx=10, pady=(5, 0))

        self.log_textbox = ctk.CTkTextbox(self.log_frame, font=("Consolas", 11), state="disabled")
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=5)

    # --- LOG SİSTEMİ ---
    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", log_entry)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # --- DOKÜMANA ÖZGÜ VURGU SAKLAMA ---
    def _get_highlights_file_path(self, doc_path):
        """Her doküman için benzersiz vurgulama dosyasının yolunu döner."""
        if not doc_path:
            return None
        file_name = os.path.basename(doc_path)
        safe_name = "".join([c if c.isalnum() else "_" for c in file_name])
        return os.path.join(STORAGE_DIR, f"highlights_{safe_name}.json")

    def save_document_highlights(self):
        """Mevcut dokümandaki renkli vurguları kaydeder."""
        if not self.current_doc_path:
            return
        
        save_path = self._get_highlights_file_path(self.current_doc_path)
        front_tags = [str(r) for r in self.doc_textbox._textbox.tag_ranges("front_highlight")]
        back_tags = [str(r) for r in self.doc_textbox._textbox.tag_ranges("back_highlight")]

        data = {
            "doc_path": self.current_doc_path,
            "front_tags": front_tags,
            "back_tags": back_tags
        }

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"Vurgular kaydedilemedi: {e}")

    def load_document_highlights(self, doc_path):
        """Açılan doküman daha önce işlenmişse, kaydedilmiş vurguları geri yükler."""
        save_path = self._get_highlights_file_path(doc_path)
        if not os.path.exists(save_path):
            return

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            front_tags = data.get("front_tags", [])
            for i in range(0, len(front_tags), 2):
                self.doc_textbox._textbox.tag_add("front_highlight", front_tags[i], front_tags[i+1])

            back_tags = data.get("back_tags", [])
            for i in range(0, len(back_tags), 2):
                self.doc_textbox._textbox.tag_add("back_highlight", back_tags[i], back_tags[i+1])

            self.log("Bu doküman için önceki vurgulamalar otomatik yüklendi.")
        except Exception as e:
            self.log(f"Önceki vurgular yüklenirken hata oluştu: {e}")

    # --- DOKÜMAN OKUMA ---
    def load_document(self, file_path=None, restore_pos=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[("Desteklenen Dosyalar", "*.pdf *.docx *.txt"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("Metin", "*.txt")]
            )
        if not file_path or not os.path.exists(file_path):
            return

        # Eski dokümanın vurgularını kaydet
        if self.current_doc_path and self.current_doc_path != file_path:
            self.save_document_highlights()

        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        try:
            if ext == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif ext == ".pdf":
                reader = PyPDF2.PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif ext == ".docx":
                doc = docx.Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])

            self.doc_textbox.delete("1.0", "end")
            self.doc_textbox.insert("1.0", text)
            
            self.current_doc_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_doc_info.configure(text=f"Yüklü: {filename}", text_color="#10B981")
            self.log(f"Doküman yüklendi: {filename}")

            # Dokümana ait geçmiş vurgulamaları yükle
            self.load_document_highlights(file_path)

            # Kaydırma Konumuna Git (Kaldığı Yer)
            if restore_pos:
                try:
                    self.doc_textbox._textbox.see(restore_pos)
                    self.doc_textbox._textbox.mark_set("insert", restore_pos)
                except Exception:
                    pass

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunurken hata oluştu: {str(e)}")
            self.log(f"HATA: Doküman okunamadı ({str(e)})")

    def select_excel_file(self, file_path=None):
        if not file_path:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel Dosyası", "*.xlsx")]
            )
        if file_path:
            self.excel_file_path = file_path
            filename = os.path.basename(file_path)
            self.lbl_excel_path.configure(text=f"Seçili: {filename}", text_color="#10B981")
            self.log(f"Excel hedefi belirlendi: {filename}")
            self.save_session()

    # --- METİN SEÇİMİ VE VURGULAMA ---
    def set_front_text(self):
        try:
            sel_start = self.doc_textbox._textbox.index("sel.first")
            sel_end = self.doc_textbox._textbox.index("sel.last")
            selected_text = self.doc_textbox._textbox.get(sel_start, sel_end).strip()

            if not selected_text:
                return

            self.txt_front.delete("1.0", "end")
            self.txt_front.insert("1.0", selected_text)

            self.doc_textbox._textbox.tag_add("front_highlight", sel_start, sel_end)
            self.log(f"Ön yüze metin eklendi ve vurgulandı ({len(selected_text)} karakter)")
            
            self.save_document_highlights()
            self.save_session()

        except Exception:
            messagebox.showwarning("Uyarı", "Lütfen önce dokümandan bir metin seçin!")

    def set_back_text(self):
        try:
            sel_start = self.doc_textbox._textbox.index("sel.first")
            sel_end = self.doc_textbox._textbox.index("sel.last")
            selected_text = self.doc_textbox._textbox.get(sel_start, sel_end).strip()

            if not selected_text:
                return

            self.txt_back.delete("1.0", "end")
            self.txt_back.insert("1.0", selected_text)

            self.doc_textbox._textbox.tag_add("back_highlight", sel_start, sel_end)
            self.log(f"Arka yüze metin eklendi ve vurgulandı ({len(selected_text)} karakter)")
            
            self.save_document_highlights()
            self.save_session()

        except Exception:
            messagebox.showwarning("Uyarı", "Lütfen önce dokümandan bir metin seçin!")

    # --- PEYDERPEY EXCEL AKTARIMI ---
    def add_card_to_excel(self):
        if not self.excel_file_path:
            messagebox.showwarning("Uyarı", "Lütfen önce bir Excel dosyası seçin veya oluşturun!")
            return

        front = self.txt_front.get("1.0", "end").strip()
        back = self.txt_back.get("1.0", "end").strip()

        if not front or not back:
            messagebox.showwarning("Eksik Bilgi", "Kartın hem Ön Yüzü hem de Arka Yüzü dolu olmalıdır!")
            return

        new_data = pd.DataFrame([{"Ön Yüz (Front)": front, "Arka Yüz (Back)": back, "Tarih": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}])

        try:
            if os.path.exists(self.excel_file_path):
                df_existing = pd.read_excel(self.excel_file_path)

                is_duplicate = ((df_existing["Ön Yüz (Front)"] == front) & (df_existing["Arka Yüz (Back)"] == back)).any()
                if is_duplicate:
                    messagebox.showinfo("Bilgi", "Bu kart zaten Excel havuzunda mevcut.")
                    self.log("Mükerrer kart ekleme isteği engellendi.")
                    return

                df_updated = pd.concat([df_existing, new_data], ignore_index=True)
            else:
                df_updated = new_data

            df_updated.to_excel(self.excel_file_path, index=False)

            self.txt_front.delete("1.0", "end")
            self.txt_back.delete("1.0", "end")

            total_cards = len(df_updated)
            self.log(f"Kart Excel'e kaydedildi. Toplam Kart: {total_cards}")
            self.save_session()
            messagebox.showinfo("Başarılı", f"Kart kaydedildi!\nToplam Kart Sayısı: {total_cards}")

        except Exception as e:
            messagebox.showerror("Hata", f"Excel'e kaydedilirken bir hata oluştu: {str(e)}")
            self.log(f"HATA: Excel kaydı başarısız ({str(e)})")

    # --- ANLIK OTURUM VE KONUM KAYDI (AUTOSAVE) ---
    def save_session(self):
        """Uygulamanın o anki tüm durumunu (imleç/sayfa konumu dahil) Json dosyasına yazar."""
        try:
            try:
                cursor_pos = self.doc_textbox._textbox.index("@0,0")
            except Exception:
                cursor_pos = "1.0"

            config = {
                "excel_file_path": self.excel_file_path,
                "current_doc_path": self.current_doc_path,
                "cursor_pos": cursor_pos,
                "txt_front": self.txt_front.get("1.0", "end").strip(),
                "txt_back": self.txt_back.get("1.0", "end").strip()
            }

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Oturum kaydedilemedi: {e}")

    def load_session(self):
        """Uygulama açıldığında en son kalınan yeri (doküman, sayfa konumu, taslak metinler) geri yükler."""
        if not os.path.exists(CONFIG_FILE):
            self.log("Yeni oturum başlatıldı.")
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

            if config.get("excel_file_path"):
                self.select_excel_file(config["excel_file_path"])

            if config.get("current_doc_path") and os.path.exists(config["current_doc_path"]):
                cursor_pos = config.get("cursor_pos", "1.0")
                self.load_document(config["current_doc_path"], restore_pos=cursor_pos)

            if config.get("txt_front"):
                self.txt_front.insert("1.0", config["txt_front"])
            if config.get("txt_back"):
                self.txt_back.insert("1.0", config["txt_back"])

            self.log("Son oturum ve imleç konumu tam olarak geri yüklendi.")

        except Exception as e:
            self.log(f"Oturum verileri yüklenirken hata oluştu: {str(e)}")

    def on_closing(self):
        self.save_document_highlights()
        self.save_session()
        self.destroy()

if __name__ == "__main__":
    app = FlashcardStudioApp()
    app.mainloop()