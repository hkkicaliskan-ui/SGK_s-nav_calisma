import tkinter as tk
from tkinter import ttk

class LawFlowchartUI:
    def __init__(self, root, controller):
        self.root = root
        self.c = controller
        self.root.title("Gelişmiş Hukuk Karar Mekanizması (Go-To Destekli)")
        self.root.geometry("1000x700")
        self.setup_ui()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_builder = ttk.Frame(self.notebook)
        self.tab_runner = ttk.Frame(self.notebook)
        self.tab_visualizer = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_builder, text="1. Akış Oluşturucu & Dosya")
        self.notebook.add(self.tab_runner, text="2. Mekanizmayı Çalıştır")
        self.notebook.add(self.tab_visualizer, text="3. Görsel Akış Diyagramı")

        self.build_tab_builder()
        self.build_tab_runner()
        self.build_tab_visualizer()
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.c.on_tab_change())

    def build_tab_builder(self):
        # Dosya İşlemleri
        file_frame = ttk.LabelFrame(self.tab_builder, text=" Dosya İşlemleri ")
        file_frame.pack(pady=5, padx=20, fill="x")
        ttk.Button(file_frame, text="Akışı Kaydet (.json)", command=self.c.save_rules).pack(side="left", padx=10, pady=5)
        ttk.Button(file_frame, text="Akış Yükle (.json)", command=self.c.load_rules).pack(side="left", padx=10, pady=5)

        # Form Alanı
        form_frame = ttk.LabelFrame(self.tab_builder, text=" Adım Ekle (Her adıma otomatik bir ID verilir) ")
        form_frame.pack(pady=5, padx=20, fill="x")

        ttk.Label(form_frame, text="Soru / Şart:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.ent_question = ttk.Entry(form_frame, width=70)
        self.ent_question.grid(row=0, column=1, columnspan=3, pady=5, padx=5)

        # EVET Dallanması
        ttk.Label(form_frame, text="EVET ise Eylem:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.cmb_yes_action = ttk.Combobox(form_frame, values=["Nihai Sonuç Göster", "Başka Adıma Git (Go-To)", "Sıradaki Adıma Geç"], width=22, state="readonly")
        self.cmb_yes_action.grid(row=1, column=1, pady=5, padx=5)
        self.cmb_yes_action.set("Sıradaki Adıma Geç")
        self.ent_yes_value = ttk.Entry(form_frame, width=35)
        self.ent_yes_value.grid(row=1, column=2, pady=5, padx=5)
        ttk.Label(form_frame, text="(Sonuç metni veya Hedef Adım No yazın)").grid(row=1, column=3, sticky="w")

        # HAYIR Dallanması
        ttk.Label(form_frame, text="HAYIR ise Eylem:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.cmb_no_action = ttk.Combobox(form_frame, values=["Nihai Sonuç Göster", "Başka Adıma Git (Go-To)", "Sıradaki Adıma Geç"], width=22, state="readonly")
        self.cmb_no_action.grid(row=2, column=1, pady=5, padx=5)
        self.cmb_no_action.set("Nihai Sonuç Göster")
        self.ent_no_value = ttk.Entry(form_frame, width=35)
        self.ent_no_value.grid(row=2, column=2, pady=5, padx=5)
        ttk.Label(form_frame, text="(Sonuç metni veya Hedef Adım No yazın)").grid(row=2, column=3, sticky="w")

        # Butonlar
        btn_frame = ttk.Frame(self.tab_builder)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Şartı Akışa Ekle", command=self.c.add_rule).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Listeyi Temizle", command=self.c.clear_rules).grid(row=0, column=1, padx=5)

        # Tablo
        self.tree = ttk.Treeview(self.tab_builder, columns=("ID", "Soru", "Evet Eylemi", "Hayır Eylemi"), show="headings", height=10)
        self.tree.heading("ID", text="Adım No")
        self.tree.heading("Soru", text="Soru / Şart")
        self.tree.heading("Evet Eylemi", text="EVET Durumu")
        self.tree.heading("Hayır Eylemi", text="HAYIR Durumu")
        self.tree.column("ID", width=70, anchor="center")
        self.tree.column("Soru", width=350)
        self.tree.column("Evet Eylemi", width=250)
        self.tree.column("Hayır Eylemi", width=250)
        self.tree.pack(pady=10, padx=20, fill="both", expand=True)

    def build_tab_runner(self):
        self.lbl_run_title = ttk.Label(self.tab_runner, text="Akışı Başlatmak için Butona Basın", font=("Arial", 14, "bold"), wraplength=700, justify="center")
        self.lbl_run_title.pack(pady=40)

        self.btn_start_eval = ttk.Button(self.tab_runner, text="Analizi Başlat", command=self.c.start_evaluation)
        self.btn_start_eval.pack(pady=10)

        self.choice_frame = ttk.Frame(self.tab_runner)
        self.choice_frame.pack(pady=20)

        self.btn_yes = ttk.Button(self.choice_frame, text="EVET", command=lambda: self.c.process_answer("Evet"))
        self.btn_no = ttk.Button(self.choice_frame, text="HAYIR", command=lambda: self.c.process_answer("Hayır"))

    def build_tab_visualizer(self):
        canvas_container = ttk.Frame(self.tab_visualizer)
        canvas_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(canvas_container, bg="white")
        v_scroll = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.pack(side="right", fill="y")
        h_scroll.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
