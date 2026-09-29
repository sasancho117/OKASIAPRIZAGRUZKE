# import asyncio
# from prisma import Prisma

# async def main() -> None:
#     db = Prisma()
#     await db.connect()

#     clients = await db.clients.find_many()

#     for client in clients:
#         # У объекта будут доступны свойства, совпадающие с колонками в БД
#         print(f"ID: {client.id}, fullname: {client.full_name}, Phone: {client.mobile_phone}")

#     await db.disconnect()

# if __name__ == '__main__':
#     asyncio.run(main())
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox
from async_tkinter_loop import async_handler, async_mainloop
from prisma import Prisma

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление клиентами (Prisma + Tkinter)")
        self.root.geometry("700x450")
        
        # Переменная для отслеживания направления сортировки по колонкам
        self.sort_reverse = {"id": False, "full_name": False, "mobile_phone": False}
        
        # Инициализация Prisma
        self.db = Prisma()
        self.is_connected = False

        self.setup_ui()
        self.root.after(0, async_handler(self.initialize_db))

    def setup_ui(self):
        """Создание основного интерфейса."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Таблица клиентов (Treeview)
        columns = ("id", "full_name", "mobile_phone")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings", selectmode="browse")
        
        # Настройка заголовков с привязкой функции сортировки
        self.tree.heading("id", text="ID", command=lambda: self.sort_column("id", is_numeric=True))
        self.tree.heading("full_name", text="ФИО", command=lambda: self.sort_column("full_name", is_numeric=False))
        self.tree.heading("mobile_phone", text="Телефон", command=lambda: self.sort_column("mobile_phone", is_numeric=False))
        
        self.tree.column("id", width=60, anchor=tk.CENTER)
        self.tree.column("full_name", width=250)
        self.tree.column("mobile_phone", width=150)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.tree)

        # Панель кнопок
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.btn_refresh = ttk.Button(btn_frame, text="Обновить список", command=async_handler(self.load_clients))
        self.btn_refresh.pack(side=tk.LEFT, padx=5)

        self.btn_edit = ttk.Button(btn_frame, text="Просмотр / Редактировать", command=self.open_edit_window)
        self.btn_edit.pack(side=tk.LEFT, padx=5)
        
        self.tree.bind("<Double-1>", lambda event: self.open_edit_window())

    def sort_column(self, col: str, is_numeric: bool):
        """Сортировка содержимого таблицы по выбранной колонке."""
        # Получаем все элементы таблицы (их id и значения)
        items = [(self.tree.set(item_id, col), item_id) for item_id in self.tree.get_children("")]
        
        # Если колонка числовая, приводим значения к int для правильного сравнения (чтобы 10 было больше 2)
        if is_numeric:
            try:
                items = [(int(val), item_id) for val, item_id in items]
            except ValueError:
                pass  # Если в ID лежит UUID или строка, оставляем как есть

        # Сортируем список элементов
        reverse_dir = self.sort_reverse[col]
        items.sort(reverse=reverse_dir)

        # Перемещаем элементы в таблице в новом порядке
        for index, (_, item_id) in enumerate(items):
            self.tree.move(item_id, "", index)

        # Сбрасываем стрелочки у всех колонок и ставим нужную у текущей
        headers = {"id": "ID", "full_name": "ФИО", "mobile_phone": "Телефон"}
        for c in headers:
            self.tree.heading(c, text=headers[c])
            
        arrow = " ▼" if reverse_dir else " ▲"
        self.tree.heading(col, text=headers[col] + arrow)

        # Меняем направление для следующего клика по этой же колонке
        self.sort_reverse[col] = not reverse_dir

    async def initialize_db(self):
        """Асинхронное подключение к базе данных после старта event loop."""
        try:
            await self.db.connect()
            self.is_connected = True
            await self.load_clients()
        except Exception as e:
            messagebox.showerror("Ошибка БД", f"Не удалось подключиться к базе данных:\n{e}")

    async def load_clients(self):
        """Потокобезопасная загрузка списка клиентов в таблицу."""
        if not self.is_connected:
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            clients = await self.db.clients.find_many()
            for client in clients:
                self.tree.insert("", tk.END, iid=client.id, values=(client.id, client.full_name, client.mobile_phone))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных:\n{e}")

    def open_edit_window(self):
        """Открытие модального окна для просмотра и редактирования."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Внимание", "Выберите клиента из списка!")
            return

        client_id = selected_item[0]
        values = self.tree.item(client_id, "values")
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title(f"Клиент ID: {client_id}")
        edit_win.geometry("350x200")
        edit_win.transient(self.root)
        edit_win.grab_set()

        ttk.Label(edit_win, text="ФИО:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        name_entry = ttk.Entry(edit_win, width=40)
        name_entry.insert(0, values[1])
        name_entry.pack(padx=10, fill=tk.X)

        ttk.Label(edit_win, text="Телефон:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        phone_entry = ttk.Entry(edit_win, width=40)
        phone_entry.insert(0, values[2])
        phone_entry.pack(padx=10, fill=tk.X)

        async def save_changes():
            new_name = name_entry.get().strip()
            new_phone = phone_entry.get().strip()

            if not new_name:
                messagebox.showerror("Ошибка", "ФИО не может быть пустым", parent=edit_win)
                return

            try:
                try:
                    db_id = int(client_id)
                except ValueError:
                    db_id = client_id

                await self.db.clients.update(
                    where={"id": db_id},
                    data={
                        "full_name": new_name,
                        "mobile_phone": new_phone
                    }
                )
                self.tree.item(client_id, values=(client_id, new_name, new_phone))
                edit_win.destroy()
                messagebox.showinfo("Успех", "Данные клиента успешно обновлены!")
            except Exception as e:
                messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить:\n{e}", parent=edit_win)

        btn_frame = ttk.Frame(edit_win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Сохранить", command=async_handler(save_changes)).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=edit_win.destroy).pack(side=tk.RIGHT)

    async def close_db(self):
        """Закрытие соединения перед выходом."""
        if self.is_connected:
            await self.db.disconnect()

def main():
    root = tk.Tk()
    app = App(root)
    
    def on_closing():
        asyncio.create_task(app.close_db())
        root.destroy()
        
    root.protocol("WM_DELETE_WINDOW", on_closing)
    async_mainloop(root)

if __name__ == '__main__':
    main()
