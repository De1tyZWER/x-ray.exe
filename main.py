import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logic


class ModUpdaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("X-RAY checker")
        self.root.geometry("700x600")
        self.root.minsize(550, 500)

        self.config = logic.load_config()
        self.setup_ui()

    def setup_ui(self):
        # Фрейм локальной папки
        local_frame = ttk.LabelFrame(self.root, text="Локальная папка (Игра)", padding=10)
        local_frame.pack(fill=tk.X, padx=10, pady=5)

        self.user_dir_var = tk.StringVar(value=self.config.get("user_dir", ""))
        self.entry_user = ttk.Entry(local_frame, textvariable=self.user_dir_var)
        self.entry_user.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(local_frame, text="Выбрать...", command=self.select_user_dir).pack(side=tk.RIGHT)

        # Фрейм сервера
        srv_frame = ttk.LabelFrame(self.root, text="Настройки сервера", padding=10)
        srv_frame.pack(fill=tk.X, padx=10, pady=5)

        # IP
        ttk.Label(srv_frame, text="IP адрес:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ip_var = tk.StringVar(value=self.config.get("server_ip", ""))
        ttk.Entry(srv_frame, textvariable=self.ip_var, width=20).grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        # Порт
        ttk.Label(srv_frame, text="Порт:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10, 0))
        self.port_var = tk.StringVar(value=self.config.get("server_port", ""))
        ttk.Entry(srv_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)

        # Путь
        ttk.Label(srv_frame, text="Путь (API):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.path_var = tk.StringVar(value=self.config.get("server_path", ""))
        ttk.Entry(srv_frame, textvariable=self.path_var, width=20).grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        # Кнопки сервера
        btn_srv_frame = ttk.Frame(srv_frame)
        btn_srv_frame.grid(row=1, column=2, columnspan=2, pady=2, sticky=tk.E)
        ttk.Button(btn_srv_frame, text="Проверить соединение", command=self.run_test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_srv_frame, text="Сохранить", command=self._save_current_config).pack(side=tk.LEFT)

        opt_frame = ttk.LabelFrame(self.root, text="Опции", padding=10)
        opt_frame.pack(fill=tk.X, padx=10, pady=5)

        self.confirm_del_var = tk.BooleanVar(value=self.config.get("confirm_delete", True))
        ttk.Checkbutton(opt_frame, text="Подтверждать удаление лишних модов", variable=self.confirm_del_var).pack(
            anchor=tk.W)

        self.copy_missing_var = tk.BooleanVar(value=self.config.get("copy_missing", True))
        ttk.Checkbutton(opt_frame, text="Автоматически скачивать недостающие моды", variable=self.copy_missing_var).pack(anchor=tk.W)

        # Основные кнопки
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=tk.X)

        self.btn_sync = ttk.Button(btn_frame, text="Проверить и Синхронизировать", command=self.run_sync)
        self.btn_sync.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить лог", command=self.clear_log).pack(side=tk.RIGHT, padx=5)

        # Лог
        log_frame = ttk.LabelFrame(self.root, text="Журнал событий", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.safe_log("Приложение запущено. Укажите настройки и нажмите 'Проверить и Синхронизировать'.")

    def safe_log(self, message):
        """Безопасный вывод в лог из любого потока."""
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def select_user_dir(self):
        path = filedialog.askdirectory(title="Выберите папку с вашими модами")
        if path:
            self.user_dir_var.set(path)
            self._save_current_config()

    def _save_current_config(self):
        self.config["user_dir"] = self.user_dir_var.get()
        self.config["server_ip"] = self.ip_var.get()
        self.config["server_port"] = self.port_var.get()
        self.config["server_path"] = self.path_var.get()
        self.config["confirm_delete"] = self.confirm_del_var.get()
        self.config["copy_missing"] = self.copy_missing_var.get()
        logic.save_config(self.config)
        self.safe_log("⚙️ Настройки сохранены.")

    def run_test_connection(self):
        """Запуск проверки в отдельном потоке."""
        self._save_current_config()
        threading.Thread(target=self._test_connection_thread, daemon=True).start()

    def _test_connection_thread(self):
        self.safe_log("\nПроверка соединения с сервером...")
        success, msg = logic.test_connection(self.ip_var.get(), self.port_var.get(), self.path_var.get())
        if success:
            self.safe_log(f"✅ {msg}")
        else:
            self.safe_log(f"❌ {msg}")

    def run_sync(self):
        self._save_current_config()
        user_dir = self.user_dir_var.get()

        if not os.path.isdir(user_dir):
            messagebox.showerror("Ошибка", "Папка пользователя не существует или не выбрана!")
            return

        self.btn_sync.config(state=tk.DISABLED)
        threading.Thread(target=self._sync_thread, args=(user_dir,), daemon=True).start()

    def _sync_thread(self, user_dir):
        try:
            self.safe_log("\n--- Запуск проверки ---")
            self.safe_log("Подключение к серверу для получения списка модов...")

            # Получение списка с сервера
            server_mods = logic.get_server_mods(self.ip_var.get(), self.port_var.get(), self.path_var.get())
            self.safe_log(f"Получено модов в эталоне: {len(server_mods)}")

            # Сравнение
            extra, missing = logic.compare_mods(user_dir, server_mods)

            if not extra and not missing:
                self.safe_log("✅ Ваша сборка полностью совпадает с сервером!")
                return

            # --- Обработка лишних ---
            if extra:
                self.safe_log(f"⚠️ Найдено лишних модов: {len(extra)}")
                proceed_delete = True

                if self.confirm_del_var.get():
                    # Вызов окна подтверждения должен быть в главном потоке
                    proceed_delete = self._ask_confirmation(
                        f"Найдено {len(extra)} лишних модов. Удалить их?\n\nПервые 10:\n" + "\n".join(extra[:10]))

                if proceed_delete:
                    for mod in extra:
                        success, msg = logic.delete_mod(user_dir, mod)
                        self.safe_log(f"  - {msg}")
                else:
                    self.safe_log("❌ Удаление лишних модов отменено.")

            # --- Обработка недостающих ---
            if missing:
                self.safe_log(f"📥 Не хватает модов: {len(missing)}")
                if self.copy_missing_var.get():
                    self.safe_log("Начало загрузки...")
                    for mod in missing:
                        success, msg = logic.download_mod(
                            self.ip_var.get(), self.port_var.get(),
                            self.path_var.get(), mod, user_dir
                        )
                        self.safe_log(f"  - {msg}")
                    self.safe_log("✅ Загрузка завершена!")
                else:
                    for mod in missing:
                        self.safe_log(f"  - [Отсутствует] {mod}")
                    self.safe_log("ℹ️ Автозагрузка отключена. Моды не скачаны.")

            self.safe_log("--- Синхронизация завершена ---")

        except Exception as e:
            self.safe_log(f"❌ Критическая ошибка: {e}")
        finally:
            self.root.after(0, lambda: self.btn_sync.config(state=tk.NORMAL))  # Разблокируем кнопку

    def _ask_confirmation(self, message):
        """Синхронный вызов messagebox из дочернего потока через event."""
        result = [False]
        event = threading.Event()

        def ask():
            result[0] = messagebox.askyesno("Удаление модов", message)
            event.set()

        self.root.after(0, ask)
        event.wait()
        return result[0]


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style(root)
    style.theme_use('clam')
    app = ModUpdaterApp(root)
    root.mainloop()