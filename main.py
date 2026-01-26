from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Callable

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


class GradeRowUI:
    def __init__(
        self,
        parent: ttk.Frame,
        index: int,
        selected_var: tk.IntVar,
        on_select: Callable[[int], None],
    ) -> None:
        self.parent = parent
        self.index = index
        self.selected_var = selected_var
        self.on_select = on_select

        self.model = GradeRowModel(mNote=[None, None], sNote=[None, None], gNote=None)

        self.subject_var = tk.StringVar(value="")
        self.m1_var = tk.StringVar(value="")
        self.m2_var = tk.StringVar(value="")
        self.s1_var = tk.StringVar(value="")
        self.s2_var = tk.StringVar(value="")
        self.g_var = tk.StringVar(value="")

        self.row_frame = ttk.Frame(parent)
        self._build_widgets()
        self._wire_events()
        self._update_gNote()

    def _build_widgets(self) -> None:
        self.sel_btn = ttk.Radiobutton(
            self.row_frame,
            variable=self.selected_var,
            value=self.index,
            command=self._select_me,
        )

        self.subject_entry = ttk.Entry(self.row_frame, textvariable=self.subject_var, width=22)

        self.m1_entry = ttk.Entry(self.row_frame, textvariable=self.m1_var, width=10)
        self.m2_entry = ttk.Entry(self.row_frame, textvariable=self.m2_var, width=10)
        self.s1_entry = ttk.Entry(self.row_frame, textvariable=self.s1_var, width=10)
        self.s2_entry = ttk.Entry(self.row_frame, textvariable=self.s2_var, width=10)

        self.g_label = ttk.Label(self.row_frame, textvariable=self.g_var, width=10, anchor="center")

        self.sel_btn.grid(row=0, column=0, padx=(2, 6), pady=2, sticky="w")
        self.subject_entry.grid(row=0, column=1, padx=6, pady=2, sticky="ew")
        self.m1_entry.grid(row=0, column=2, padx=6, pady=2)
        self.m2_entry.grid(row=0, column=3, padx=6, pady=2)
        self.s1_entry.grid(row=0, column=4, padx=6, pady=2)
        self.s2_entry.grid(row=0, column=5, padx=6, pady=2)
        self.g_label.grid(row=0, column=6, padx=6, pady=2)

        self.row_frame.columnconfigure(1, weight=1)

    def _wire_events(self) -> None:
        for var in (self.m1_var, self.m2_var, self.s1_var, self.s2_var):
            var.trace_add("write", lambda *_: self._update_gNote())

    def _select_me(self) -> None:
        self.on_select(self.index)

    def grid(self, row: int) -> None:
        self.row_frame.grid(row=row, column=0, sticky="ew")
        self.row_frame.columnconfigure(1, weight=1)

    def destroy(self) -> None:
        self.row_frame.destroy()

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
            return

        gNote = compute_gNote([m1, m2], [s1, s2])
        self.model.gNote = round(gNote, 2)
        self.g_var.set(f"{self.model.gNote:.2f}")


class NotenToolApp(ttk.Frame):
    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root = root

        self.selected_var = tk.IntVar(value=-1)
        self.rows: list[GradeRowUI] = []

        self._build_ui()
        self._add_row()

    def _build_ui(self) -> None:
        self.root.title("Noten-Tool")
        self.root.minsize(820, 420)

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=12, pady=(12, 6))

        ttk.Label(header, text="").grid(row=0, column=0, padx=(2, 6), sticky="w")
        ttk.Label(header, text="Fach").grid(row=0, column=1, padx=6, sticky="w")
        ttk.Label(header, text="mNote 1").grid(row=0, column=2, padx=6)
        ttk.Label(header, text="mNote 2").grid(row=0, column=3, padx=6)
        ttk.Label(header, text="sNote 1").grid(row=0, column=4, padx=6)
        ttk.Label(header, text="sNote 2").grid(row=0, column=5, padx=6)
        ttk.Label(header, text="gNote").grid(row=0, column=6, padx=6)

        header.columnconfigure(1, weight=1)
        self.rows_container = ttk.Frame(self.root)
        self.rows_container.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.rows_container.columnconfigure(0, weight=1)

        controls = ttk.Frame(self.root)
        controls.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Button(controls, text="Zeile hinzufügen", command=self._add_row).pack(side="left")
        ttk.Button(controls, text="Markierte Zeile löschen", command=self._delete_selected).pack(
            side="left", padx=8
        )

    def _on_select_row(self, index: int) -> None:
        self.selected_var.set(index)

    def _add_row(self) -> None:
        row = GradeRowUI(
            self.rows_container,
            index=len(self.rows),
            selected_var=self.selected_var,
            on_select=self._on_select_row,
        )
        self.rows.append(row)
        self._regrid_rows()

    def _delete_selected(self) -> None:
        index = self.selected_var.get()
        if not (0 <= index < len(self.rows)):
            return

        self.rows[index].destroy()
        del self.rows[index]
        self.selected_var.set(-1)

        for i, r in enumerate(self.rows):
            r.set_index(i)

        self._regrid_rows()

    def _regrid_rows(self) -> None:
        for widget in self.rows_container.winfo_children():
            widget.grid_forget()

        for i, row in enumerate(self.rows):
            row.grid(i)

        self.rows_container.columnconfigure(0, weight=1)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass

    app = NotenToolApp(root)
    app.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
