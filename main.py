from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable
import json
import os
import calendar
import datetime

import tkinter as tk
from tkinter import ttk


def parse_grade(text: str) -> Optional[float]:
    raw = text.strip()
    if not raw:
        return None
    raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def compute_gNote(mNote: list[float], sNote: list[float]) -> float:
    return (mNote[0] + mNote[1] + sNote[0] + sNote[1]) / 4.0


@dataclass
class GradeRowModel:
    mNote: list[Optional[float]]
    sNote: list[Optional[float]]
    gNote: Optional[float]

# UI
class GradeRowUI:
    def __init__(
        self,
        parent: ttk.Frame,
        index: int,
        selected_var: tk.IntVar,
        on_select: Callable[[int], None],
        on_change: Optional[Callable[[], None]] = None,
    ) -> None:
        self.parent = parent
        self.index = index
        self.selected_var = selected_var
        self.on_select = on_select
        self.on_change = on_change

        self.model = GradeRowModel(mNote=[None, None], sNote=[None, None], gNote=None)

        self.subject_var = tk.StringVar(value="")
        self.m1_var = tk.StringVar(value="")
        self.m2_var = tk.StringVar(value="")
        self.s1_var = tk.StringVar(value="")
        self.s2_var = tk.StringVar(value="")
        self.g_var = tk.StringVar(value="")

        self.widgets: list[tk.Widget] = []
        self._build_widgets()
        self._wire_events()
        self._update_gNote()

    def _build_widgets(self) -> None:
        self.sel_btn = ttk.Radiobutton(
            self.parent,
            variable=self.selected_var,
            value=self.index,
            command=self._select_me,
        )

        self.subject_entry = ttk.Entry(self.parent, textvariable=self.subject_var, width=22)
        self.m1_entry = ttk.Entry(self.parent, textvariable=self.m1_var, width=10)
        self.m2_entry = ttk.Entry(self.parent, textvariable=self.m2_var, width=10)
        self.s1_entry = ttk.Entry(self.parent, textvariable=self.s1_var, width=10)
        self.s2_entry = ttk.Entry(self.parent, textvariable=self.s2_var, width=10)
        self.g_label = ttk.Label(self.parent, textvariable=self.g_var, width=10, anchor="center")

        self.widgets = [
            self.sel_btn, self.subject_entry, self.m1_entry, self.m2_entry,
            self.s1_entry, self.s2_entry, self.g_label
        ]

    def _wire_events(self) -> None:
        for var in (self.m1_var, self.m2_var, self.s1_var, self.s2_var):
            var.trace_add("write", lambda *_: self._update_gNote())
        self.subject_var.trace_add("write", lambda *_: self.on_change() if self.on_change else None)

    def _select_me(self) -> None:
        self.on_select(self.index)

    def grid(self, row: int) -> None:
        self.sel_btn.grid(row=row, column=0, padx=(2, 6), pady=2, sticky="w")
        self.subject_entry.grid(row=row, column=1, padx=6, pady=2, sticky="ew")
        self.m1_entry.grid(row=row, column=2, padx=6, pady=2)
        self.m2_entry.grid(row=row, column=3, padx=6, pady=2)
        self.s1_entry.grid(row=row, column=4, padx=6, pady=2)
        self.s2_entry.grid(row=row, column=5, padx=6, pady=2)
        self.g_label.grid(row=row, column=6, padx=6, pady=2)

    def destroy(self) -> None:
        for w in self.widgets:
            w.destroy()

    def set_index(self, index: int) -> None:
        self.index = index
        self.sel_btn.configure(value=index)

    def _update_gNote(self) -> None:
        m1 = parse_grade(self.m1_var.get())
        m2 = parse_grade(self.m2_var.get())
        s1 = parse_grade(self.s1_var.get())
        s2 = parse_grade(self.s2_var.get())

        self.model.mNote = [m1, m2]
        self.model.sNote = [s1, s2]

        if None in (m1, m2, s1, s2):
            self.model.gNote = None
            self.g_var.set("")
        else:
            gNote = compute_gNote([m1, m2], [s1, s2])
            self.model.gNote = round(gNote, 2)
            self.g_var.set(f"{self.model.gNote:.2f}")

        if self.on_change:
            self.on_change()


class NotenToolApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root
        self.root.title("Schüler-Helfer")

        # File Paths
        self.grades_filename = "noten.txt"
        self.homework_filename = "Hausaufgaben.txt"

        # Noten Data
        self.style = ttk.Style()
        self.is_dark = False
        self.colors = {
            "light": {
                "bg": "#d9d9d9", "fg": "black", "input_bg": "white", "text_insert": "black"
            },
            "dark": {
                "bg": "#2d2d2d", "fg": "white", "input_bg": "#404040", "text_insert": "white"
            }
        }
        self._loading = False
        self.selected_var = tk.IntVar(value=-1)
        self.rows: list[GradeRowUI] = []

        # Homework Data
        self.notes = self.load_notes()
        today = datetime.date.today()
        self.current_year = today.year
        self.current_month = today.month

        self._build_ui()
        self._load_data()

        if not self.rows:
            self._add_row()

        self._update_total_average()

    def _toggle_dark_mode(self) -> None:
        self.is_dark = not self.is_dark
        mode = "dark" if self.is_dark else "light"
        c = self.colors[mode]

        self.theme_btn.configure(text="Light Mode" if self.is_dark else "Dark Mode")

        # Styles
        self.style.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["input_bg"])
        self.style.configure("TLabel", background=c["bg"], foreground=c["fg"])
        self.style.configure("TButton", background=c["bg"], foreground=c["fg"])
        self.style.configure("TEntry", fieldbackground=c["input_bg"], foreground=c["fg"])
        self.style.configure("TRadiobutton", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe", background=c["bg"], foreground=c["fg"])
        self.style.configure("TLabelframe.Label", background=c["bg"], foreground=c["fg"])
        self.style.configure("TNotebook", background=c["bg"])
        self.style.configure("TNotebook.Tab", background=c["bg"], foreground=c["fg"])
        
        # Update
        self.root.configure(bg=c["bg"])
        if hasattr(self, "hw_canvas"):
            self.hw_canvas.configure(bg=c["bg"])
        
        self._refresh_infos_tab()
        self.update_calendar()

    def _build_ui(self) -> None:
        top_frame = ttk.Frame(self)
        top_frame.pack(side="top", fill="x", padx=10, pady=5)
        self.theme_btn = ttk.Button(top_frame, text="Dark Mode", command=self._toggle_dark_mode)
        self.theme_btn.pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)

        self.infos_frame = ttk.Frame(self.notebook)
        grades_frame = ttk.Frame(self.notebook)
        homework_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.infos_frame, text="Infos")
        self.notebook.add(grades_frame, text="Noten")
        self.notebook.add(homework_frame, text="Hausaufgaben")

        self._build_infos_tab(self.infos_frame)
        self._build_grades_tab(grades_frame)
        self._build_homework_tab(homework_frame)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event: tk.Event) -> None:
        if self.notebook.index("current") == 0:
            self._refresh_infos_tab()

    def _build_infos_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        self.info_homework_container = ttk.LabelFrame(parent, text="Anstehende Hausaufgaben (7 Tage)")
        self.info_homework_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.hw_canvas = tk.Canvas(self.info_homework_container, highlightthickness=0)
        self.hw_scrollbar = ttk.Scrollbar(self.info_homework_container, orient="vertical", command=self.hw_canvas.yview)
        self.hw_scrollable_frame = ttk.Frame(self.hw_canvas)

        self.hw_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.hw_canvas.configure(scrollregion=self.hw_canvas.bbox("all"))
        )

        self.hw_canvas_window = self.hw_canvas.create_window((0, 0), window=self.hw_scrollable_frame, anchor="nw")

        self.hw_canvas.bind("<Configure>", lambda e: self.hw_canvas.itemconfig(self.hw_canvas_window, width=e.width))
        self.hw_canvas.configure(yscrollcommand=self.hw_scrollbar.set)

        self.hw_canvas.pack(side="left", fill="both", expand=True)
        self.hw_scrollbar.pack(side="right", fill="y")

        self.info_grades_container = ttk.LabelFrame(parent, text="Notenübersicht")
        self.info_grades_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self._refresh_infos_tab()

    def _refresh_infos_tab(self) -> None:
        for widget in self.hw_scrollable_frame.winfo_children():
            widget.destroy()
        for widget in self.info_grades_container.winfo_children():
            widget.destroy()

        # Hausaufgaben
        today = datetime.date.today()
        found_hw = False
        for i in range(7):
            day = today + datetime.timedelta(days=i)
            key = (day.year, day.month, day.day)
            if key in self.notes:
                found_hw = True
                is_important = i < 3
                fg_color = "red" if is_important else ""
                font = ("TkDefaultFont", 9, "bold") if is_important else ("TkDefaultFont", 9)
                
                f = ttk.Frame(self.hw_scrollable_frame)
                f.pack(fill="x", padx=5, pady=2)
                date_str = day.strftime("%d.%m.%Y")
                ttk.Label(f, text=f"{date_str}:", foreground=fg_color, font=font, anchor="w").pack(side="top", fill="x")
                ttk.Label(f, text=f"{self.notes[key]}", foreground=fg_color, font=font, wraplength=250, justify="left", anchor="w").pack(side="top", fill="x", expand=True)

        if not found_hw:
            ttk.Label(self.hw_scrollable_frame, text="Keine Hausaufgaben in den nächsten 7 Tagen.").pack(padx=5, pady=5)

        # Noten
        valid_grades = [row.model.gNote for row in self.rows if row.model.gNote is not None]
        header_avg_text = "Ø"
        if valid_grades:
            total_avg = sum(valid_grades) / len(valid_grades)
            header_avg_text += f" {total_avg:.2f}"

        ttk.Label(self.info_grades_container, text="Fach", font=("TkDefaultFont", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(self.info_grades_container, text=header_avg_text, font=("TkDefaultFont", 9, "bold")).grid(row=0, column=1, sticky="e", padx=5, pady=5)
        
        r = 1
        for row in self.rows:
            subj = row.subject_var.get()
            if subj:
                avg = row.model.gNote
                avg_str = f"{avg:.2f}" if avg is not None else "-"
                ttk.Label(self.info_grades_container, text=subj).grid(row=r, column=0, sticky="w", padx=5, pady=2)
                ttk.Label(self.info_grades_container, text=avg_str).grid(row=r, column=1, sticky="e", padx=5, pady=2)
                r += 1
        
        self.info_grades_container.columnconfigure(0, weight=1)

    def _build_grades_tab(self, parent: ttk.Frame) -> None:
        # Rows
        self.rows_frame = ttk.Frame(parent)
        self.rows_frame.pack(fill="both", expand=True, padx=10)

        # Header 
        ttk.Label(self.rows_frame, text="Fach", width=24, anchor="w").grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Label(self.rows_frame, text="Mündlich 1").grid(row=0, column=2, padx=6)
        ttk.Label(self.rows_frame, text="Mündlich 2").grid(row=0, column=3, padx=6)
        ttk.Label(self.rows_frame, text="Schriftlich 1").grid(row=0, column=4, padx=6)
        ttk.Label(self.rows_frame, text="Schriftlich 2").grid(row=0, column=5, padx=6)
        ttk.Label(self.rows_frame, text="Gesamt").grid(row=0, column=6, padx=6)
        self.rows_frame.columnconfigure(1, weight=1)

        # Controls
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        add_button = ttk.Button(controls_frame, text="Zeile hinzufügen", command=self._add_row)
        add_button.pack(side="left", padx=5)

        remove_button = ttk.Button(controls_frame, text="Markierte Zeile entfernen", command=self._remove_row)
        remove_button.pack(side="left", padx=5)

        # Average label
        self.avg_g_var = tk.StringVar()
        avg_frame = ttk.Frame(parent)
        avg_frame.pack(fill="x", padx=10, pady=5, side="bottom")
        ttk.Label(avg_frame, text="Gesamtdurchschnitt:").pack(side="left")
        ttk.Label(avg_frame, textvariable=self.avg_g_var, font=("TkDefaultFont", 9, "bold")).pack(side="left")

    # NOTEN SPEICHERN

    def _save_data(self) -> None:
        if self._loading:
            return

        data = [
            [
                row.subject_var.get(),
                row.model.mNote[0], row.model.mNote[1],
                row.model.sNote[0], row.model.sNote[1],
            ] for row in self.rows
        ]

        with open(self.grades_filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _load_data(self) -> None:
        if not os.path.exists(self.grades_filename):
            return

        self._loading = True
        try:
            with open(self.grades_filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            for row_data in data:
                self._add_row(row_data)
        except (json.JSONDecodeError, IOError):
            pass
        self._loading = False
        self._refresh_infos_tab()

    def _add_row(self, data: Optional[list] = None) -> None:
        index = len(self.rows)
        row = GradeRowUI(
            parent=self.rows_frame,
            index=index,
            selected_var=self.selected_var,
            on_select=self._on_row_select,
            on_change=self._on_row_change,
        )
        row.grid(row=index + 1)
        self.rows.append(row)

        if data:
            subject, m1, m2, s1, s2 = data
            row.subject_var.set(subject or "")
            row.m1_var.set(str(m1) if m1 is not None else "")
            row.m2_var.set(str(m2) if m2 is not None else "")
            row.s1_var.set(str(s1) if s1 is not None else "")
            row.s2_var.set(str(s2) if s2 is not None else "")
        
        self._on_row_change()

    def _remove_row(self) -> None:
        selected_index = self.selected_var.get()
        if not (0 <= selected_index < len(self.rows)):
            return

        row_to_remove = self.rows.pop(selected_index)
        row_to_remove.destroy()

        for i in range(selected_index, len(self.rows)):
            self.rows[i].set_index(i)
            self.rows[i].grid(row=i + 1)
        
        self.selected_var.set(-1)
        self._on_row_change()

    def _on_row_select(self, index: int) -> None:
        pass

    def _on_row_change(self) -> None:
        self._update_total_average()
        self._save_data()

    def _update_total_average(self) -> None:
        valid_grades = [row.model.gNote for row in self.rows if row.model.gNote is not None]
        if valid_grades:
            avg = sum(valid_grades) / len(valid_grades)
            self.avg_g_var.set(f"{avg:.2f}")
        else:
            self.avg_g_var.set("")

    # HAUSAUFGABEN

    def _build_homework_tab(self, parent: ttk.Frame) -> None:
        nav_frame = ttk.Frame(parent)
        nav_frame.pack(pady=5)

        ttk.Button(nav_frame, text="<", command=self.prev_month, width=3).pack(side="left", padx=10)
        self.month_year_label = ttk.Label(nav_frame, text="", width=20, anchor="center")
        self.month_year_label.pack(side="left")
        ttk.Button(nav_frame, text=">", command=self.next_month, width=3).pack(side="left", padx=10)

        self.calendar_frame = ttk.Frame(parent)
        self.calendar_frame.pack(pady=5, padx=5, fill="both", expand=True)

        self.update_calendar()

    def load_notes(self) -> dict[tuple[int, int, int], str]:
        if os.path.exists(self.homework_filename):
            try:
                with open(self.homework_filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {eval(k): v for k, v in data.items()}
            except (json.JSONDecodeError, SyntaxError, IOError):
                return {}
        return {}

    def save_Hausaufgaben(self) -> None:
        data_to_save = {str(k): v for k, v in self.notes.items()}
        with open(self.homework_filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)

    def open_note_popup(self, day: int) -> None:
        popup = tk.Toplevel(self.root)
        popup.title(f"Notiz für {day}.{self.current_month}.{self.current_year}")
        popup.geometry("300x250")

        mode = "dark" if self.is_dark else "light"
        c = self.colors[mode]
        popup.configure(bg=c["bg"])

        key = (self.current_year, self.current_month, day)

        text = tk.Text(popup, height=10, wrap="word", bg=c["input_bg"], fg=c["fg"], insertbackground=c["text_insert"])
        text.pack(padx=10, pady=10, fill="both", expand=True)

        text.insert("1.0", self.notes.get(key, ""))

        def save_note() -> None:
            content = text.get("1.0", "end").strip()
            if content:
                self.notes[key] = content
            elif key in self.notes:
                del self.notes[key]

            self.save_Hausaufgaben()
            popup.destroy()
            self.update_calendar()

        ttk.Button(popup, text="Speichern", command=save_note).pack(pady=5)
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

    def update_calendar(self) -> None:
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_year_label.config(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        cal = calendar.monthcalendar(self.current_year, self.current_month)

        for i, day_name in enumerate(calendar.day_abbr):
            ttk.Label(self.calendar_frame, text=day_name, anchor="center").grid(row=0, column=i, sticky="nsew", padx=2, pady=2)

        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                
                key = (self.current_year, self.current_month, day)
                style = "Accent.TButton" if self.notes.get(key) else "TButton"

                day_button = ttk.Button(
                    self.calendar_frame, text=str(day),
                    command=lambda d=day: self.open_note_popup(d), style=style
                )
                day_button.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
        
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(len(cal) + 1):
            self.calendar_frame.rowconfigure(i, weight=1)

    def prev_month(self) -> None:
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()

    def next_month(self) -> None:
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()


def main() -> None:
    root = tk.Tk()
    root.geometry("800x600")
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Style calendar
    style.configure("Accent.TButton", foreground="blue")

    app = NotenToolApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()