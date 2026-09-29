
"""SnapDesk AI - local-first AI workbench for Snapdragon-powered HP PCs."""
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout,
                               QPushButton, QTextEdit, QFileDialog, QWidget, QLabel,
                               QComboBox, QHBoxLayout)
from PySide6.QtCore import Qt
from core.npu import system_profile, accelerator_label
from core.doc_chat import DocChat
from core.study_tools import StudyTools
from core.translate import OfflineTranslate, TARGET_LANGS

# ---- lazy singletons: app launches even before models are downloaded ----
class Services:
    def __init__(self):
        self._chat = None; self._voice = None; self._snap = None
        self._ocr = None; self._narrate = None; self._lecture = None

    @property
    def chat(self):
        if not self._chat:
            try: self._chat = DocChat("models/qwen")
            except Exception as e: raise RuntimeError(f"Load models/qwen first: {e}")
        return self._chat

    def try_load(self, name, fn):
        if getattr(self, name) is None:
            try: setattr(self, name, fn())
            except Exception: setattr(self, name, "unavailable")
        return getattr(self, name)

S = Services()

class DropZone(QTextEdit):
    def __init__(self, on_drop):
        super().__init__(); self.on_drop = on_drop
        self.setAcceptDrops(True)
        self.setPlaceholderText("Drag & drop files here...")
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e):
        self.on_drop([u.toLocalFile() for u in e.mimeData().urls()])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SnapDesk AI - 100% on-device - 8 tools")
        self.cards = []
        tabs = QTabWidget(); self.setCentralWidget(tabs)
        accel = QLabel(f"Accelerator: {accelerator_label()}  |  {system_profile()['machine']}")

        # 1. Doc Chat
        t1 = QWidget(); lay = QVBoxLayout(t1)
        self.doc_out = DropZone(self._load_pdf); self.doc_out.setReadOnly(True)
        row = QHBoxLayout()
        for label, fn in [("Summarize", "summarize"), ("Explain", "explain")]:
            b = QPushButton(label); b.clicked.connect(lambda _, f=fn: self._run_doc(f)); row.addWidget(b)
        self.ask = QTextEdit(); self.ask.setMaximumHeight(60)
        self.ask.setPlaceholderText("Ask a question about the loaded PDF...")
        ba = QPushButton("Ask"); ba.clicked.connect(self._ask)
        lay.addWidget(accel); lay.addWidget(self.doc_out); lay.addLayout(row)
        lay.addWidget(self.ask); lay.addWidget(ba)

        # 2. Voice Notes
        t2 = QWidget(); lay2 = QVBoxLayout(t2)
        self.notes_out = QTextEdit(readOnly=True)
        rec = QPushButton("Record 60s -> Structured Notes"); rec.clicked.connect(self._voice_notes)
        lay2.addWidget(rec); lay2.addWidget(self.notes_out)

        # 3. Snap Explain
        t3 = QWidget(); lay3 = QVBoxLayout(t3)
        self.snap_out = QTextEdit(readOnly=True)
        cap = QPushButton("Capture Full Screen + Explain"); cap.clicked.connect(self._snap)
        lay3.addWidget(cap); lay3.addWidget(self.snap_out)

        # 4. Flashcards
        t4 = QWidget(); lay4 = QVBoxLayout(t4)
        self.fc_out = QTextEdit(readOnly=True)
        b4 = QPushButton("Generate Flashcards from PDF"); b4.clicked.connect(self._flashcards)
        b4e = QPushButton("Export Anki CSV"); b4e.clicked.connect(self._export_anki)
        lay4.addWidget(b4); lay4.addWidget(b4e); lay4.addWidget(self.fc_out)

        # 5. Quiz
        t5 = QWidget(); lay5 = QVBoxLayout(t5)
        self.quiz_out = QTextEdit(readOnly=True)
        b5 = QPushButton("Generate MCQ Quiz"); b5.clicked.connect(self._quiz)
        lay5.addWidget(b5); lay5.addWidget(self.quiz_out)

        # 6. Study Plan
        t6 = QWidget(); lay6 = QVBoxLayout(t6)
        self.plan_out = QTextEdit(readOnly=True)
        b6 = QPushButton("Build 7-Day Study Plan"); b6.clicked.connect(self._plan)
        lay6.addWidget(b6); lay6.addWidget(self.plan_out)

        # 7. HandyNotes OCR
        t7 = QWidget(); lay7 = QVBoxLayout(t7)
        self.ocr_out = QTextEdit(readOnly=True)
        dz = DropZone(self._ocr); dz.setMaximumHeight(80); dz.setPlaceholderText("Drop photos of handwritten notes here")
        lay7.addWidget(dz); lay7.addWidget(self.ocr_out)

        # 8. Translate + Speak
        t8 = QWidget(); lay8 = QVBoxLayout(t8)
        self.tr_out = QTextEdit(readOnly=True)
        row8 = QHBoxLayout()
        self.lang = QComboBox(); self.lang.addItems(TARGET_LANGS)
        b8 = QPushButton("Translate PDF text"); b8.clicked.connect(self._translate)
        b8n = QPushButton("Read Summary Aloud"); b8n.clicked.connect(self._speak)
        row8.addWidget(self.lang); row8.addWidget(b8); row8.addWidget(b8n)
        lay8.addLayout(row8); lay8.addWidget(self.tr_out)

        for t, name in [(t1,"Doc Chat"),(t2,"Voice Notes"),(t3,"Snap Explain"),(t4,"Flashcards"),
                        (t5,"Quiz"),(t6,"Study Plan"),(t7,"HandyNotes OCR"),(t8,"Translate+Speak")]:
            tabs.addTab(t, name)

    # ---- helpers ----
    def _show(self, widget, text): widget.setPlainText(str(text))
    def _load_pdf(self, paths):
        try: self._show(self.doc_out, S.chat.load_pdf(paths[0]))
        except Exception as e: self._show(self.doc_out, f"Error: {e}")
    def _run_doc(self, fn):
        try: self._show(self.doc_out, getattr(S.chat, fn)())
        except Exception as e: self._show(self.doc_out, f"Error: {e}")
    def _ask(self):
        try: self._show(self.doc_out, S.chat.ask(self.ask.toPlainText()))
        except Exception as e: self._show(self.doc_out, f"Error: {e}")
    def _voice_notes(self):
        def go():
            from core.voice import VoiceNotes
            v = S.try_load("_voice", lambda: VoiceNotes("models/whisper", S.chat))
            if v == "unavailable": return "Download Whisper model (see MODELS.md)"
            v.record(60); return v.structured_notes()
        self._show(self.notes_out, go())
    def _snap(self):
        def go():
            from core.screenshot import SnapExplain
            s = S.try_load("_snap", lambda: SnapExplain(S.chat))
            if s == "unavailable": return "Download Florence-2 (see MODELS.md)"
            return s.describe()
        self._show(self.snap_out, go())
    def _flashcards(self):
        try:
            from core.study_tools import StudyTools
            self.cards = StudyTools(S.chat).flashcards(S.chat.doc_text)
            self._show(self.fc_out, "\n\n".join(f"Q: {c['q']}\nA: {c['a']}" for c in self.cards))
        except Exception as e: self._show(self.fc_out, f"Error: {e}")
    def _export_anki(self):
        from core.study_tools import StudyTools
        p, _ = QFileDialog.getSaveFileName(self, "Save Anki CSV", "flashcards.csv")
        if p: StudyTools(S.chat).export_anki(self.cards, p)
    def _quiz(self):
        try: self._show(self.quiz_out, __import__("core.study_tools", fromlist=["StudyTools"]).StudyTools(S.chat).quiz(S.chat.doc_text))
        except Exception as e: self._show(self.quiz_out, f"Error: {e}")
    def _plan(self):
        try: self._show(self.plan_out, __import__("core.study_tools", fromlist=["StudyTools"]).StudyTools(S.chat).study_plan(S.chat.doc_text))
        except Exception as e: self._show(self.plan_out, f"Error: {e}")
    def _ocr(self, paths):
        def go():
            from core.ocr_notes import HandwrittenOCR
            o = S.try_load("_ocr", lambda: HandwrittenOCR(S.chat))
            if o == "unavailable": return "Download TrOCR model (see MODELS.md)"
            _, organized = o.make_searchable(paths)
            return organized
        self._show(self.ocr_out, go())
    def _translate(self):
        try: self._show(self.tr_out, OfflineTranslate(S.chat).translate(S.chat.doc_text or "(no document)", self.lang.currentText()))
        except Exception as e: self._show(self.tr_out, f"Error: {e}")
    def _speak(self):
        def go():
            from core.narrate import Narrate
            n = S.try_load("_narrate", lambda: Narrate("models/tts-voices/en/en_US/lessac/medium/en_US-lessac-medium.onnx"))
            if n == "unavailable": return "Download Piper voice (see MODELS.md)"
            n.speak(S.chat.doc_text[:1500]); return "Playing..."
        self._show(self.tr_out, go())

if __name__ == "__main__":
    app = QApplication(sys.argv); win = MainWindow(); win.resize(960, 680); win.show()
    sys.exit(app.exec())
