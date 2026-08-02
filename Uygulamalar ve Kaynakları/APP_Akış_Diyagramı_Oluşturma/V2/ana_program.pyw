import tkinter as tk
from tkinter import messagebox, filedialog
import json
from arayuz import LawFlowchartUI

class LawController:
    def __init__(self):
        self.root = tk.Tk()
        self.rules = []
        self.current_step = 0  # Bu artık dizideki indeks yerine aktif "Adım No"yu (1'den başlayarak) takip edebilir
        self.ui = LawFlowchartUI(self.root, self)

    def run(self):
        self.root.mainloop()

    def add_rule(self):
        q = self.ui.ent_question.get().strip()
        y_act = self.ui.cmb_yes_action.get()
        y_val = self.ui.ent_yes_value.get().strip()
        n_act = self.ui.cmb_no_action.get()
        n_val = self.ui.ent_no_value.get().strip()

        if not q:
            messagebox.showwarning("Hata", "Lütfen bir soru girin!")
            return

        next_id = len(self.rules) + 1

        rule = {
            "id": next_id,
            "question": q,
            "yes": {"action": y_act, "value": y_val},
            "no": {"action": n_act, "value": n_val}
        }
        self.rules.append(rule)
        
        # Tabloya ekle (Metin gösterimi özeti)
        y_str = f"{y_act} -> {y_val}" if y_val else y_act
        n_str = f"{n_act} -> {n_val}" if n_val else n_act
        self.ui.tree.insert("", "end", values=(next_id, q, y_str, n_str))
        
        # Formu temizle
        self.ui.ent_question.delete(0, tk.END)
        self.ui.ent_yes_value.delete(0, tk.END)
        self.ui.ent_no_value.delete(0, tk.END)

    def clear_rules(self):
        self.rules.clear()
        for item in self.ui.tree.get_children():
            self.ui.tree.delete(item)
        self.reset_runner()
        self.ui.canvas.delete("all")

    def save_rules(self):
        if not self.rules:
            messagebox.showwarning("Hata", "Kaydedilecek akış bulunamadı!")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Dosyaları", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Başarılı", "Akış başarıyla kaydedildi!")

    def load_rules(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Dosyaları", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                for item in self.ui.tree.get_children():
                    self.ui.tree.delete(item)
                for r in self.rules:
                    y_str = f"{r['yes']['action']} -> {r['yes']['value']}" if r['yes']['value'] else r['yes']['action']
                    n_str = f"{r['no']['action']} -> {r['no']['value']}" if r['no']['value'] else r['no']['action']
                    self.ui.tree.insert("", "end", values=(r["id"], r["question"], y_str, n_str))
                self.reset_runner()
                messagebox.showinfo("Başarılı", "Akış başarıyla yüklendi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Yükleme hatası: {e}")

    def reset_runner(self):
        self.current_step = 0
        self.ui.lbl_run_title.config(text="Akışı Başlatmak için Butona Basın")
        self.ui.btn_yes.pack_forget()
        self.ui.btn_no.pack_forget()
        self.ui.btn_start_eval.pack(pady=10)

    def start_evaluation(self):
        if not self.rules:
            messagebox.showwarning("Hata", "Önce akış oluşturun veya yükleyin!")
            return
        self.current_step = 1  # 1. Adımdan başlıyoruz
        self.ui.btn_start_eval.pack_forget()
        self.ui.btn_yes.pack(side="left", padx=20)
        self.ui.btn_no.pack(side="left", padx=20)
        self.show_step()

    def get_rule_by_id(self, rule_id):
        for r in self.rules:
            if r["id"] == rule_id:
                return r
        return None

    def show_step(self):
        current_rule = self.get_rule_by_id(self.current_step)
        if current_rule:
            self.ui.lbl_run_title.config(text=f"[Adım No: {current_rule['id']}]\n\nŞART / SORU:\n\n{current_rule['question']}")
        else:
            self.ui.lbl_run_title.config(text="SONUÇ: Akış sonuna ulaşıldı, başka kural tetiklenmedi.")
            self.ui.btn_yes.pack_forget()
            self.ui.btn_no.pack_forget()
            self.ui.btn_start_eval.pack(pady=10)

    def process_answer(self, answer):
        current_rule = self.get_rule_by_id(self.current_step)
        if not current_rule:
            return

        cfg = current_rule["yes"] if answer == "Evet" else current_rule["no"]
        action = cfg["action"]
        val = cfg["value"]

        if action == "Nihai Sonuç Göster":
            self.ui.lbl_run_title.config(text=f"⚖️ HUKUKİ SONUÇ:\n\n{val if val else 'Süreç Tamamlandı.'}")
            self.ui.btn_yes.pack_forget()
            self.ui.btn_no.pack_forget()
            self.ui.btn_start_eval.pack(pady=10)
        
        elif action == "Başka Adıma Git (Go-To)":
            try:
                target_id = int(val)
                if self.get_rule_by_id(target_id):
                    self.current_step = target_id
                    self.show_step()
                else:
                    messagebox.showerror("Hata", f"Hedeflenen Adım No ({target_id}) sistemde bulunamadı!")
            except ValueError:
                messagebox.showerror("Hata", f"Geçersiz Adım No: '{val}'. Lütfen sadece sayı girin.")
        
        elif action == "Sıradaki Adıma Geç":
            self.current_step += 1
            self.show_step()

    def on_tab_change(self):
        if self.ui.notebook.index("current") == 2:
            self.draw_flowchart()

    def draw_flowchart(self):
        self.ui.canvas.delete("all")
        if not self.rules:
            return
        start_x, start_y = 350, 40
        box_w, box_h = 180, 50
        y_gap = 100
        curr_y = start_y

        # Her adımın çizildiği dikey konumu kaydetmek için sözlük (Ok çizerken lazım olacak)
        positions = {}

        # 1. Aşama: Kutuları Çiz
        for r in self.rules:
            positions[r["id"]] = curr_y
            # Ana Karar Kutusu
            self.ui.canvas.create_rectangle(start_x - box_w/2, curr_y, start_x + box_w/2, curr_y + box_h, fill="#e6f2ff", outline="#0066cc", width=2)
            self.ui.canvas.create_text(start_x, curr_y + box_h/2, text=f"No:{r['id']} - {r['question'][:25]}...", font=("Arial", 9, "bold"))
            curr_y += y_gap

        # 2. Aşama: Bağlantı Oklarını Çiz (Go-To mantığıyla yönlendirerek)
        for r in self.rules:
            y_pos = positions[r["id"]]
            
            # EVET ÇİZGİSİ
            if r["yes"]["action"] == "Başka Adıma Git (Go-To)":
                try:
                    tid = int(r["yes"]["value"])
                    if tid in positions:
                        # Sağa açılıp hedef kutunun yanına giden Go-To Oku
                        target_y = positions[tid]
                        self.ui.canvas.create_line(start_x + box_w/2, y_pos + box_h/2, start_x + box_w/2 + 40, y_pos + box_h/2, start_x + box_w/2 + 40, target_y + box_h/2, start_x + box_w/2, target_y + box_h/2, arrow=tk.LAST, fill="#00aa00", width=2)
                except: pass
            elif r["yes"]["action"] == "Sıradaki Adıma Geç" and (r["id"] + 1) in positions:
                # Düz aşağı ok
                self.ui.canvas.create_line(start_x, y_pos + box_h, start_x, positions[r["id"]+1], arrow=tk.LAST, fill="gray", width=2)

            # HAYIR ÇİZGİSİ
            if r["no"]["action"] == "Başka Adıma Git (Go-To)":
                try:
                    tid = int(r["no"]["value"])
                    if tid in positions:
                        # Sola açılıp hedef kutuya giden Go-To Oku
                        target_y = positions[tid]
                        self.ui.canvas.create_line(start_x - box_w/2, y_pos + box_h/2, start_x - box_w/2 - 40, y_pos + box_h/2, start_x - box_w/2 - 40, target_y + box_h/2, start_x - box_w/2, target_y + box_h/2, arrow=tk.LAST, fill="#ff0000", width=2)
                except: pass

        self.ui.canvas.config(scrollregion=self.ui.canvas.bbox("all"))

if __name__ == "__main__":
    controller = LawController()
    controller.run()
