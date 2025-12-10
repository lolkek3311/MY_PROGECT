import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QSplitter)
from PyQt5.QtCore import Qt

class Ui_MainWindow(QWidget):
    def setupUi(self):
        self.setWindowTitle("Конституционный помощник (Local RAG)")
        self.resize(1000, 700)
        
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Верх
        top = QHBoxLayout()
        self.btn_load_db = QPushButton("Загрузить Конституцию в БД")
        self.lbl_status = QLabel("Запуск...")
        top.addWidget(self.btn_load_db)
        top.addWidget(self.lbl_status)
        top.addStretch()
        main_layout.addLayout(top)

        # Центр (Сплиттер)
        splitter = QSplitter(Qt.Horizontal)
        
        # Чат
        chat_w = QWidget()
        chat_l = QVBoxLayout()
        chat_w.setLayout(chat_l)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_l.addWidget(QLabel("Диалог:"))
        chat_l.addWidget(self.chat_display)
        
        # Ссылки
        ref_w = QWidget()
        ref_l = QVBoxLayout()
        ref_w.setLayout(ref_l)
        self.ref_display = QTextEdit()
        self.ref_display.setReadOnly(True)
        ref_l.addWidget(QLabel("Статьи:"))
        ref_l.addWidget(self.ref_display)
        
        splitter.addWidget(chat_w)
        splitter.addWidget(ref_w)
        splitter.setSizes([700, 300])
        main_layout.addWidget(splitter)

        # Низ
        inp_l = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите вопрос...")
        self.btn_send = QPushButton("Отправить")
        inp_l.addWidget(self.input_field)
        inp_l.addWidget(self.btn_send)
        main_layout.addLayout(inp_l)