import sys, os, sqlite3, calendar, datetime
from PyQt5 import (QtWidgets, QtGui, QtCore)

DB = 'eduquest_gui.db'
NOTES_DIR = 'eduquest_notes'
PRIMARY_COLOR = '#4a148c'
ACCENT_COLOR = '#7b45ff'
BACKGROUND_DARK = '#2d2d3c'
BACKGROUND_LIGHT = '#ffffff'
CARD_BACKGROUND = '#3a3a4c'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            title TEXT NOT NULL, 
            date TEXT NOT NULL, 
            time TEXT 
        )
    """)
    
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            type TEXT NOT NULL, 
            start_time TEXT NOT NULL, 
            end_time TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL
        )
    """)
    
    conn.commit()

    try:
        c.execute("SELECT time FROM events LIMIT 1")
    except sqlite3.OperationalError:
        print("MIGRATING DATABASE: Adding 'time' column to events table.")
        c.execute("ALTER TABLE events ADD COLUMN time TEXT")
        conn.commit()
    
    conn.close()
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)

GLOBAL_STYLE = f"""
    QMainWindow {{
        background-color: {BACKGROUND_DARK}; 
    }}
    QDialog {{
        background-color: {BACKGROUND_LIGHT};
        border-radius: 12px;
    }}
    
    QPushButton {{
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PRIMARY_COLOR}, stop:1 {ACCENT_COLOR});
        color: white; 
        border-radius: 18px; 
        padding: 8px 16px; 
        font-weight: 700;
        min-width: 90px;
    }}
    QPushButton:hover {{ 
        background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PRIMARY_COLOR}, stop:1 #a842eb);
        border: 2px solid #ffffff33;
    }}
    
    QLineEdit, QPlainTextEdit, QTimeEdit {{
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        background-color: {BACKGROUND_LIGHT};
    }}
    QTimeEdit::up-button, QTimeEdit::down-button {{
        border: none;
        background-color: transparent;
    }}
    QListWidget {{
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 5px;
        background-color: {BACKGROUND_LIGHT};
        outline: none;
    }}
    QListWidget::item:selected {{
        background-color: #f0f0ff;
        color: {PRIMARY_COLOR};
    }}
    
    QTableWidget {{
        background-color: {BACKGROUND_DARK}; 
        border: none;
        gridline-color: #3f3f50;
        font-size: 14px;
        color: white;
    }}
    QHeaderView::section {{
        background-color: #3a3a4c;
        color: #ffffff;
        padding: 8px;
        border: 1px solid {BACKGROUND_DARK};
        font-weight: 600;
        font-size: 15px;
    }}
    QTableWidget QWidget {{
        background-color: {CARD_BACKGROUND};
        border-radius: 8px;
        margin: 4px;
        padding: 0;
    }}
"""
EVENT_LABEL_STYLE = f"""
    background-color: {ACCENT_COLOR}aa;
    color: white; 
    border-left: 6px solid #ffd54f; 
    padding: 6px; 
    border-radius: 4px; 
    font-weight: 600;
    margin-bottom: 2px;
    font-size: 11px;
"""

HEADER_LOGO_STYLE = f"font-weight:900; font-size:24px; color:{ACCENT_COLOR};"

class RoundLogo(QtWidgets.QLabel):
    def __init__(self, path, size=64):
        super().__init__()
        self.size = size
        self.setFixedSize(size, size)
        
        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            self.setText("EQ")
            self.setStyleSheet(f"font-weight:900; font-size:{int(size*0.4)}px; color:white; background-color:{ACCENT_COLOR}; border-radius: {size//2}px; text-align: center;")
            self.setAlignment(QtCore.Qt.AlignCenter)
        else:
            pixmap = pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            mask = QtGui.QPixmap(size, size)
            mask.fill(QtCore.Qt.transparent)
            
            painter = QtGui.QPainter(mask)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setBrush(QtGui.QColor(0, 0, 0))
            painter.drawEllipse(0, 0, size, size)
            painter.end()
            
            pixmap.setMask(mask.mask())
            self.setPixmap(pixmap)

class EventDialog(QtWidgets.QDialog):
    def __init__(self, parent, date):
        super().__init__(parent)
        self.setWindowTitle(f"Add/View Events — {date}")
        self.date = date
        self.resize(450,400)
        
        v = QtWidgets.QVBoxLayout()
        
        title_lbl = QtWidgets.QLabel(f"Events on: **{date}**")
        title_lbl.setStyleSheet(f"font-size: 16px; color: {PRIMARY_COLOR}; font-weight: 700;")
        v.addWidget(title_lbl)
        
        self.listw = QtWidgets.QListWidget()
        self.listw.setStyleSheet(f"QListWidget {{ border: 1px solid {PRIMARY_COLOR}33; min-height: 150px; }}")
        v.addWidget(self.listw)
        
        add_h = QtWidgets.QHBoxLayout()
        self.time_in = QtWidgets.QTimeEdit()
        self.time_in.setDisplayFormat("HH:mm")
        self.time_in.setTime(QtCore.QTime.currentTime())
        
        self.title_in = QtWidgets.QLineEdit()
        self.title_in.setPlaceholderText("New event title...")
        self.title_in.setStyleSheet("QLineEdit { padding: 10px; }")
        
        add_btn = QtWidgets.QPushButton("Add Event")
        add_btn.setStyleSheet(f"QPushButton {{ padding: 5px 10px; border-radius: 12px; min-width: 60px; font-size: 12px; }}")
        add_btn.clicked.connect(self.add_event)
        
        add_h.addWidget(self.time_in)
        add_h.addWidget(self.title_in)
        add_h.addWidget(add_btn)
        v.addLayout(add_h)
        
        del_btn = QtWidgets.QPushButton("Delete Selected Event")
        del_btn.setStyleSheet(f"QPushButton {{ background-color: #f44336; border: none; }} QPushButton:hover {{ background-color: #d32f2f; }}")
        del_btn.clicked.connect(self.delete_selected)
        v.addWidget(del_btn)
        
        self.setLayout(v)
        self.load_events()

    def load_events(self):
        self.listw.clear()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT id, title, time FROM events WHERE date=? ORDER BY time, id", (self.date,))
        for row in c.fetchall():
            event_id = row[0]
            title = row[1]
            time = row[2] if row[2] else "N/A"
            display_text = f"[{time}] {title}"
            item = QtWidgets.QListWidgetItem(display_text)
            item.setData(QtCore.Qt.UserRole, event_id)
            self.listw.addItem(item)
        conn.close()

    def add_event(self):
        title = self.title_in.text().strip()
        time = self.time_in.time().toString("HH:mm")
        if not title:
            return
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO events (title, date, time) VALUES (?,?,?)", (title, self.date, time))
        conn.commit()
        conn.close()
        self.title_in.clear()
        self.load_events()
        self.parent().populate_calendar(self.parent().current_date.year, self.parent().current_date.month)


    def delete_selected(self):
        item = self.listw.currentItem()
        if not item:
            return
        ev_id = item.data(QtCore.Qt.UserRole)
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("DELETE FROM events WHERE id=?", (ev_id,))
        conn.commit()
        conn.close()
        self.load_events()
        self.parent().populate_calendar(self.parent().current_date.year, self.parent().current_date.month)


class StudyHistoryDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Study History 📚")
        self.resize(550, 450)
        self.setStyleSheet(f"QDialog {{ background-color: {BACKGROUND_LIGHT}; }}")
        
        v = QtWidgets.QVBoxLayout()
        
        self.total_lbl = QtWidgets.QLabel("Loading study totals...")
        self.total_lbl.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {PRIMARY_COLOR}; margin-bottom: 10px;")
        v.addWidget(self.total_lbl)
        
        self.listw = QtWidgets.QListWidget()
        v.addWidget(self.listw)
        
        self.setLayout(v)
        self.load_history()

    def load_history(self):
        self.listw.clear()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        c.execute("SELECT SUM(duration_seconds) FROM study_sessions")
        total_seconds = c.fetchone()[0] or 0
        total_duration = self.format_seconds(total_seconds)
        self.total_lbl.setText(f"Total Study Time: **{total_duration}**")
        
        c.execute("SELECT type, start_time, duration_seconds FROM study_sessions ORDER BY start_time DESC")
        
        for type, start_time, duration_seconds in c.fetchall():
            duration_str = self.format_seconds(duration_seconds)
            
            try:
                dt = datetime.datetime.fromisoformat(start_time)
                start_str = dt.strftime("%Y-%m-%d @ %I:%M %p")
            except ValueError:
                start_str = start_time
                
            item_text = f"[{type}] {start_str} | Duration: {duration_str}"
            self.listw.addItem(item_text)
            
        conn.close()

    def format_seconds(self, total_seconds):
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        
        return " ".join(parts)


class NotesDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Notes — Persistent Editor")
        self.resize(800, 600)
        self.setStyleSheet(f"QDialog {{ background-color: {BACKGROUND_LIGHT}; }}")
        
        self.start_time = datetime.datetime.now() 
        
        h = QtWidgets.QHBoxLayout()
        
        v_list = QtWidgets.QVBoxLayout()
        
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("🔎 Search notes...")
        self.search_input.textChanged.connect(self.filter_notes)
        v_list.addWidget(self.search_input)
        
        self.listw = QtWidgets.QListWidget()
        self.listw.setFixedWidth(240)
        self.listw.setStyleSheet(f"QListWidget {{ border: none; background-color: #f7f9fc; border-right: 1px solid #e0e0e0; border-radius: 0; }}")
        self.listw.itemClicked.connect(self.load_note)
        v_list.addWidget(self.listw)
        
        h.addLayout(v_list)
        
        v = QtWidgets.QVBoxLayout()
        self.current_fname = None
        
        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText("Note title...")
        self.title.setStyleSheet(f"QLineEdit {{ font-size: 18px; font-weight: 700; border: none; border-bottom: 2px solid {PRIMARY_COLOR}33; border-radius: 0; padding: 10px 0; }}")
        
        self.body = QtWidgets.QPlainTextEdit()
        self.body.setStyleSheet(f"QPlainTextEdit {{ border: none; font-family: 'Segoe UI', 'Arial'; font-size: 14px; }}")
        
        btn_h = QtWidgets.QHBoxLayout()
        new = QtWidgets.QPushButton("New")
        new.setStyleSheet(f"QPushButton {{ background-color: #5cb85c; border: none; }} QPushButton:hover {{ background-color: #4cae4c; }}")
        new.clicked.connect(self.new_note)
        
        save = QtWidgets.QPushButton("Save")
        save.setStyleSheet(f"QPushButton {{ background-color: {ACCENT_COLOR}; border: none; }}")
        save.clicked.connect(self.save_note)
        
        delete = QtWidgets.QPushButton("Delete")
        delete.setStyleSheet(f"QPushButton {{ background-color: #f0ad4e; border: none; }} QPushButton:hover {{ background-color: #ec971f; }}")
        delete.clicked.connect(self.delete_note)
        
        btn_h.addWidget(new)
        btn_h.addWidget(save)
        btn_h.addWidget(delete)
        
        v.addWidget(self.title)
        v.addWidget(self.body)
        v.addLayout(btn_h)
        
        h.addLayout(v)
        self.setLayout(h)
        
        self.all_notes = {}
        self.load_note_list()
        self.new_note()

    def load_note_list(self):
        self.listw.clear()
        self.all_notes = {}
        for fname in os.listdir(NOTES_DIR):
            if fname.endswith(".txt"):
                fpath = os.path.join(NOTES_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        title = lines[0].strip() if lines else fname
                        self.all_notes[title] = fpath
                except Exception as e:
                    print(f"Error loading note {fname}: {e}")
        self.filter_notes("") 

    def filter_notes(self, text):
        self.listw.clear()
        search_text = text.lower()
        for title in self.all_notes:
            if search_text in title.lower():
                self.listw.addItem(title)

    def new_note(self):
        self.current_fname = None
        self.title.clear()
        self.body.clear()
        self.title.setFocus()

    def load_note(self, item):
        title = item.text()
        fpath = self.all_notes.get(title)
        if fpath and os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                    parts = content.split('\n\n', 1)
                    self.title.setText(parts[0].strip())
                    self.body.setPlainText(parts[1].strip() if len(parts) > 1 else "")
                    self.current_fname = fpath
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Could not load note: {e}")

    def save_note(self):
        t = self.title.text().strip()
        b = self.body.toPlainText().strip()
        
        if not t and not b:
            QtWidgets.QMessageBox.warning(self, "Empty Note", "Title or body cannot be empty.")
            return

        if self.current_fname and os.path.exists(self.current_fname):
            fname_to_use = self.current_fname
        else:
            fname_to_use = os.path.join(NOTES_DIR, f"note_{int(datetime.datetime.now().timestamp())}.txt")
            
        try:
            with open(fname_to_use, "w", encoding="utf-8") as f:
                f.write(t + "\n\n" + b)
            self.current_fname = fname_to_use
            QtWidgets.QMessageBox.information(self, "Saved", f"Note saved.")
            self.load_note_list()
            items = self.listw.findItems(t, QtCore.Qt.MatchExactly)
            if items:
                self.listw.setCurrentItem(items[0])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Could not save note: {e}")
            
    def delete_note(self):
        if not self.current_fname or not os.path.exists(self.current_fname):
            QtWidgets.QMessageBox.warning(self, "Select Note", "No note selected to delete.")
            return

        reply = QtWidgets.QMessageBox.question(self, 'Confirm Delete',
            "Are you sure you want to delete this note?", 
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                os.remove(self.current_fname)
                self.new_note() 
                self.load_note_list()
                QtWidgets.QMessageBox.information(self, "Deleted", "Note successfully deleted.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Could not delete note: {e}")
                
    def closeEvent(self, event):
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        duration_seconds = int(duration.total_seconds())
        
        if duration_seconds > 5: 
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("INSERT INTO study_sessions (type, start_time, end_time, duration_seconds) VALUES (?,?,?,?)", 
                      ("Notes", self.start_time.isoformat(), end_time.isoformat(), duration_seconds))
            conn.commit()
            conn.close()
            
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            msg = f"Study time recorded: {minutes} minutes and {seconds} seconds spent viewing notes."
            self.parent().status.showMessage(msg, 5000)
            
        super().closeEvent(event)


class FlashcardViewerDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Flashcards Study Mode")
        self.resize(600, 450)
        self.setStyleSheet(f"QDialog {{ background-color: {BACKGROUND_LIGHT}; }}")
        self.cards = []
        self.current_card_index = -1
        self.is_front = True
        
        self.start_time = datetime.datetime.now() 
        
        v = QtWidgets.QVBoxLayout()
        
        card_container = QtWidgets.QWidget()
        card_container.setObjectName("FlashcardContainer")
        card_container.setStyleSheet(f"""
            #FlashcardContainer {{
                background-color: #f7f9fc; 
                border: 1px solid #e0e0e0;
                border-radius: 15px;
                padding: 10px;
            }}
        """)
        card_v = QtWidgets.QVBoxLayout(card_container)

        self.card_label = QtWidgets.QLabel("Click to flip")
        self.card_label.setAlignment(QtCore.Qt.AlignCenter)
        self.card_label.setWordWrap(True)
        self.card_label.setMinimumSize(450, 250)
        self.card_label.setStyleSheet(f"""
            QLabel {{
                background-color: {BACKGROUND_LIGHT};
                border: 4px solid {ACCENT_COLOR};
                border-radius: 12px;
                font-size: 20px;
                font-weight: 700;
                padding: 30px;
                color: {PRIMARY_COLOR};
                margin: 10px;
            }}
        """)
        
        self.card_label.installEventFilter(self)
        card_v.addWidget(self.card_label, alignment=QtCore.Qt.AlignCenter)
        
        nav_h = QtWidgets.QHBoxLayout()
        self.prev_btn = QtWidgets.QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.show_prev)
        self.info_lbl = QtWidgets.QLabel("0/0")
        self.info_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.info_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #555;")
        self.next_btn = QtWidgets.QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.show_next)
        
        nav_btn_style = "QPushButton { background: none; color: #555; border: 1px solid #ccc; border-radius: 15px; } QPushButton:hover { color: #333; background-color: #eee; }"
        self.prev_btn.setStyleSheet(nav_btn_style)
        self.next_btn.setStyleSheet(nav_btn_style)

        nav_h.addWidget(self.prev_btn)
        nav_h.addWidget(self.info_lbl)
        nav_h.addWidget(self.next_btn)
        
        v.addWidget(card_container, alignment=QtCore.Qt.AlignCenter)
        v.addLayout(nav_h)
        self.setLayout(v)
        
        self.load_cards()
        self.show_card(0)

    def load_cards(self):
        self.cards = []
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        today = datetime.date.today().isoformat()
        c.execute("SELECT title FROM events WHERE date=? ORDER BY id", (today,))
        for r in c.fetchall():
            if ' — ' in r[0]:
                front, back = r[0].split(' — ', 1)
                self.cards.append((front, back))
        conn.close()

    def show_card(self, index):
        if not self.cards:
            self.card_label.setText("No flashcards added for today. Go to 'Add Flashcard'!")
            self.info_lbl.setText("0/0")
            self.current_card_index = -1
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        if 0 <= index < len(self.cards):
            self.current_card_index = index
            self.is_front = True
            self.card_label.setText(self.cards[index][0]) 
            self.info_lbl.setText(f"{index + 1}/{len(self.cards)}")
            
            self.prev_btn.setEnabled(index > 0)
            self.next_btn.setEnabled(index < len(self.cards) - 1)
        else:
            self.current_card_index = -1

    def flip_card(self):
        if self.current_card_index != -1:
            card = self.cards[self.current_card_index]
            self.is_front = not self.is_front
            if self.is_front:
                self.card_label.setText(card[0])
            else:
                self.card_label.setText(card[1])

    def show_prev(self):
        if self.current_card_index > 0:
            self.show_card(self.current_card_index - 1)

    def show_next(self):
        if self.current_card_index < len(self.cards) - 1:
            self.show_card(self.current_card_index + 1)
            
    def eventFilter(self, source, event):
        if source == self.card_label and event.type() == QtCore.QEvent.MouseButtonPress:
            self.flip_card()
            return True
        return super().eventFilter(source, event)
        
    def closeEvent(self, event):
        end_time = datetime.datetime.now()
        duration = end_time - self.start_time
        duration_seconds = int(duration.total_seconds())

        if duration_seconds > 5: 
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("INSERT INTO study_sessions (type, start_time, end_time, duration_seconds) VALUES (?,?,?,?)", 
                      ("Flashcards", self.start_time.isoformat(), end_time.isoformat(), duration_seconds))
            conn.commit()
            conn.close()
            
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            msg = f"Study time recorded: {minutes} minutes and {seconds} seconds spent studying flashcards."
            self.parent().status.showMessage(msg, 5000)
            
        super().closeEvent(event)


class FlashcardsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Add Flashcards (Today)")
        self.resize(520,360)
        v = QtWidgets.QVBoxLayout()
        
        title_lbl = QtWidgets.QLabel("New Flashcard for Today")
        title_lbl.setStyleSheet(f"font-size: 16px; color: {PRIMARY_COLOR}; font-weight: 700; margin-bottom: 10px;")
        v.addWidget(title_lbl)
        
        self.front = QtWidgets.QLineEdit()
        self.front.setPlaceholderText("Front (Question)")
        self.back = QtWidgets.QLineEdit()
        self.back.setPlaceholderText("Back (Answer)")
        add = QtWidgets.QPushButton("➕ Add Card")
        add.clicked.connect(self.add_card)
        self.cards_list = QtWidgets.QListWidget()
        self.cards_list.setStyleSheet("min-height: 100px;")
        
        v.addWidget(self.front)
        v.addWidget(self.back)
        v.addWidget(add)
        v.addWidget(QtWidgets.QLabel("Cards Added Today:"))
        v.addWidget(self.cards_list)
        self.setLayout(v)
        self.load_cards()

    def add_card(self):
        f = self.front.text().strip()
        b = self.back.text().strip()
        if not f or not b:
            return
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO events (title,date) VALUES (?,?)", (f + " — " + b, datetime.date.today().isoformat()))
        conn.commit()
        conn.close()
        self.front.clear()
        self.back.clear()
        self.load_cards()

    def load_cards(self):
        self.cards_list.clear()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        today = datetime.date.today().isoformat()
        c.execute("SELECT id,title FROM events WHERE date=? ORDER BY id", (today,))
        for r in c.fetchall():
            self.cards_list.addItem(r[1])
        conn.close()


class NotificationsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Notifications — Upcoming Deadlines")
        self.resize(450,350)
        v = QtWidgets.QVBoxLayout()
        
        title_lbl = QtWidgets.QLabel("Events Today & Tomorrow")
        title_lbl.setStyleSheet(f"font-size: 16px; color: {PRIMARY_COLOR}; font-weight: 700; margin-bottom: 10px;")
        v.addWidget(title_lbl)
        
        self.listw = QtWidgets.QListWidget()
        v.addWidget(self.listw)
        self.setLayout(v)
        self.load_notifications()

    def load_notifications(self):
        self.listw.clear()
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        
        c.execute("SELECT title, date, time FROM events WHERE date BETWEEN ? AND ? AND title NOT LIKE '% — %' ORDER BY date, time", (today.isoformat(), tomorrow.isoformat()))
        
        for r in c.fetchall():
            title = r[0]
            date_str = "Today" if r[1] == today.isoformat() else "Tomorrow"
            time_str = r[2] if r[2] else "N/A"
            self.listw.addItem(f"[{date_str} @ {time_str}] {title}")
        
        conn.close()
        
        if self.listw.count() == 0:
            self.listw.addItem("No upcoming events found for today or tomorrow.")


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("EduQuest Login")
        self.resize(350,220)
        
        v = QtWidgets.QVBoxLayout()
        
        title_lbl = QtWidgets.QLabel("EduQuest")
        title_lbl.setStyleSheet(f"font-weight: 900; font-size: 30px; color: {PRIMARY_COLOR}; margin-bottom: 15px;")
        title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(title_lbl)
        
        self.user = QtWidgets.QLineEdit()
        self.user.setPlaceholderText("Username")
        self.passw = QtWidgets.QLineEdit()
        self.passw.setPlaceholderText("Password")
        self.passw.setEchoMode(QtWidgets.QLineEdit.Password)
        
        btn = QtWidgets.QPushButton("Log In")
        btn.clicked.connect(self.try_login)
        
        v.addWidget(self.user)
        v.addWidget(self.passw)
        v.addWidget(btn)
        self.setLayout(v)
        
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def try_login(self):
        if self.user.text() == "demo" and self.passw.text() == "eduquest":
            QtWidgets.QMessageBox.information(self, "Welcome", "Logged in as demo")
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(self, "Denied", "Wrong credentials")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_logged_in = False
        self.setWindowTitle("EduQuest — Desktop")
        self.resize(1200,800)
        
        init_db()
        self.setStyleSheet(GLOBAL_STYLE) 
        
        self.current_date = datetime.date.today()
        self.setup_ui()
        self.show_login_screen()

    def setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout()
        
        self.header = QtWidgets.QHBoxLayout()
        logo_path = os.path.join(os.getcwd(), "eduquest_logo.png")
        self.logo_lbl = RoundLogo(logo_path, size=64)
        self.logo_lbl.setStyleSheet(f"border: 2px solid {ACCENT_COLOR}; border-radius: 32px;")
        self.header.addWidget(self.logo_lbl)
        self.header.addStretch()
        
        self.nav_buttons = {}
        btn_data = [
            ("Calendar", self.show_calendar), 
            ("Add Flashcard", self.open_flashcard_adder),
            ("Study Flashcards", self.open_flashcard_viewer),
            ("Notes", self.open_notes), 
            ("Study History", self.open_study_history), 
            ("Notifications", self.open_notifications),
        ]
        
        for name, slot in btn_data:
            b = QtWidgets.QPushButton(name)
            b.clicked.connect(slot)
            b.setCursor(QtCore.Qt.PointingHandCursor)
            self.header.addWidget(b)
            self.nav_buttons[name] = b
            
        self.login_btn = QtWidgets.QPushButton("Login")
        self.login_btn.clicked.connect(self.handle_login_logout)
        self.header.addWidget(self.login_btn)
        
        main_layout.addLayout(self.header)
        
        cal_title_h = QtWidgets.QHBoxLayout()
        self.month_year_lbl = QtWidgets.QLabel("Calendar")
        self.month_year_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: white; margin: 15px 0;")
        
        prev_btn = QtWidgets.QPushButton("◀")
        next_btn = QtWidgets.QPushButton("▶")
        
        nav_btn_style = f"QPushButton {{ background-color: {ACCENT_COLOR}; color: white; border-radius: 15px; padding: 6px 10px; font-weight: 700; min-width: 30px; }}"
        prev_btn.setStyleSheet(nav_btn_style)
        next_btn.setStyleSheet(nav_btn_style)
        
        prev_btn.clicked.connect(lambda: self.change_month(-1))
        next_btn.clicked.connect(lambda: self.change_month(1))
        
        cal_title_h.addWidget(prev_btn)
        cal_title_h.addWidget(self.month_year_lbl, alignment=QtCore.Qt.AlignCenter)
        cal_title_h.addWidget(next_btn)
        
        main_layout.addLayout(cal_title_h)
        
        self.cal_table = QtWidgets.QTableWidget(6,7)
        self.cal_table.verticalHeader().setVisible(False)
        self.cal_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cal_table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.cal_table.cellDoubleClicked.connect(self.cell_double)
        
        main_layout.addWidget(self.cal_table, 8)
        central.setLayout(main_layout)
        
        self.status = QtWidgets.QStatusBar()
        self.status.setStyleSheet("color: white;")
        self.setStatusBar(self.status)
        
        self.populate_calendar(self.current_date.year, self.current_date.month)
        self.update_ui_state()

    def handle_login_logout(self):
        if self.is_logged_in:
            self.logout()
        else:
            self.open_login()

    def update_ui_state(self):
        if self.is_logged_in:
            self.login_btn.setText("Logout")
            self.setWindowTitle("EduQuest — Desktop (Logged In)")
        else:
            self.login_btn.setText("Login")
            self.setWindowTitle("EduQuest — Desktop (Logged Out)")
            
        for btn in self.nav_buttons.values():
            btn.setVisible(self.is_logged_in)
            
        self.cal_table.setEnabled(self.is_logged_in)
        self.populate_calendar(self.current_date.year, self.current_date.month)
        

    def show_login_screen(self):
        dlg = LoginDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.is_logged_in = True
            self.update_ui_state()

    def logout(self):
        self.is_logged_in = False
        self.update_ui_state()
        QtWidgets.QMessageBox.information(self, "Logout", "You have been logged out.")

    def change_month(self, delta):
        new_date = self.current_date + datetime.timedelta(days=32 * delta)
        self.current_date = datetime.date(new_date.year, new_date.month, 1)
        self.populate_calendar(self.current_date.year, self.current_date.month)


    def populate_calendar(self, year, month):
        self.cal_table.clearContents()
        
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for c, name in enumerate(day_names):
            header_item = QtWidgets.QTableWidgetItem(name)
            header_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.cal_table.setHorizontalHeaderItem(c, header_item)

        for r in range(6):
            self.cal_table.setRowHeight(r, int(self.height() * 0.12))
        for c in range(7):
            self.cal_table.setColumnWidth(c, int(self.width() / 7) - 12)
            
        cal = calendar.Calendar(firstweekday=6) 
        month_days = cal.monthdatescalendar(year, month)
        
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                cell_widget = QtWidgets.QWidget()
                layout = QtWidgets.QVBoxLayout()
                layout.setContentsMargins(6,6,6,6)
                
                date_lbl = QtWidgets.QLabel(str(day.day))
                date_lbl_style = "font-weight:700; font-size: 16px; color: white;"
                
                if day == datetime.date.today():
                    date_lbl_style = f"font-weight:900; font-size: 18px; color:{PRIMARY_COLOR}; background-color:white; border-radius:8px; padding:4px 8px;"
                
                date_lbl.setStyleSheet(date_lbl_style)
                layout.addWidget(date_lbl, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
                
                ev_box = QtWidgets.QVBoxLayout()
                cur.execute("SELECT title, time FROM events WHERE date=? AND title NOT LIKE '% — %' ORDER BY time", (day.isoformat(),))
                evs = cur.fetchall()
                
                for ev in evs:
                    title = ev[0]
                    time = ev[1] if ev[1] else ""
                    display_text = f"{time} {title}" if time else title
                    
                    ev_lbl = QtWidgets.QLabel(display_text)
                    ev_lbl.setStyleSheet(EVENT_LABEL_STYLE)
                    ev_lbl.setWordWrap(True)
                    ev_box.addWidget(ev_lbl)
                    
                layout.addLayout(ev_box)
                layout.addStretch()
                cell_widget.setLayout(layout)
                self.cal_table.setCellWidget(r, c, cell_widget)
                
                if day.month != month:
                    cell_widget.setStyleSheet(f"QWidget {{ background-color: {CARD_BACKGROUND}cc; border-radius: 8px; margin: 4px; }}")
                    cell_widget.setDisabled(True)
                else:
                    cell_widget.setStyleSheet(f"QWidget {{ background-color: {CARD_BACKGROUND}; border-radius: 8px; margin: 4px; }}")
                    
        conn.close()
        self.month_year_lbl.setText(f"{calendar.month_name[month]} {year}")
        self.status.showMessage("Calendar loaded successfully.")

    def cell_double(self, row, col):
        if not self.is_logged_in:
            return
            
        cal = calendar.Calendar(firstweekday=6)
        month_days = cal.monthdatescalendar(self.current_date.year, self.current_date.month)
        try:
            day = month_days[row][col]
        except Exception:
            return
            
        if day.month != self.current_date.month:
            return
            
        dlg = EventDialog(self, day.isoformat())
        dlg.exec_()
        self.populate_calendar(self.current_date.year, self.current_date.month)

    def show_calendar(self):
        if self.is_logged_in:
            self.populate_calendar(self.current_date.year, self.current_date.month)

    def open_notes(self):
        if self.is_logged_in:
            dlg = NotesDialog(self)
            dlg.exec_()

    def open_flashcard_viewer(self):
        if self.is_logged_in:
            dlg = FlashcardViewerDialog(self)
            dlg.exec_()
            
    def open_flashcard_adder(self):
        if self.is_logged_in:
            dlg = FlashcardsDialog(self)
            dlg.exec_()

    def open_notifications(self):
        if self.is_logged_in:
            dlg = NotificationsDialog(self)
            dlg.exec_()

    def open_study_history(self):
        if self.is_logged_in:
            dlg = StudyHistoryDialog(self)
            dlg.exec_()

    def open_login(self):
        dlg = LoginDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.is_logged_in = True
            self.update_ui_state()

if __name__ == '__main__':
    init_db() 
    
    app = QtWidgets.QApplication(sys.argv)
    
    logo_path = os.path.join(os.getcwd(), "eduquest_logo.png")
    if not os.path.exists(logo_path):
        dummy_pixmap = QtGui.QPixmap(64, 64)
        dummy_pixmap.fill(QtGui.QColor(ACCENT_COLOR))
        dummy_painter = QtGui.QPainter(dummy_pixmap)
        dummy_painter.setFont(QtGui.QFont("Arial", 24, QtGui.QFont.Bold))
        dummy_painter.setPen(QtCore.Qt.white)
        dummy_painter.drawText(dummy_pixmap.rect(), QtCore.Qt.AlignCenter, "EQ")
        dummy_painter.end()
        dummy_pixmap.save(logo_path, "PNG")

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())