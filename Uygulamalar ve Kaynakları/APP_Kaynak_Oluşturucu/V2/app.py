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

class FlashcardStudioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Flashcard Excel Studio v2 - Gelişmiş Kart ve Metin Yönetimi")
        self.geometry("1180x760")
        self.minsize(950, 650)

        # Durum Değişkenleri
        self.excel_file_path = ""
        self.current_doc_path = ""
        
        # UI Bileşenleri Kurulumu
        self.create_widgets()

        # Uygulama Durumunu (Session) Yükle
        self.load_session()

        # Kapanış Protokolü
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # --- ÜST PANEL (Header) ---
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=15, pady=10)

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="📚 Flashcard Studio Pro",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(side="left", padx=15, pady=10)

        self.lbl_session_status = ctk.CTkLabel(
            self.header_frame,
            text="🔄 Oturum Saklama: Aktif",
            text_color="#10B981",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_session_status.pack(side="right", padx=15, pady=10)

        # --- ANA İÇERİK BÖLÜMÜ ---
        self.main_pane = ctk.CTkFrame(self, fg_color="transparent")
        self.main_pane.pack(fill="both", expand=True, padx=15, pady=5)

        # --- SOL PANEL: Doküman ve Vurgulama ---
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

        # Doküman Metin Kutusu (Tkinter Text alt yapısı ile tag/vurgu desteği)
        self.doc_textbox = ctk.CTkTextbox(self.left_frame, font=("Consolas", 13), wrap="word")
        self.doc_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Vurgulama Etiket (Tag) Renk Ayarları
        # Ön yüz için Sarı/Kahve arka plan, Arka yüz için Yeşil ton
        self.doc_textbox._textbox.tag_config("front_highlight", background="#854D0E", foreground="#FFFFFF")
        self.doc_textbox._textbox.tag_config("back_highlight", background="#065F46", foreground="#FFFFFF")

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

    # --- DOKÜMAN OKUMA ---
    def load_document(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[("Desteklenen Dosyalar", "*.pdf *.docx *.txt"), ("PDF", "*.pdf"), ("Word", "*.docx"), ("Metin", "*.txt")]
            )
        if not file_path or not os.path.exists(file_path):
            return

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

    # --- METİN SEÇİMİ VE VURGULAMA ---
    def set_front_text(self):
        try:
            sel_start = self.doc_textbox._textbox.index("sel.first")
            sel_end = self.doc_textbox._textbox.index("sel.last")
            selected_text = self.doc_textbox._textbox.get(sel_start, sel_end).strip()

            if not selected_text:
                return

            # Metin kutusuna aktar
            self.txt_front.delete("1.0", "end")
            self.txt_front.insert("1.0", selected_text)

            # Dokümanda Ön Yüz Vurgusu (Sarı) Uygula
            self.doc_textbox._textbox.tag_add("front_highlight", sel_start, sel_end)
            self.log(f"Ön yüze metin eklendi ve vurgulandı ({len(selected_text)} karakter)")

        except Exception:
            messagebox.showwarning("Uyarı", "Lütfen önce dokümandan bir metin seçin!")

    def set_back_text(self):
        try:
            sel_start = self.doc_textbox._textbox.index("sel.first")
            sel_end = self.doc_textbox._textbox.index("sel.last")
            selected_text = self.doc_textbox._textbox.get(sel_start, sel_end).strip()

            if not selected_text:
                return

            # Metin kutusuna aktar
            self.txt_back.delete("1.0", "end")
            self.txt_back.insert("1.0", selected_text)

            # Dokümanda Arka Yüz Vurgusu (Yeşil) Uygula
            self.doc_textbox._textbox.tag_add("back_highlight", sel_start, sel_end)
            self.log(f"Arka yüze metin eklendi ve vurgulandı ({len(selected_text)} karakter)")

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

                # Mükerrer Kontrolü
                is_duplicate = ((df_existing["Ön Yüz (Front)"] == front) & (df_existing["Arka Yüz (Back)"] == back)).any()
                if is_duplicate:
                    messagebox.showinfo("Bilgi", "Bu kart zaten Excel havuzunda mevcut.")
                    self.log("Mükerrer kart ekleme isteği engellendi.")
                    return

                df_updated = pd.concat([df_existing, new_data], ignore_index=True)
            else:
                df_updated = new_data

            df_updated.to_excel(self.excel_file_path, index=False)

            # Form Temizleme
            self.txt_front.delete("1.0", "end")
            self.txt_back.delete("1.0", "end")

            total_cards = len(df_updated)
            self.log(f"Kart Excel'e kaydedildi. Toplam Kart: {total_cards}")
            messagebox.showinfo("Başarılı", f"Kart kaydedildi!\nToplam Kart Sayısı: {total_cards}")

        except Exception as e:
            messagebox.showerror("Hata", f"Excel'e kaydedilirken bir hata oluştu: {str(e)}")
            self.log(f"HATA: Excel kaydı başarısız ({str(e)})")

    # --- OTURUM KAYDI & GERİ YÜKLEME ---
    def save_session(self):
        """Uygulama kapatılırken durum, metinler ve vurgulama konumları kaydedilir."""
        try:
            # Tag konumlarını alma
            front_tags = []
            for ranges in self.doc_textbox._textbox.tag_ranges("front_highlight"):
                front_tags.append(str(ranges))

            back_tags = []
            for ranges in self.doc_textbox._textbox.tag_ranges("back_highlight"):
                back_tags.append(str(ranges))

            config = {
                "excel_file_path": self.excel_file_path,
                "current_doc_path": self.current_doc_path,
                "txt_front": self.txt_front.get("1.0", "end").strip(),
                "txt_back": self.txt_back.get("1.0", "end").strip(),
                "front_tags": front_tags,
                "back_tags": back_tags
            }

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

        except Exception as e:
            print(f"Oturum kaydedilemedi: {e}")

    def load_session(self):
        """Uygulama açıldığında önceki oturum verilerini geri yükler."""
        if not os.path.exists(CONFIG_FILE):
            self.log("Yeni oturum başlatıldı.")
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Excel yolunu yükle
            if config.get("excel_file_path"):
                self.select_excel_file(config["excel_file_path"])

            # Dokümanı yükle
            if config.get("current_doc_path") and os.path.exists(config["current_doc_path"]):
                self.load_document(config["current_doc_path"])

                # Vurguları geri yükle
                front_tags = config.get("front_tags", [])
                for i in range(0, len(front_tags), 2):
                    self.doc_textbox._textbox.tag_add("front_highlight", front_tags[i], front_tags[i+1])

                back_tags = config.get("back_tags", [])
                for i in range(0, len(back_tags), 2):
                    self.doc_textbox._textbox.tag_add("back_highlight", back_tags[i], back_tags[i+1])

            # Metin alanlarını geri yükle
            if config.get("txt_front"):
                self.txt_front.insert("1.0", config["txt_front"])
            if config.get("txt_back"):
                self.txt_back.insert("1.0", config["txt_back"])

            self.log("Önceki oturum verileri ve vurgular yüklendi.")

        except Exception as e:
            self.log(f"Oturum verileri yüklenirken hata oluştu: {str(e)}")

    def on_closing(self):
        self.save_session()
        self.destroy()


if __name__ == "__main__":
    app = FlashcardStudioApp()
    app.mainloop()