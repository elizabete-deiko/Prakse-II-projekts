import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .engine import analyse
from .reports import export


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / 'data'


class HealthCheckApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('ILIM Health Check')
        self.geometry('1100x680')
        self.result = None

        self.tms = tk.StringVar(value=str(DATA / 'TMS.xlsx'))
        self.mars = tk.StringVar(value=str(DATA / 'MARS.xlsx'))
        self.ova = tk.StringVar(value=str(DATA / 'OVA'))
        self.agency = tk.StringVar(value='Visas')
        self.direction = tk.StringVar(value='Abi')
        self.check_date = tk.StringVar()
        self.message = tk.StringVar(value='Izvēlies datu failus un nospied Analizēt.')

        self.build_window()

    def add_file_row(self, parent, title, variable, is_ova=False):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=title, width=12).pack(side='left')
        ttk.Entry(row, textvariable=variable).pack(side='left', fill='x', expand=True)

        def choose():
            if is_ova:
                path = filedialog.askdirectory(title='Izvēlies OVA mapi')
                if not path:
                    path = filedialog.askopenfilename(filetypes=[('TXT', '*.txt')])
            else:
                path = filedialog.askopenfilename(
                    filetypes=[('Excel vai CSV', '*.xlsx *.csv')])
            if path:
                variable.set(path)

        ttk.Button(row, text='Izvēlēties', command=choose).pack(side='left', padx=6)

    def build_window(self):
        frame = ttk.Frame(self, padding=14)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text='ILIM Health Check',
                  font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='TMS, OVA un MARS sintētisko datu pārbaude').pack(anchor='w', pady=5)

        self.add_file_row(frame, 'TMS', self.tms)
        self.add_file_row(frame, 'MARS', self.mars)
        self.add_file_row(frame, 'OVA SQL', self.ova, True)

        filters = ttk.Frame(frame)
        filters.pack(fill='x', pady=12)
        ttk.Label(filters, text='Aģentūra').pack(side='left')
        ttk.Combobox(filters, textvariable=self.agency, width=8,
                     values=['Visas', 'US', 'BR', 'ZA'], state='readonly').pack(side='left', padx=5)
        ttk.Label(filters, text='Virziens').pack(side='left', padx=(12, 0))
        ttk.Combobox(filters, textvariable=self.direction, width=10,
                     values=['Abi', 'Import', 'Export'], state='readonly').pack(side='left', padx=5)
        ttk.Label(filters, text='Datums (GGGG-MM-DD)').pack(side='left', padx=(12, 0))
        ttk.Entry(filters, textvariable=self.check_date, width=14).pack(side='left', padx=5)
        ttk.Button(filters, text='Analizēt', command=self.run_check).pack(side='left', padx=6)
        ttk.Button(filters, text='Saglabāt', command=self.save_report).pack(side='left')

        ttk.Label(frame, textvariable=self.message).pack(anchor='w', pady=6)
        columns = ['Aģentūra', 'Līguma numurs', 'Sistēma', 'Parametrs',
                   'Sagaidāmā vērtība', 'Faktiskā vērtība']
        self.columns = columns
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill='both', expand=True)
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings')
        for column in columns:
            self.table.heading(column, text=column)
            self.table.column(column, width=150)
        self.table.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(table_frame, command=self.table.yview)
        scrollbar.pack(side='right', fill='y')
        self.table.configure(yscrollcommand=scrollbar.set)

        self.details = tk.StringVar(value='Izvēlies rindu, lai apskatītu detaļas.')
        ttk.Label(frame, textvariable=self.details, wraplength=1000).pack(anchor='w', pady=10)
        self.table.bind('<<TreeviewSelect>>', self.show_details)

    def run_check(self):
        agency = None if self.agency.get() == 'Visas' else self.agency.get()
        direction = None if self.direction.get() == 'Abi' else self.direction.get()
        check_date = self.check_date.get().strip() or None

        try:
            self.result = analyse(self.tms.get(), self.mars.get(), self.ova.get(),
                                  agency, direction, check_date)
        except (OSError, ValueError) as error:
            messagebox.showerror('Kļūda', str(error))
            return

        for row in self.table.get_children():
            self.table.delete(row)
        for index, issue in enumerate(self.result.issues):
            values = [issue.get(column, '') for column in self.columns]
            self.table.insert('', 'end', iid=str(index), values=values)

        totals = self.result.totals
        self.message.set(
            f"Pārbaudīti {totals['TMS līgumi']} līgumi. "
            f"Atrastas {totals['Neatbilstības']} neatbilstības."
        )

    def show_details(self, event):
        selected = self.table.selection()
        if not selected or self.result is None:
            return
        issue = self.result.issues[int(selected[0])]
        self.details.set(
            f"{issue['Exception Name']} | {issue['Parametrs']} | "
            f"{issue['Paskaidrojums']}"
        )

    def save_report(self):
        if self.result is None:
            messagebox.showinfo('Pārskats', 'Vispirms veic analīzi.')
            return
        filename = filedialog.asksaveasfilename(
            defaultextension='.xlsx',
            filetypes=[('Excel', '*.xlsx'), ('CSV', '*.csv')]
        )
        if filename:
            try:
                export(self.result, filename)
                messagebox.showinfo('Saglabāts', filename)
            except (OSError, ValueError) as error:
                messagebox.showerror('Kļūda', str(error))


def start_gui():
    app = HealthCheckApp()
    app.mainloop()
