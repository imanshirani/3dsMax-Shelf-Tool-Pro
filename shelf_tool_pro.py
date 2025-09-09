# ==========================
# IMAN SHIRANI
# 2025 V0.2
# ==========================
import sys
import os
import json
import ast
import pymxs
import configparser
import webbrowser
import platform

# ==========================
# Check 3ds Max Version
# ==========================
def check_max_version():
    rt = pymxs.runtime
    py_major = sys.version_info.major
    py_minor = sys.version_info.minor
    print(f"[INFO] Detected Python Version: {py_major}.{py_minor}")

    if (py_major, py_minor) < (3, 11):
        rt.messageBox("? This tool requires 3ds Max 2025 or newer!\n\n(Python 3.11 and Qt6 / PySide6 are required)",
                      title="Shelf Tool - Incompatible Version")
        sys.exit()


# ==========================
# From import
# ==========================
def safe_import_pyside6():
    global QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea
    global QTabWidget, QLineEdit, QLabel, QDialog, QToolButton, QMenu, QListWidget
    global QComboBox, QSizePolicy, QDockWidget, QFileDialog, QInputDialog, QTextEdit
    global QIcon, QCursor, QPixmap, QAction, QShortcut, QKeySequence
    global Qt, QSize

    from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
                                   QTabWidget, QLineEdit, QLabel, QDialog, QToolButton, QMenu, QListWidget,
                                   QComboBox, QSizePolicy, QDockWidget, QFileDialog, QInputDialog, QTextEdit )
    from PySide6.QtGui import QIcon, QCursor, QPixmap, QAction, QShortcut, QKeySequence
    from PySide6.QtCore import Qt, QSize

# ==========================
# EXECUTION FLOW
# ==========================

check_max_version()
safe_import_pyside6()


# ==========================
# Helper to run max command (With Debug)
# ==========================
def run_max_command(command):
    rt = pymxs.runtime
    if isinstance(command, str):
        command = command.strip()
        print(f"[RUNNING COMMAND] {command}")
        try:
            rt.execute(command)
        except Exception as e:
            print(f"[ERROR running command]: {e}")
# Helper to trigger actionMan actions by ID
def trigger_action(action_id, context_id=0):
    rt = pymxs.runtime
    try:
        print(f"[TRIGGERING ACTION ID] {action_id}")
        rt.actionMan.executeAction(context_id, str(action_id))
    except Exception as e:
        print(f"[ERROR triggering action]: {e}")



# ==========================
# Find Action Data
# ==========================
def _find_action_data(self, action_name):
    for group in self.action_list:
        if 'Actions' in group:
            for action in group['Actions']:
                if action.get('Desc') == action_name:
                    # Make sure 'title' exists
                    if 'title' not in action or not action['title']:
                        action['title'] = action.get('Desc', 'Unknown Action')

                    # Make sure 'command' exists
                    if 'command' not in action:
                        if 'ID' in action:
                            action["command"] = 'actionMan.executeAction 0 "{}"'.format(action["ID"])
                        else:
                            action['command'] = ''  # fallback empty if no ID

                    return action
    return None
    
# ==========================
# Additional: Run Script from Editor
# ==========================
def run_script_from_editor(text_edit_widget):
    code = text_edit_widget.toPlainText()
    if code.strip():
        try:
            pymxs.runtime.execute(code)
            print("[SUCCESS] Script executed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to execute script: {e}")
# ==========================
# Run Script button
# ==========================            
def add_run_script_button(layout, command_edit):
    run_script_button = QPushButton("Run Script")
    run_script_button.clicked.connect(lambda: run_script_from_editor(command_edit))
    layout.addWidget(run_script_button)
    
# ==========================
# Main Shelf Tool
# ==========================
class ShelfTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3ds Max Shelf Tool")

        
        # Load settings
        default_folder = os.path.join(os.path.expanduser("~"), "Documents", "3dsMaxShelves")
        self.settings_path = os.path.join(default_folder, "settings.ini")
        self.shelves_save_path = os.path.join(default_folder, "shelves.json") 
        self.icon_size = 32
        self.button_base_width = 80
        self.button_spacing = 5
        self.load_settings_from_ini()

        self.layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.hidden_tabs = {}
        self.tab_toolbars = {}
        self.action_list = []

        

        self._load_actions()
        self._add_tab_manager_buttons()

        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)

        if os.path.exists(self.shelves_save_path):
            self.load_shelves_from_file(self.shelves_save_path)
        else:
            self.save_shelves_to_file(self.shelves_save_path)
            
    





    # ==========================
    # Load settings from INI
    # ==========================
    def load_settings_from_ini(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.settings_path):
            config.read(self.settings_path)
            if "Settings" in config:
                settings = config["Settings"]
                self.shelves_save_path = settings.get("save_path", self.shelves_save_path)
                self.icon_size = int(settings.get("icon_size", self.icon_size))
                self.button_base_width = int(settings.get("button_base_width", self.button_base_width))
                self.button_spacing = int(settings.get("button_spacing", self.button_spacing))

    # ==========================
    # Save settings to INI
    # ==========================
    def save_settings_to_ini(self):
        config = configparser.ConfigParser()
        config["Settings"] = {
            "save_path": self.shelves_save_path,
            "icon_size": str(self.icon_size),
            "button_base_width": str(self.button_base_width),
            "button_spacing": str(self.button_spacing)
        }
        os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
        with open(self.settings_path, "w", encoding="utf-8") as configfile:
            config.write(configfile)

    # ==========================
    # Show Tab Contex
    # ==========================
    def _show_tab_context_menu(self, pos):
            tab_bar = self.tab_widget.tabBar()
            index = tab_bar.tabAt(pos)
            if index != -1:
                menu = QMenu(self)
                rename_action = QAction("Rename Tab", self)
                rename_action.triggered.connect(lambda: self._rename_tab(index))
                menu.addAction(rename_action)
                menu.exec(tab_bar.mapToGlobal(pos))
                
    # ==========================
    # Delete Icon
    # ==========================                
    def _delete_action(self, button, tab_name):
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "Delete Tool", "Are you sure you want to delete this tool?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                layout = self.tab_toolbars.get(tab_name)
                if layout:
                    layout.removeWidget(button)
                    button.deleteLater()
                    self.save_shelves_to_file(self.shelves_save_path)

    # ==========================
    # Load Action
    # ==========================  
    def _load_actions(self):
        try:
            with open('max_actions.json', 'r', encoding='utf-8') as f:
                self.action_list = json.load(f)
                #print(f"[DEBUG] Loaded {len(self.action_list)} actions from max_actions.json")
        except Exception as e:
            print(f"Error loading actions: {e}")

    # ==========================
    # Add New Tab
    # ========================== 
    def add_tab(self, tab_name, actions_data=None):
        new_tab = QWidget()
        new_tab_layout = QVBoxLayout(new_tab)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        #scroll_area.setFixedHeight(100)
        dock.setMinimumHeight(200)
        dock.setMaximumHeight(200)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(5)

        scroll_area.setWidget(scroll_widget)
        new_tab_layout.addWidget(scroll_area)

        self.tab_toolbars[tab_name] = scroll_layout

        button_layout = QHBoxLayout()

        add_tool_button = QPushButton("Add Tool", self)
        add_tool_button.clicked.connect(lambda: self._open_add_tool_dialog(tab_name))
        button_layout.addWidget(add_tool_button)

        create_custom_tool_button = QPushButton("Create Custom Tool", self)
        create_custom_tool_button.clicked.connect(lambda: self._open_create_custom_tool_dialog(tab_name))
        button_layout.addWidget(create_custom_tool_button)

        new_tab_layout.addLayout(button_layout)

        self.tab_widget.addTab(new_tab, tab_name)

        if actions_data:
            for action_data in actions_data:
                self._add_action_to_toolbar(tab_name, action_data)

        self.save_shelves_to_file(self.shelves_save_path)

    # ==========================
    # Rename Tab
    # ==========================
    def _rename_tab(self, index):
        old_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Tab", "Enter new tab name:", text=old_name)
        if ok and new_name:
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            self.tab_toolbars[new_name] = self.tab_toolbars.pop(old_name)
            self.tab_widget.insertTab(index, widget, new_name)
            self.save_shelves_to_file(self.shelves_save_path)

    def _add_action_to_toolbar(self, tab_name, action_data):
        layout = self.tab_toolbars.get(tab_name)
        if layout is None:
            return

        button = QToolButton()
        button.setText(action_data.get("title", "Unknown"))
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setIconSize(QSize(self.icon_size, self.icon_size))

        if icon_path := action_data.get("icon"):
            button.setIcon(QIcon(icon_path))

        button.setProperty("action_data", action_data)        

        def on_button_clicked():
            action_data = button.property("action_data")
            command = action_data.get("command", "").strip()
            action_id = action_data.get("ID", None)

            if command:
                print(f"[RUNNING COMMAND] {command}")
                run_max_command(command)
            elif action_id:
                print(f"[TRIGGERING ACTION ID] {action_id}")
                trigger_action(action_id)
            else:
                print("[WARNING] No command or action defined!")


        button.clicked.connect(on_button_clicked)

        # Add shortcut binding if exists
        shortcut = action_data.get("shortcut", "").strip()
        if shortcut:
            qshortcut = QShortcut(QKeySequence(shortcut), button)
            qshortcut.activated.connect(on_button_clicked)

        layout.addWidget(button)

        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda pos, b=button: self._show_action_context_menu(b, tab_name))

    def _show_action_context_menu(self, button, tab_name):
        menu = QMenu()
        edit_action = menu.addAction("Edit Action")
        delete_action = menu.addAction("Delete Tool")

        edit_action.triggered.connect(lambda: self._edit_action(button, tab_name))
        delete_action.triggered.connect(lambda: self._delete_action(button, tab_name))

        menu.exec(QCursor.pos())


    # ==========================
    # Edit Action Tool DIALOG
    # ========================== 
    def _edit_action(self, button, tab_name):
        action_data = button.property("action_data")

        dialog = QDialog(self)
        dialog.resize(500, 300)
        layout = QVBoxLayout(dialog)

        # ??????
        title_edit = QLineEdit(action_data.get("title", ""))
        command_edit = QTextEdit()
        command_edit.setPlainText(action_data.get("command", ""))
        command_edit.setMinimumHeight(100)
        shortcut_edit = QLineEdit(action_data.get("shortcut", ""))
        icon_edit = QLineEdit(action_data.get("icon", ""))
        icon_preview = QLabel()
        icon_preview.setFixedSize(100, 100)

        # ??? ????? ????
        if icon_edit.text():
            pixmap = QPixmap(icon_edit.text())
            if not pixmap.isNull():
                icon_preview.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

        browse_button = QPushButton("Browse Icon")
        browse_button.clicked.connect(lambda: self._browse_icon(icon_edit, icon_preview))

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self._update_action_data_full(button,
                                                                           title_edit.text(),
                                                                           icon_edit.text(),
                                                                           command_edit.toPlainText(),
                                                                           shortcut_edit.text(),
                                                                           dialog))

        # ????? ????? ????
        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_edit)

        layout.addWidget(QLabel("Command (3dsMax Script or Action):"))
        layout.addWidget(command_edit)
        add_run_script_button(layout, command_edit)
        layout.addWidget(QLabel("Shortcut (optional):"))
        layout.addWidget(shortcut_edit)

        layout.addWidget(QLabel("Icon Path:"))
        layout.addWidget(icon_edit)
        layout.addWidget(browse_button)
        layout.addWidget(icon_preview)

        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec()

    def _update_action_data_full(self, button, new_title, new_icon_path, new_command, new_shortcut, dialog):
        action_data = button.property("action_data")
        action_data.update({
            "title": new_title,
            "icon": new_icon_path,
            "command": new_command,
            "shortcut": new_shortcut
        })
        button.setText(new_title)
        button.setIcon(QIcon(new_icon_path))
        button.setProperty("action_data", action_data)
        self.save_shelves_to_file(self.shelves_save_path)
        dialog.accept()

    def _browse_icon(self, line_edit, preview_label):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            line_edit.setText(path)
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                preview_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))

    def _open_add_tool_dialog(self, tab_name):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)

        category_combo = QComboBox()
        search_edit = QLineEdit()
        action_listbox = QListWidget()

        category_combo.addItem("All Categories")
        categories = [group['GroupName'] for group in self.action_list if 'GroupName' in group]
        category_combo.addItems(sorted(categories))

        # ???? ???????
        self._all_actions = []
        for group in self.action_list:
            for action in group.get('Actions', []):
                action['_GroupName'] = group['GroupName']  # ????? ???? ??? ???? ?? ????
                self._all_actions.append(action)

        self._populate_actions(action_listbox, category_combo)

        category_combo.currentIndexChanged.connect(lambda: self._populate_actions(action_listbox, category_combo, search_edit))
        search_edit.textChanged.connect(lambda: self._populate_actions(action_listbox, category_combo, search_edit))

        add_button = QPushButton("Add Selected Tool")
        add_button.clicked.connect(lambda: self._add_action_to_toolbar_from_list(tab_name, action_listbox.currentItem()) or dialog.accept())

        for w in [category_combo, search_edit, action_listbox, add_button]:
            layout.addWidget(w)

        dialog.exec()

    # ==========================
    # Populate Actions to Listbox
    # ==========================
    def _populate_actions(self, listbox, combo, search_edit=None):
        selected_cat = combo.currentText()
        search_text = search_edit.text().lower() if search_edit else ""
        
        listbox.clear()
        for action in self._all_actions:
            if (selected_cat == "All Categories" or action.get('_GroupName') == selected_cat):
                if not search_text or search_text in action.get('title', '').lower():
                    listbox.addItem(action.get('title', 'Unknown'))

    # ==========================
    # Filter Actions
    # ==========================
    def _filter_actions(self, listbox, search_edit):
        text = search_edit.text().lower()
        listbox.clear()
        for action in self.action_list:
            if text in action.get("title", "").lower():
                listbox.addItem(action.get("title", "Unknown"))

    def _add_action_to_toolbar_from_list(self, tab_name, list_item):
        if not list_item:
            return
        action_data = self._find_action_data(list_item.text())
        if action_data:
            self._add_action_to_toolbar(tab_name, action_data)

    # ==========================
    # Find Action Data by Title
    # ==========================
    def _find_action_data(self, desc):
        for action in self._all_actions:
            if action.get("title", "") == desc:
                return {
                    "title": action.get("title", "Unknown Action"),
                    "icon": action.get("icon", ""),
                    "command": action.get("command", ""),
                    "shortcut": action.get("shortcut", ""),
                    "Cat": action.get("Cat", ""),
                }
        return None

    # ==========================
    # Create Custom Tool DIALOG
    # ========================== 
    def _open_create_custom_tool_dialog(self, tab_name):
        dialog = QDialog(self)
        dialog.resize(500, 300)
        layout = QVBoxLayout(dialog)

        title_edit = QLineEdit()
        command_edit = QTextEdit()
        command_edit.setMinimumHeight(100)
        command_edit.setPlaceholderText("-- Enter your 3dsMax script here --")
        shortcut_edit = QLineEdit()
        icon_edit = QLineEdit()
        icon_preview = QLabel()
        icon_preview.setFixedSize(100, 100)

        browse_button = QPushButton("Browse Icon")
        browse_button.clicked.connect(lambda: self._browse_icon(icon_edit, icon_preview))

        save_button = QPushButton("Create Tool")

        def save_custom_tool():
            action_data = {
                "title": title_edit.text(),
                "command": command_edit.toPlainText(),
                "shortcut": shortcut_edit.text(),
                "icon": icon_edit.text()
            }
            self._add_action_to_toolbar(tab_name, action_data)
            self.save_shelves_to_file(self.shelves_save_path)
            dialog.accept()

        save_button.clicked.connect(save_custom_tool)

        layout.addWidget(QLabel("Title:"))
        layout.addWidget(title_edit)
        layout.addWidget(QLabel("Command (3dsMax Command or Script):"))        
        layout.addWidget(command_edit)
        add_run_script_button(layout, command_edit)
        layout.addWidget(QLabel("Shortcut Key (Optional):"))
        layout.addWidget(shortcut_edit)
        layout.addWidget(QLabel("Icon Path:"))
        layout.addWidget(icon_edit)
        layout.addWidget(browse_button)
        layout.addWidget(icon_preview)
        layout.addWidget(save_button)

        dialog.setLayout(layout)
        dialog.exec()


    def _add_tab_manager_buttons(self):
        layout = QHBoxLayout()
        for text, method in [("Add Tab", self._open_add_tab_dialog), ("Remove Tab", self._remove_current_tab),
                              ("Hide Tab", self._hide_current_tab), ("Unhide Tab", self._unhide_tab_dialog),
                              ("Settings", self.open_settings_dialog)]:
            btn = QPushButton(text)
            btn.clicked.connect(method)
            layout.addWidget(btn)
        self.layout.addLayout(layout)

    def _open_add_tab_dialog(self):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        text_edit = QLineEdit()
        add_button = QPushButton("Add")
        add_button.clicked.connect(lambda: self.add_tab(text_edit.text()) or dialog.accept())
        layout.addWidget(text_edit)
        layout.addWidget(add_button)
        dialog.exec()

    def _remove_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index != -1:
            tab_name = self.tab_widget.tabText(index)
            self.tab_widget.removeTab(index)
            self.tab_toolbars.pop(tab_name, None)
            self.save_shelves_to_file(self.shelves_save_path)

    def _hide_current_tab(self):
        index = self.tab_widget.currentIndex()
        if index != -1:
            name = self.tab_widget.tabText(index)
            widget = self.tab_widget.widget(index)
            self.tab_widget.removeTab(index)
            self.hidden_tabs[name] = widget

    def _unhide_tab_dialog(self):
        if not self.hidden_tabs:
            return
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        listbox = QListWidget()
        listbox.addItems(self.hidden_tabs.keys())
        unhide_button = QPushButton("Unhide")
        unhide_button.clicked.connect(lambda: self._unhide_selected_tab(listbox.currentItem()) or dialog.accept())
        layout.addWidget(listbox)
        layout.addWidget(unhide_button)
        dialog.exec()

    def _unhide_selected_tab(self, item):
        if item:
            name = item.text()
            widget = self.hidden_tabs.pop(name)
            self.tab_widget.addTab(widget, name)

    # ==========================
    # Open Settings Dialog 
    # ==========================
    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.resize(500, 300)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)

        # Icon Size
        icon_size_edit = QLineEdit(str(self.icon_size))
        layout.addWidget(QLabel("Icon Size:"))
        layout.addWidget(icon_size_edit)

        # Button Base Width
        base_width_edit = QLineEdit(str(self.button_base_width))
        layout.addWidget(QLabel("Button Base Width:"))
        layout.addWidget(base_width_edit)

        # Button Spacing
        button_spacing_edit = QLineEdit(str(self.button_spacing))
        layout.addWidget(QLabel("Button Spacing:"))
        layout.addWidget(button_spacing_edit)

        # Shelves Save Path
        path_edit = QLineEdit(self.shelves_save_path)
        browse_button = QPushButton("Browse Save Path...")
        browse_button.clicked.connect(lambda: self._browse_save_path(path_edit))
        layout.addWidget(QLabel("Shelves Save Path:"))
        layout.addWidget(path_edit)
        layout.addWidget(browse_button)

        # INI Save Path
        settings_path_edit = QLineEdit(self.settings_path)
        browse_ini_button = QPushButton("Browse INI Path...")
        browse_ini_button.clicked.connect(lambda: self._browse_ini_path(settings_path_edit))
        layout.addWidget(QLabel("Settings INI Path:"))
        layout.addWidget(settings_path_edit)
        layout.addWidget(browse_ini_button)
        

        # Save Button
        save_button = QPushButton("Save Settings")
        
        def save_all_settings():
            self.icon_size = int(icon_size_edit.text())
            self.button_base_width = int(base_width_edit.text())
            self.button_spacing = int(button_spacing_edit.text())
            self.shelves_save_path = path_edit.text()
            self.save_settings_to_ini()
            self.save_shelves_to_file(self.shelves_save_path)
            self.settings_path = settings_path_edit.text()
            self.save_settings_to_ini()
            dialog.accept()

        save_button.clicked.connect(save_all_settings)
        layout.addWidget(save_button)

        
        

        # ==========================
        # About Section
        # ==========================
        about_label = QLabel("3ds Max Shelf Tool\n\nPlugin page: https://github.com/imanshirani/3dsMax-Shelf-Tool-Pro\n\nBy Iman Shirani")
        about_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_label)

        donate_button = QPushButton("Donate ??")
        donate_button.clicked.connect(lambda: self.open_url("https://www.paypal.com/donate/?hosted_button_id=LAMNRY6DDWDC4"))
        layout.addWidget(donate_button)

        dialog.setLayout(layout)
        dialog.exec()

    # ==========================
    # Save Settings
    # ==========================
    def _save_settings(self, path_edit, dialog):
        self.shelves_save_path = path_edit.text()
        self._save_settings_to_ini()   # Save ini
        self.save_shelves_to_file(self.shelves_save_path)   # Save shelves
        dialog.accept()

    def _browse_save_path(self, path_edit):
        initial_dir = os.path.dirname(self.settings_path)
        path, _ = QFileDialog.getSaveFileName(self, "Select Save File", initial_dir, "JSON Files (*.json)")
        if path:
            path_edit.setText(path)

    
    def open_url(self, url):    
        webbrowser.open(url)

    def _browse_ini_path(self, line_edit):
        initial_dir = os.path.dirname(self.settings_path)
        path, _ = QFileDialog.getSaveFileName(self, "Select INI File", initial_dir, "INI Files (*.ini)")
        if path:
            line_edit.setText(path)


    # ==========================
    # Save Shelves To File
    # ==========================
    def save_shelves_to_file(self, filepath):
        data = {"tabs": []}
        for i in range(self.tab_widget.count()):
            tab_name = self.tab_widget.tabText(i)
            actions = []
            layout = self.tab_toolbars.get(tab_name)
            if layout:
                for j in range(layout.count()):
                    button = layout.itemAt(j).widget()
                    if isinstance(button, QToolButton):
                        action_data = button.property("action_data")
                        actions.append({
                            "title": action_data.get("title", ""),
                            "icon": action_data.get("icon", ""),
                            "command": action_data.get("command", ""),
                            "shortcut": action_data.get("shortcut", ""),
                            "ID": action_data.get("ID", None)
                        })
            data["tabs"].append({"name": tab_name, "actions": actions})

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Shelves saved successfully to {filepath}")


    def load_shelves_from_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            for tab in data.get("tabs", []):
                self.add_tab(tab["name"], tab.get("actions", []))
            print(f"Shelves loaded from {filepath}")
        except Exception as e:
            print(f"Error loading shelves: {e}")



# ==========================
# Run inside 3ds Max
# ==========================
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

main_window = next(w for w in app.topLevelWidgets() if isinstance(w, QMainWindow))

dock = QDockWidget("3ds Max Shelf Tool")
shelf_tool = ShelfTool()
dock.setWidget(shelf_tool)
main_window.addDockWidget(Qt.LeftDockWidgetArea, dock)

dock.show()

if not app.exec():
    sys.exit()

