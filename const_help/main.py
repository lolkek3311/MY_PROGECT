import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"


import sys
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from disain import Ui_MainWindow
from chat import RAGSystem

# --- ПОТОКИ ---
class LoadThread(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, rag, path):
        super().__init__()
        self.rag = rag
        self.path = path

    def run(self):
        try:
            n = self.rag.load_data(self.path)
            self.finished.emit(f"Успешно! Векторизовано фрагментов: {n}")
        except Exception as e:
            self.finished.emit(f"Ошибка при загрузке: {e}")

class AskThread(QThread):
    ready = pyqtSignal(str, list)
    
    def __init__(self, rag, text):
        super().__init__()
        self.rag = rag
        self.text = text

    def run(self):
        ans, refs = self.rag.ask(self.text)
        self.ready.emit(ans, refs)

# --- ПРИЛОЖЕНИЕ ---
class App(Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # 1. Загрузка UI
        self.setupUi()
        
        # 2. Инициализация логики (может занять пару секунд на загрузку модели)
        self.lbl_status.setText("Загрузка нейросети...")
        QApplication.processEvents() # Чтобы интерфейс обновился
        
        try:
            self.rag = RAGSystem()
            self.lbl_status.setText("Готов к работе")
        except Exception as e:
            QMessageBox.critical(self, "Критическая ошибка", f"Не удалось запустить систему:\n{e}")
            sys.exit(1)
            
        # 3. Кнопки
        self.btn_load_db.clicked.connect(self.load_file)
        self.btn_send.clicked.connect(self.ask_question)
        self.input_field.returnPressed.connect(self.ask_question)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Text (*.txt)")
        if path:
            self.lbl_status.setText("Обработка файла (это займет время)...")
            self.btn_load_db.setEnabled(False)
            
            self.loader = LoadThread(self.rag, path)
            self.loader.finished.connect(self.on_load_done)
            self.loader.start()

    def on_load_done(self, msg):
        self.lbl_status.setText("Готов")
        self.btn_load_db.setEnabled(True)
        QMessageBox.information(self, "Результат", msg)

    def ask_question(self):
        q = self.input_field.text().strip()
        if not q: return
        
        self.chat_display.append(f"<b>Вы:</b> {q}")
        self.input_field.clear()
        self.lbl_status.setText("Думаю...")
        self.btn_send.setEnabled(False)
        
        self.asker = AskThread(self.rag, q)
        self.asker.ready.connect(self.on_answer)
        self.asker.start()

    def on_answer(self, ans, refs):
        self.chat_display.append(f"<b>Бот:</b> {ans}")
        self.chat_display.append("<hr>")
        
        if refs:
            ref_txt = "\n".join(sorted(refs)) # Сортировка статей
            self.ref_display.setText(ref_txt)
        else:
            self.ref_display.setText("Источники не найдены")
            
        self.lbl_status.setText("Готов")
        self.btn_send.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())