import tkinter as tk
from tkinter import messagebox, filedialog
import json
from arayuz import LawFlowchartUI

class LawController:
    def __init__(self):
        self.root = tk.Tk()
        self.rules = []
        self.current_step = 0
        self.ui = LawFlowchartUI(self.root, self)

    def run(self):
        self.root.mainloop()

    def add_rule(self):
        q = self.ui.ent_question.get().strip()
        y = self.ui.ent_yes.get().strip()
        n = self.ui.ent_no.get().strip()

        if not q:
            messagebox.showwarning("Hata", "Lütfen bir soru girin!")
            return

        rule = {"question": q, "yes_output": y if y else None, "no_output": n if n else None}
        self.rules.append(rule)
        self.ui.tree.insert("", "end", values=(q, y if y else "Sonraki Şart", n if n else "Sonraki Şart"))
        
        self.ui.ent_question.delete(0, tk.END)
        self.ui.ent_yes.delete(0, tk.END)
        self.ui.ent_no.delete(0, tk.END)

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
            messagebox.showinfo("Başarılı", "Akış kaydedildi!")

    def load_rules(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Dosyaları", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                for item in self.ui.tree.get_children():
                    self.ui.tree.delete(item)
                for r in self.rules:
                    self.ui.tree.insert("", "end", values=(r["question"], r["yes_output"] if r["yes_output"] else "Sonraki Şart", r["no_output"] if r["no_output"] else "Sonraki Şart"))
                self.reset_runner()
                messagebox.showinfo("Başarılı", "Akış yüklendi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Hata: {e}")

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
        self.current_step = 0
        self.ui.btn_start_eval.pack_forget()
        self.ui.btn_yes.pack(side="left", padx=20)
        self.ui.btn_no.pack(side="left", padx=20)
        self.show_step()

    def show_step(self):
        if self.current_step < len(self.rules):
            self.ui.lbl_run_title.config(text=f"ŞART / SORU:\n\n{self.rules[self.current_step]['question']}")
        else:
            self.ui.lbl_run_title.config(text="SONUÇ: Özel bir istisna tetiklenmedi.")
            self.ui.btn_yes.pack_forget()
            self.ui.btn_no.pack_forget()
            self.ui.btn_start_eval.pack(pady=10)

    def process_answer(self, answer):
        current_rule = self.rules[self.current_step]
        output = current_rule["yes_output"] if answer == "Evet" else current_rule["no_output"]

        if output:
            self.ui.lbl_run_title.config(text=f"⚖️ HUKUKI SONUÇ:\n\n{output}")
            self.ui.btn_yes.pack_forget()
            self.ui.btn_no.pack_forget()
            self.ui.btn_start_eval.pack(pady=10)
        else:
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
        y_gap = 90
        curr_y = start_y

        for i, rule in enumerate(self.rules):
            self.ui.canvas.create_rectangle(start_x - box_w/2, curr_y, start_x + box_w/2, curr_y + box_h, fill="#e6f2ff", outline="#0066cc", width=2)
            self.ui.canvas.create_text(start_x, curr_y + box_h/2, text=rule["question"][:40], font=("Arial", 9, "bold"))

            if rule["yes_output"]:
                self.ui.canvas.create_line(start_x + box_w/2, curr_y + box_h/2, start_x + box_w/2 + 60, curr_y + box_h/2, arrow=tk.LAST, fill="green", width=2)
                self.ui.canvas.create_rectangle(start_x + box_w/2 + 60, curr_y + 10, start_x + box_w/2 + 200, curr_y + box_h - 10, fill="#e6ffe6", outline="green")
                self.ui.canvas.create_text(start_x + box_w/2 + 130, curr_y + box_h/2, text=rule["yes_output"][:25], font=("Arial", 8))

            if rule["no_output"]:
                self.ui.canvas.create_line(start_x - box_w/2, curr_y + box_h/2, start_x - box_w/2 - 60, curr_y + box_h/2, arrow=tk.LAST, fill="red", width=2)
                self.ui.canvas.create_rectangle(start_x - box_w/2 - 200, curr_y + 10, start_x - box_w/2 - 60, curr_y + box_h - 10, fill="#ffe6e6", outline="red")
                self.ui.canvas.create_text(start_x - box_w/2 - 130, curr_y + box_h/2, text=rule["no_output"][:25], font=("Arial", 8))

            if i < len(self.rules) - 1:
                self.ui.canvas.create_line(start_x, curr_y + box_h, start_x, curr_y + y_gap, arrow=tk.LAST, fill="gray", width=2)
            curr_y += y_gap

        self.ui.canvas.config(scrollregion=self.ui.canvas.bbox("all"))

if __name__ == "__main__":
    controller = LawController()
    controller.run()
