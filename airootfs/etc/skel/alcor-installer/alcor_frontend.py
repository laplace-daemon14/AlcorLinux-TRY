import sys
import os
import re
import shlex
import subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QRadioButton, QCheckBox, QLabel, QScrollArea, 
                             QGroupBox, QPushButton, QStackedWidget, QGridLayout,
                             QMessageBox, QComboBox,
                             QLineEdit, QProgressDialog, QSizePolicy, QFrame,
                             QToolButton)
from PyQt6.QtCore import (
    Qt, QSize, QTimer, QSignalBlocker
)
from PyQt6.QtGui import QPixmap, QIcon

class AlcorFrontend(QWidget):
    def __init__(self):
        super().__init__()
        
        self.pentest_boxes = {}
        self.daily_boxes = {}
        self.expert_boxes = {}
        self.expert_package_groups = {}
        self.expert_package_widgets = []
        self.expert_package_widget_boxes = {}
        self.built_expert_package_profiles = set()
        self.expert_controls = {}
        self.tool_entries = []
        self.tool_groups = set()
        self.category_expanded = {}
        self.category_toggle_buttons = {}
        self.category_grids = {}
        
        self.logo_dir = os.path.dirname(os.path.abspath(__file__))
        default_selection_file = f"/tmp/alcor_selection_{os.getuid()}.txt"
        self.selection_file = os.environ.get("ALCOR_SELECTION_FILE", default_selection_file)
        default_expert_file = f"/tmp/alcor_expert_{os.getuid()}.conf"
        self.expert_file = os.environ.get("ALCOR_EXPERT_FILE", default_expert_file)
        self.package_count_timer = QTimer(self)
        self.package_count_timer.setSingleShot(True)
        self.package_count_timer.setInterval(45)
        self.package_count_timer.timeout.connect(self.refresh_package_count)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(90)
        self.search_timer.timeout.connect(
            lambda: self.filter_tools(self.tool_search.text())
        )
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Alcor GNU/Linux Deployment Setup')
        self.resize(1040, 760)
        self.setMinimumSize(820, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #0b0e14;
                color: #e6eaf2;
                font-family: 'Noto Sans', 'Segoe UI', sans-serif;
            }
            QCheckBox {
                padding: 5px 4px;
                color: #cbd3df;
                spacing: 9px;
            }
            QCheckBox:hover {
                color: #ffffff;
                background-color: #151b25;
                border-radius: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #465164;
                border-radius: 4px;
                background-color: #111722;
            }
            QCheckBox::indicator:checked {
                background-color: #ff9f1c;
                border-color: #ffb84d;
            }
            QGroupBox {
                border: 1px solid #293242;
                border-radius: 10px;
                margin-top: 16px;
                padding: 14px 10px 10px 10px;
                background-color: #10151e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 7px;
                color: #f0b35a;
                font-weight: 700;
                background-color: #0b0e14;
            }
            QComboBox, QLineEdit {
                min-height: 20px;
                padding: 7px 10px;
                border: 1px solid #303b4d;
                border-radius: 7px;
                background-color: #111722;
                selection-background-color: #ff9f1c;
            }
            QComboBox:focus, QLineEdit:focus {
                border-color: #d58b27;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #303b4d;
                background-color: #111722;
                selection-background-color: #273448;
                selection-color: #ffffff;
            }
            QPushButton {
                padding: 9px 16px;
                border: 1px solid #39465b;
                border-radius: 7px;
                background-color: #171e29;
                color: #edf1f7;
                font-weight: 700;
            }
            QPushButton:hover {
                border-color: #ff9f1c;
                background-color: #202a38;
            }
            QPushButton:disabled {
                color: #727d8d;
                border-color: #27303d;
                background-color: #121720;
            }
            QScrollArea {
                border: 1px solid #283243;
                border-radius: 10px;
                background-color: #0e131b;
            }
            QScrollBar:vertical {
                width: 11px;
                background: #0e131b;
                margin: 3px;
            }
            QScrollBar::handle:vertical {
                background: #39465a;
                border-radius: 5px;
                min-height: 36px;
            }
            QScrollBar::handle:vertical:hover {
                background: #53637b;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(10)
        
        title = QLabel("ALCOR LINUX INSTALLER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff; letter-spacing: 2px; margin-top: 8px; margin-bottom: 2px;")
        main_layout.addWidget(title)

        subtitle = QLabel(
            "Choose a profile, customize your packages, and review the deployment."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #747d8f; font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)

        self.tool_search = QLineEdit()
        self.tool_search.setPlaceholderText("Search tools across the selected profile...")
        self.tool_search.setClearButtonEnabled(True)
        self.tool_search.setStyleSheet("""
            QLineEdit {
                color: #e5e7eb;
                background-color: #11141b;
                border: 1px solid #29303d;
                border-radius: 7px;
                padding: 9px 12px;
                selection-background-color: #344054;
            }
            QLineEdit:focus {
                border-color: #697386;
            }
        """)
        self.tool_search.textChanged.connect(self.schedule_tool_filter)
        main_layout.addWidget(self.tool_search)

        mode_layout = QGridLayout()
        mode_layout.setSpacing(15)
        mode_layout.setColumnStretch(0, 1)
        mode_layout.setColumnStretch(1, 1)
        
        self.radio_pentest = QRadioButton("  AlcorPentest")
        self.radio_pentest.setIcon(QIcon(QPixmap(os.path.join(self.logo_dir, "red_alcor.png"))))
        self.radio_pentest.setIconSize(QSize(42, 42))
        self.radio_pentest.setMinimumSize(250, 68)
        self.radio_pentest.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.radio_pentest.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #aeb6c5;
                padding: 12px 16px;
                border: 1px solid #29303d;
                border-radius: 8px;
                background-color: #11141b;
            }
            QRadioButton:checked {
                color: #ff1e27;
                border-color: #ff1e27;
                background-color: #140708;
            }
        """)
        mode_layout.addWidget(self.radio_pentest, 0, 0)

        self.radio_daily = QRadioButton("  AlcorDaily")
        self.radio_daily.setIcon(QIcon(QPixmap(os.path.join(self.logo_dir, "blue_alcor.png"))))
        self.radio_daily.setIconSize(QSize(42, 42))
        self.radio_daily.setMinimumSize(250, 68)
        self.radio_daily.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.radio_daily.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #aeb6c5;
                padding: 12px 16px;
                border: 1px solid #29303d;
                border-radius: 8px;
                background-color: #11141b;
            }
            QRadioButton:checked {
                color: #1e77ff;
                border-color: #1e77ff;
                background-color: #070d14;
            }
        """)
        mode_layout.addWidget(self.radio_daily, 0, 1)

        self.radio_carma = QRadioButton("  AlcorCarma")
        self.radio_carma.setIcon(QIcon(QPixmap(os.path.join(self.logo_dir, "purple_alcor.png"))))
        self.radio_carma.setIconSize(QSize(42, 42))
        self.radio_carma.setMinimumSize(250, 68)
        self.radio_carma.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.radio_carma.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #aeb6c5;
                padding: 12px 16px;
                border: 1px solid #29303d;
                border-radius: 8px;
                background-color: #11141b;
            }
            QRadioButton:checked {
                color: #a61eff;
                border-color: #a61eff;
                background-color: #0e0714;
            }
        """)
        mode_layout.addWidget(self.radio_carma, 1, 0)

        self.radio_expert = QRadioButton("  AlcorExpert")
        self.radio_expert.setIcon(QIcon(QPixmap(os.path.join(self.logo_dir, "expert_alcor.png"))))
        self.radio_expert.setIconSize(QSize(42, 42))
        self.radio_expert.setMinimumSize(250, 68)
        self.radio_expert.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.radio_expert.setStyleSheet("""
            QRadioButton {
                font-size: 14px;
                font-weight: bold;
                color: #aeb6c5;
                padding: 12px 16px;
                border: 1px solid #29303d;
                border-radius: 8px;
                background-color: #11141b;
            }
            QRadioButton:checked {
                color: #ff9f1c;
                border-color: #ff9f1c;
                background-color: #171107;
            }
        """)
        mode_layout.addWidget(self.radio_expert, 1, 1)

        main_layout.addLayout(mode_layout)

        display_manager_row = QHBoxLayout()
        display_manager_label = QLabel("Display manager")
        display_manager_label.setStyleSheet(
            "color: #c7ccd6; font-weight: bold; padding: 6px;"
        )
        self.display_manager = QComboBox()
        self.display_manager.addItem("LightDM + XFCE", "lightdm")
        self.display_manager.addItem("SDDM + KDE (Coming Soon)", "sddm")
        self.display_manager.addItem("GDM + GNOME (Coming Soon)", "gdm")
        manager_model = self.display_manager.model()
        manager_model.item(1).setEnabled(False)
        manager_model.item(2).setEnabled(False)
        self.display_manager.setMinimumHeight(34)
        self.display_manager.setMinimumWidth(280)
        self.display_manager.setStyleSheet("""
            QComboBox {
                color: #e5e7eb;
                background-color: #11141b;
                border: 1px solid #343b49;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView {
                color: #e5e7eb;
                background-color: #11141b;
                selection-background-color: #ff9f1c;
                selection-color: #111111;
            }
        """)
        self.display_manager.currentIndexChanged.connect(self.update_expert_summary)
        display_manager_row.addWidget(display_manager_label)
        display_manager_row.addWidget(self.display_manager)
        display_manager_row.addStretch()
        main_layout.addLayout(display_manager_row)

        self.selection_status = QLabel("No deployment profile selected")
        self.selection_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selection_status.setStyleSheet("color: #747d8f; font-size: 12px; padding: 8px;")
        main_layout.addWidget(self.selection_status)

        self.package_count_label = QLabel("0 packages selected")
        self.package_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.package_count_label.setStyleSheet("color: #9aa3b2; font-size: 12px; padding-bottom: 4px;")
        main_layout.addWidget(self.package_count_label)

        self.radio_pentest.toggled.connect(self.switch_panel)
        self.radio_daily.toggled.connect(self.switch_panel)
        self.radio_carma.toggled.connect(self.switch_panel)
        self.radio_expert.toggled.connect(self.switch_panel)

        self.stack = QStackedWidget()
        
        self.page_empty = QLabel("Select a deployment profile to get started.")
        self.page_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_empty.setStyleSheet("color: #48484a; font-style: italic; font-size: 14px;")
        
        self.page_pentest = self.init_pentest_ui()
        self.page_daily = self.init_daily_ui()
        self.page_carma = self.init_carma_ui()
        self.page_expert = self.init_expert_ui()

        self.stack.addWidget(self.page_empty)
        self.stack.addWidget(self.page_pentest)
        self.stack.addWidget(self.page_daily)
        self.stack.addWidget(self.page_carma)
        self.stack.addWidget(self.page_expert)
        main_layout.addWidget(self.stack)

        btn_layout = QHBoxLayout()
        self.btn_save_profile = QPushButton("SAVE PROFILE")
        self.btn_save_profile.setStyleSheet("""
            QPushButton {
                background-color: #11141b;
                border: 1px solid #343b49;
                border-radius: 6px;
                padding: 10px 18px;
                color: #cbd0da;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #697386;
                color: #ffffff;
            }
        """)
        self.btn_save_profile.clicked.connect(self.save_profile)
        btn_layout.addWidget(self.btn_save_profile)
        btn_layout.addStretch()
        self.btn_launch = QPushButton("INITIALIZE CALAMARES ENGINE")
        self.btn_launch.setStyleSheet("""
            QPushButton {
                background-color: #a96410;
                border: 1px solid #d58b27;
                border-radius: 8px;
                padding: 11px 24px;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c27b1a;
                border-color: #ffb84d;
            }
        """)
        self.btn_launch.clicked.connect(self.save_and_launch)
        btn_layout.addWidget(self.btn_launch)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.stack.setCurrentIndex(0)

    def update_dynamic_styles(self, color_code):
        style = f"""
            QGroupBox {{
                border: 1px solid #303b4d;
                border-top: 2px solid {color_code};
                border-radius: 10px;
                margin-top: 14px;
                padding: 14px 10px 10px 10px;
                background-color: #10151e;
            }}
            QGroupBox::title {{
                color: {color_code};
                font-weight: bold;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 7px;
                background-color: #0b0e14;
            }}
            QCheckBox::indicator:checked {{
                background-color: {color_code};
                border: 1px solid {color_code};
            }}
        """
        active_page = self.stack.currentWidget()
        if active_page is not None and hasattr(active_page, "widget"):
            active_page.widget().setStyleSheet(style)
        
        self.btn_launch.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_code};
                border: 1px solid {color_code};
                border-radius: 8px;
                padding: 11px 24px;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                border-color: #ffffff;
                background-color: {color_code};
            }}
        """)

    def switch_panel(self):
        if self.radio_pentest.isChecked():
            self.stack.setCurrentIndex(1)
            self.update_dynamic_styles("#ff1e27") # Neon Kırmızı
            self.selection_status.setText("AlcorPentest selected - security toolkit and assessment utilities")
        elif self.radio_daily.isChecked():
            self.stack.setCurrentIndex(2)
            self.update_dynamic_styles("#1e77ff") # Neon Mavi
            self.selection_status.setText("AlcorDaily selected - desktop, gaming, work and media tools")
        elif self.radio_carma.isChecked():
            self.stack.setCurrentIndex(3)
            self.update_dynamic_styles("#a61eff") # Neon Mor
            self.selection_status.setText("AlcorCarma selected - combined security and daily environment")
        elif self.radio_expert.isChecked():
            self.stack.setCurrentIndex(4)
            self.update_expert_kernel_style()
            self.selection_status.setText("AlcorExpert selected - choose your kernel and advanced toolset")

        self.update_package_count()

    def update_expert_kernel_style(self, _index=None):
        kernel_colors = {
            "linux": "#ff9f1c",
            "linux-zen": "#38d996",
            "linux-hardened": "#ff5c5c",
            "linux-lts": "#5ba7ff"
        }
        color = kernel_colors.get(self.expert_kernel.currentData(), "#ff9f1c")
        if self.radio_expert.isChecked():
            self.update_dynamic_styles(color)
            self.update_expert_summary()

    def create_master_group(self, title, tools, storage_dict):
        category_icons = {
            "Recon": "[R]",
            "Web": "[W]",
            "Wireless": "[N]",
            "Network": "[N]",
            "Password": "[P]",
            "Exploit": "[X]",
            "Cloud": "[C]",
            "Container": "[C]",
            "Forensics": "[F]",
            "Reverse": "[F]",
            "Gaming": "[G]",
            "Media": "[M]",
            "Development": "[D]",
            "Terminal": "[T]",
            "Monitoring": "[S]",
            "Hardware": "[S]",
            "Privacy": "[V]",
            "Social": "[V]",
            "Virtualization": "[V]"
        }
        icon = next((value for key, value in category_icons.items() if key in title), "[+]")
        box = QGroupBox(f"{icon}  {title}")
        box_lay = QVBoxLayout()
        box_lay.setContentsMargins(12, 10, 12, 10)
        box_lay.setSpacing(8)
        
        category_header = QHBoxLayout()
        master_chk = QCheckBox("Select All / Clear All")
        master_chk.setStyleSheet(
            "font-weight: 600; font-size: 12px; color: #aeb8c8;"
        )
        category_header.addWidget(master_chk)
        category_header.addStretch()
        expand_button = QToolButton()
        expand_button.setText("Show packages")
        expand_button.setCheckable(True)
        expand_button.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        expand_button.setArrowType(Qt.ArrowType.RightArrow)
        expand_button.setStyleSheet(
            "QToolButton { color: #9eabbc; padding: 4px 7px; "
            "border: 1px solid #303b4d; border-radius: 5px; }"
            "QToolButton:hover { color: #ffffff; border-color: #687891; }"
        )
        category_header.addWidget(expand_button)
        box_lay.addLayout(category_header)
        
        grid_widget = QWidget()
        grid_lay = QGridLayout(grid_widget)
        grid_lay.setContentsMargins(0, 0, 0, 0)
        
        child_boxes = []
        for index, tool in enumerate(tools):
            chk = QCheckBox(tool)
            chk.setChecked(True)
            chk.stateChanged.connect(self.update_package_count)
            child_boxes.append(chk)
            self.tool_entries.append((chk, box, grid_widget))
            self.tool_groups.add(box)
            
            row = index // 2
            col = index % 2
            grid_lay.addWidget(chk, row, col)
            
        storage_dict[title] = child_boxes
        self.category_expanded[id(box)] = False
        self.category_toggle_buttons[id(box)] = expand_button
        self.category_grids[id(box)] = grid_widget

        master_chk.setChecked(True)
        master_chk.toggled.connect(
            lambda checked, cb_list=child_boxes:
                self.set_category_selected(checked, cb_list)
        )
        expand_button.toggled.connect(
            lambda expanded, package_grid=grid_widget, group=box:
                self.toggle_category(expanded, package_grid, group)
        )
        
        grid_widget.setVisible(False)
        box_lay.addWidget(grid_widget)
        box.setLayout(box_lay)
        return box

    def set_category_selected(self, checked, child_boxes):
        blockers = [QSignalBlocker(checkbox) for checkbox in child_boxes]
        try:
            for checkbox in child_boxes:
                checkbox.setChecked(checked)
        finally:
            del blockers

        self.update_package_count()

    def toggle_category(self, expanded, package_grid, group):
        self.category_expanded[id(group)] = expanded
        toggle_button = self.category_toggle_buttons[id(group)]
        toggle_button.setText("Hide packages" if expanded else "Show packages")
        toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow
        )
        package_grid.setVisible(expanded or bool(self.tool_search.text().strip()))
        self.filter_tools(self.tool_search.text())
        self.update_package_count()

    def schedule_tool_filter(self, _query):
        self.search_timer.start()

    def filter_tools(self, query):
        query = query.strip().lower()
        groups_with_matches = set()
        for checkbox, group, _package_grid in self.tool_entries:
            matches = not query or query in checkbox.text().lower()
            checkbox.setVisible(matches)
            if matches:
                groups_with_matches.add(id(group))

        for group in self.tool_groups:
            group_id = id(group)
            has_matches = group_id in groups_with_matches
            group.setVisible(not query or has_matches)
            toggle_button = self.category_toggle_buttons[group_id]
            toggle_button.setEnabled(not query)
            toggle_button.setText(
                "Search matches"
                if query and has_matches
                else (
                    "Hide packages"
                    if self.category_expanded.get(group_id, False)
                    else "Show packages"
                )
            )
            self.category_grids[group_id].setVisible(
                (bool(query) and has_matches)
                or self.category_expanded.get(group_id, False)
            )

    def update_package_count(self, _state=None):
        self.package_count_timer.start()

    def refresh_package_count(self):
        selected = self.get_selected_packages()
        count = len(selected)
        label = f"{count} package{'s' if count != 1 else ''} selected"
        if self.package_count_label.text() != label:
            self.package_count_label.setText(label)
        if (
            self.radio_expert.isChecked()
            and hasattr(self, "expert_profile_packages")
        ):
            self.expert_profile_packages.setText(
                f"{count} package{'s' if count != 1 else ''} available below"
            )
            self.update_expert_summary()

    def init_pentest_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sections = {
            "Recon & Information Gathering": ["nmap", "recon-ng", "subfinder", "amass", "theharvester", "masscan", "dnsrecon", "rustscan"],
            "Web Testing & Vulnerability": ["nikto", "burpsuite", "sqlmap", "gobuster", "ffuf", "nuclei", "zaproxy", "whatweb", "wpscan"],
            "Wireless & Network Analysis": ["aircrack-ng", "wifite", "wireshark-qt", "bettercap", "hcxdumptool", "hcxtools", "proxychains-ng", "openvpn"],
            "Password, Exploit & Utility": ["john", "hashcat", "hydra", "metasploit", "responder", "seclists", "wordlists", "enum4linux", "netexec"],
            "Network, Traffic & OSINT": ["tcpdump", "socat", "netcat", "whois", "bind", "smbclient", "bind-tools", "tor"],
            "Cloud & Container Security": ["aws-cli-v2", "kubectl", "trivy", "skopeo", "docker", "podman", "k9s", "yq"],
            "Forensics & Reverse Engineering": ["autopsy", "binwalk", "foremost", "sleuthkit", "volatility3", "yara", "radare2", "ghidra", "strace", "ltrace"],
            "Social Engineering & Privacy": ["set", "evilginx", "mitmproxy", "proxychains-ng", "tor", "torsocks", "macchanger", "hashcat"]
        }

        for sec_title, tools in sections.items():
            layout.addWidget(self.create_master_group(sec_title, tools, self.pentest_boxes))

        scroll.setWidget(widget)
        return scroll

    def init_daily_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        sections = {
            "Gaming (Zen Kernel Tuned)": ["steam", "lutris", "heroic-games-launcher-bin", "wine-staging", "gamemode", "mangohud", "prismlauncher", "protonup-qt"],
            "Digital Workspace & Media": ["spotify", "vlc", "obs-studio", "discord", "firefox", "chromium", "gimp", "kdenlive", "audacity", "krita"],
            "Productivity & Development": ["git", "neovim", "docker", "docker-compose", "python", "nodejs", "libreoffice-fresh", "gcc", "cmake", "rust", "go", "htop"],
            "Communication & File Tools": ["thunderbird", "filezilla", "qbittorrent", "signal-desktop", "rsync", "rclone", "curl", "wget"],
            "Terminal & System Utilities": ["alacritty", "tmux", "ripgrep", "fd", "bat", "fzf", "tree", "ncdu"],
            "Virtualization & Containers": ["virt-manager", "qemu-desktop", "libvirt", "virt-viewer", "podman-compose", "vagrant", "virtualbox"],
            "System Monitoring & Hardware": ["btop", "iotop", "nmon", "lm_sensors", "smartmontools", "nvtop", "sysstat", "pciutils"]
        }

        for sec_title, tools in sections.items():
            layout.addWidget(self.create_master_group(sec_title, tools, self.daily_boxes))

        scroll.setWidget(widget)
        return scroll

    def init_carma_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.carma_pentest_boxes = {}
        self.carma_daily_boxes = {}
        
        info_lbl = QLabel("Hybrid Environment Active: combined security and daily package groups.")
        info_lbl.setStyleSheet("color: #a61eff; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(info_lbl)

        kernel_info = QLabel(
            "Dual kernel host: Daily/Game (Zen) + CyberSEC (Linux)"
        )
        kernel_info.setStyleSheet(
            "color: #c7ccd6; font-weight: bold; padding: 6px;"
        )
        layout.addWidget(kernel_info)
        
        sections_p = {
            "Hybrid Suite - Recon": ["nmap", "recon-ng", "subfinder", "amass", "theharvester", "masscan", "dnsrecon", "rustscan"],
            "Hybrid Suite - Web Testing": ["nikto", "burpsuite", "sqlmap", "gobuster", "ffuf", "nuclei", "zaproxy", "whatweb", "wpscan"],
            "Hybrid Suite - Wireless": ["aircrack-ng", "wifite", "wireshark-qt", "bettercap", "hcxdumptool", "hcxtools", "proxychains-ng", "openvpn"],
            "Hybrid Suite - Passwords & Exploits": ["john", "hashcat", "hydra", "metasploit", "responder", "seclists", "wordlists", "enum4linux", "netexec"],
            "Hybrid Suite - Network & OSINT": ["tcpdump", "socat", "netcat", "whois", "bind", "smbclient", "bind-tools", "tor"],
            "Hybrid Suite - Cloud & Containers": ["aws-cli-v2", "kubectl", "trivy", "skopeo", "docker", "podman", "k9s", "yq"],
            "Hybrid Suite - Forensics & RE": ["autopsy", "binwalk", "foremost", "sleuthkit", "volatility3", "yara", "radare2", "ghidra", "strace", "ltrace"],
            "Hybrid Suite - Privacy & Social Testing": ["set", "evilginx", "mitmproxy", "proxychains-ng", "tor", "torsocks", "macchanger", "hashcat"]
        }
        for sec_title, tools in sections_p.items():
            layout.addWidget(self.create_master_group(sec_title, tools, self.carma_pentest_boxes))
            
        sections_d = {
            "Hybrid Suite - Gaming": ["steam", "lutris", "heroic-games-launcher-bin", "wine-staging", "gamemode", "mangohud", "prismlauncher", "protonup-qt"],
            "Hybrid Suite - Workspace & Media": ["spotify", "vlc", "obs-studio", "discord", "firefox", "chromium", "gimp", "kdenlive", "audacity", "krita"],
            "Hybrid Suite - Development": ["git", "neovim", "docker", "docker-compose", "python", "nodejs", "libreoffice-fresh", "gcc", "cmake", "rust", "go", "htop"],
            "Hybrid Suite - Communication & Files": ["thunderbird", "filezilla", "qbittorrent", "signal-desktop", "rsync", "rclone", "curl", "wget"],
            "Hybrid Suite - Terminal Utilities": ["alacritty", "tmux", "ripgrep", "fd", "bat", "fzf", "tree", "ncdu"],
            "Hybrid Suite - Virtualization": ["virt-manager", "qemu-desktop", "libvirt", "virt-viewer", "podman-compose", "vagrant", "virtualbox"],
            "Hybrid Suite - Monitoring & Hardware": ["btop", "iotop", "nmon", "lm_sensors", "smartmontools", "nvtop", "sysstat", "pciutils"]
        }
        for sec_title, tools in sections_d.items():
            layout.addWidget(self.create_master_group(sec_title, tools, self.carma_daily_boxes))
            
        scroll.setWidget(widget)
        return scroll

    def init_expert_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        widget = QWidget()
        layout = QVBoxLayout(widget)

        package_row = QHBoxLayout()
        package_label = QLabel("Expert package profile")
        package_label.setStyleSheet("color: #ffb84d; font-weight: bold; padding: 6px;")
        self.expert_package_profile = QComboBox()
        self.expert_package_profile.addItem("None - no packages", "none")
        self.expert_package_profile.addItem("Pentest package set", "pentest")
        self.expert_package_profile.addItem("Daily package set", "daily")
        self.expert_package_profile.addItem("Carma package set", "carma")
        self.expert_package_profile.currentIndexChanged.connect(
            lambda _index: self.update_expert_package_groups(
                self.expert_package_profile.currentData()
            )
        )
        self.expert_package_profile.currentIndexChanged.connect(
            self.update_package_count
        )
        self.expert_package_profile.setMinimumHeight(36)
        self.expert_package_profile.setStyleSheet("""
            QComboBox {
                color: #f4f4f5;
                background-color: #15130e;
                border: 1px solid #ff9f1c;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 260px;
            }
            QComboBox QAbstractItemView {
                color: #f4f4f5;
                background-color: #15130e;
                selection-background-color: #ff9f1c;
                selection-color: #111111;
            }
        """)
        package_row.addWidget(package_label)
        package_row.addWidget(self.expert_package_profile)
        package_row.addStretch()
        layout.addLayout(package_row)

        self.expert_profile_card = QFrame()
        self.expert_profile_card.setObjectName("expertProfileCard")
        profile_card_layout = QVBoxLayout(self.expert_profile_card)
        profile_card_layout.setContentsMargins(14, 10, 14, 10)
        profile_card_layout.setSpacing(3)
        self.expert_profile_title = QLabel()
        self.expert_profile_title.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )
        self.expert_profile_description = QLabel()
        self.expert_profile_description.setWordWrap(True)
        self.expert_profile_description.setStyleSheet(
            "color: #c7ccd6; font-size: 12px;"
        )
        self.expert_profile_packages = QLabel()
        self.expert_profile_packages.setStyleSheet(
            "color: #e5e7eb; font-size: 12px; font-weight: bold;"
        )
        profile_card_layout.addWidget(self.expert_profile_title)
        profile_card_layout.addWidget(self.expert_profile_description)
        profile_card_layout.addWidget(self.expert_profile_packages)
        layout.addWidget(self.expert_profile_card)

        self.expert_summary_card = QFrame()
        self.expert_summary_card.setObjectName("expertSummaryCard")
        summary_layout = QGridLayout(self.expert_summary_card)
        summary_layout.setContentsMargins(14, 10, 14, 10)
        summary_layout.setHorizontalSpacing(18)
        summary_layout.setVerticalSpacing(3)
        summary_title = QLabel("DEPLOYMENT SUMMARY")
        summary_title.setStyleSheet(
            "color: #ffb84d; font-size: 11px; font-weight: bold;"
        )
        self.expert_summary_profile = QLabel()
        self.expert_summary_kernel = QLabel()
        self.expert_summary_packages = QLabel()
        self.expert_summary_target = QLabel("Packages → Host / ALGOL")
        for label in (
            self.expert_summary_profile,
            self.expert_summary_kernel,
            self.expert_summary_packages,
            self.expert_summary_target,
        ):
            label.setStyleSheet("color: #d7dbe3; font-size: 12px;")
        summary_layout.addWidget(summary_title, 0, 0, 1, 2)
        summary_layout.addWidget(self.expert_summary_profile, 1, 0)
        summary_layout.addWidget(self.expert_summary_kernel, 1, 1)
        summary_layout.addWidget(self.expert_summary_packages, 2, 0)
        summary_layout.addWidget(self.expert_summary_target, 2, 1)
        layout.addWidget(self.expert_summary_card)

        flow_layout = QHBoxLayout()
        self.expert_host_card = self.create_expert_flow_card(
            "HOST SYSTEM",
            "Kernel, bootloader and filesystem",
            "#ff9f1c",
        )
        self.expert_algol_card = self.create_expert_flow_card(
            "ALGOL CONTAINER",
            "Verified security tools and BlackArch packages",
            "#a61eff",
        )
        flow_layout.addWidget(self.expert_host_card)
        flow_layout.addWidget(self.expert_algol_card)
        layout.addLayout(flow_layout)

        self.expert_ready_label = QLabel()
        self.expert_ready_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.expert_ready_label.setStyleSheet(
            "padding: 8px; font-weight: bold; color: #8f96a3;"
        )
        layout.addWidget(self.expert_ready_label)

        package_info = QLabel(
            "Select or clear individual packages from the chosen profile below."
        )
        package_info.setWordWrap(True)
        package_info.setStyleSheet("color: #8f96a3; padding: 10px 6px;")
        layout.addWidget(package_info)

        self.expert_package_sources = {
            "pentest": self.pentest_boxes,
            "daily": self.daily_boxes,
            "carma": self.carma_pentest_boxes | self.carma_daily_boxes,
        }
        self.expert_package_container = QWidget()
        self.expert_package_container_layout = QVBoxLayout(
            self.expert_package_container
        )
        self.expert_package_container_layout.setContentsMargins(0, 0, 0, 0)
        self.expert_package_container_layout.setSpacing(8)
        layout.addWidget(self.expert_package_container)

        kernel_row = QHBoxLayout()
        kernel_label = QLabel("Target kernel")
        kernel_label.setStyleSheet("color: #ffb84d; font-weight: bold; padding: 6px;")

        self.expert_kernel = QComboBox()
        self.expert_kernel.addItem("Linux Standard", "linux")
        self.expert_kernel.addItem("Linux Zen - Performance", "linux-zen")
        self.expert_kernel.addItem("Linux Hardened - Security", "linux-hardened")
        self.expert_kernel.addItem("Linux LTS - Stability", "linux-lts")
        self.expert_kernel.setCurrentIndex(2)
        self.expert_kernel.currentIndexChanged.connect(self.update_expert_kernel_style)
        self.expert_kernel.setMinimumHeight(36)
        self.expert_kernel.setStyleSheet("""
            QComboBox {
                color: #f4f4f5;
                background-color: #15130e;
                border: 1px solid #ff9f1c;
                border-radius: 6px;
                padding: 6px 10px;
                min-width: 260px;
            }
            QComboBox QAbstractItemView {
                color: #f4f4f5;
                background-color: #15130e;
                selection-background-color: #ff9f1c;
                selection-color: #111111;
            }
        """)
        kernel_row.addWidget(kernel_label)
        kernel_row.addWidget(self.expert_kernel)
        kernel_row.addStretch()
        layout.addLayout(kernel_row)

        settings_grid = QGridLayout()
        settings = [
            ("Container engine", "container", [("Distrobox", "distrobox"), ("Docker", "docker"), ("Podman", "podman")], 0),
            ("Firewall", "firewall", [("UFW", "ufw"), ("Firewalld", "firewalld"), ("nftables", "nftables")], 0),
            ("Desktop", "desktop", [("XFCE", "xfce"), ("GNOME (Coming Soon)", "gnome"), ("KDE Plasma (Coming Soon)", "kde"), ("Hyprland (Coming Soon)", "hyprland"), ("i3 (Coming Soon)", "i3")], 0),
            ("Filesystem", "filesystem", [("ext4", "ext4"), ("btrfs", "btrfs")], 0),
            ("Security profile", "security", [("Balanced", "balanced"), ("Privacy", "privacy"), ("Maximum Security", "maximum")], 0),
            ("Bootloader", "bootloader", [("GRUB", "grub"), ("systemd-boot", "systemd-boot")], 0),
            ("Network profile", "network", [("NetworkManager", "networkmanager"), ("iwd", "iwd")], 0)
        ]
        for index, (label, key, options, default_index) in enumerate(settings):
            row = index // 2
            column = index % 2
            setting_label = QLabel(label)
            setting_label.setStyleSheet("color: #c7ccd6; font-weight: bold; padding: 4px;")
            combo = self.create_expert_combo(options, default_index)
            if key == "desktop":
                for option_index, (_option_label, value) in enumerate(options):
                    if value != "xfce":
                        combo.model().item(option_index).setEnabled(False)
            combo.currentIndexChanged.connect(self.update_expert_flow_cards)
            self.expert_controls[key] = combo
            settings_grid.addWidget(setting_label, row * 2, column)
            settings_grid.addWidget(combo, row * 2 + 1, column)
        layout.addLayout(settings_grid)

        scroll.setWidget(widget)
        self.update_expert_package_groups("none")
        self.update_expert_profile_card("none")
        self.update_expert_summary()
        self.update_expert_flow_cards()
        return scroll

    def create_expert_flow_card(self, title, subtitle, color):
        card = QFrame()
        card.setObjectName("expertFlowCard")
        card.setStyleSheet(
            f"""
            QFrame#expertFlowCard {{
                background-color: #0d1117;
                border: 1px solid {color};
                border-radius: 8px;
            }}
            """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 9, 12, 9)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 12px;"
        )
        subtitle_label = QLabel(subtitle)
        subtitle_label.setWordWrap(True)
        subtitle_label.setStyleSheet("color: #8f96a3; font-size: 11px;")
        detail_label = QLabel()
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("color: #d7dbe3; font-size: 12px;")
        card_layout.addWidget(title_label)
        card_layout.addWidget(subtitle_label)
        card_layout.addWidget(detail_label)
        card.detail_label = detail_label
        return card

    def create_expert_combo(self, options, default_index=0):
        combo = QComboBox()
        for label, value in options:
            combo.addItem(label, value)
        combo.setCurrentIndex(default_index)
        combo.setMinimumHeight(32)
        combo.setStyleSheet("""
            QComboBox {
                color: #e5e7eb;
                background-color: #11141b;
                border: 1px solid #343b49;
                border-radius: 6px;
                padding: 5px 9px;
                min-width: 190px;
            }
            QComboBox:focus {
                border-color: #ff9f1c;
            }
            QComboBox QAbstractItemView {
                color: #e5e7eb;
                background-color: #11141b;
                selection-background-color: #ff9f1c;
                selection-color: #111111;
            }
        """)
        return combo

    def active_profile(self):
        if self.radio_pentest.isChecked():
            return "pentest", "linux", self.pentest_boxes
        if self.radio_daily.isChecked():
            return "daily", "linux-zen", self.daily_boxes
        if self.radio_carma.isChecked():
            groups = {**self.carma_pentest_boxes, **self.carma_daily_boxes}
            return "carma", "linux-zen,linux", groups
        if self.radio_expert.isChecked():
            package_profile = self.expert_package_profile.currentData()
            groups = {
                str(id(group)): self.expert_package_widget_boxes[group]
                for group in self.expert_package_groups.get(package_profile, [])
            }
            return "expert", self.expert_kernel.currentData(), groups
        return None, None, {}

    def update_expert_package_groups(self, profile_name):
        if profile_name != "none" and \
           profile_name not in self.built_expert_package_profiles:
            source_groups = self.expert_package_sources.get(profile_name, {})
            for title, source_checkboxes in source_groups.items():
                tools = [checkbox.text() for checkbox in source_checkboxes]
                group_title = f"Expert {profile_name.title()} - {title}"
                group = self.create_master_group(
                    group_title, tools, self.expert_boxes
                )
                self.expert_package_groups.setdefault(profile_name, []).append(group)
                self.expert_package_widgets.append(group)
                self.expert_package_widget_boxes[group] = \
                    self.expert_boxes[group_title]
                self.expert_package_container_layout.addWidget(group)
            self.built_expert_package_profiles.add(profile_name)

        visible_groups = {
            id(group)
            for group in self.expert_package_groups.get(profile_name, [])
        }
        for group in self.expert_package_widgets:
            group.setVisible(id(group) in visible_groups)
        self.update_expert_profile_card(profile_name)

    def update_expert_profile_card(self, profile_name):
        profiles = {
            "none": (
                "NONE",
                "Expert settings only; no Algol packages will be installed.",
                "#6b7280",
            ),
            "pentest": (
                "PENTEST PACKAGE SET",
                "Recon, web testing, wireless and offensive security tools.",
                "#ff1e27",
            ),
            "daily": (
                "DAILY PACKAGE SET",
                "Desktop, gaming, media, development and productivity tools.",
                "#1e77ff",
            ),
            "carma": (
                "CARMA PACKAGE SET",
                "The complete Pentest and Daily package collection.",
                "#a61eff",
            ),
        }
        title, description, color = profiles.get(
            profile_name, profiles["none"]
        )
        package_count = len(self.get_selected_packages()) if hasattr(
            self, "expert_package_widgets"
        ) else 0
        self.expert_profile_title.setText(title)
        self.expert_profile_title.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color};"
        )
        self.expert_profile_description.setText(description)
        self.expert_profile_packages.setText(
            f"{package_count} package{'s' if package_count != 1 else ''} "
            "available below"
        )
        self.expert_profile_card.setStyleSheet(
            f"""
            QFrame#expertProfileCard {{
                background-color: #11141b;
                border: 1px solid {color};
                border-left: 5px solid {color};
                border-radius: 8px;
            }}
            """
        )
        self.update_expert_summary()

    def update_expert_summary(self):
        if not hasattr(self, "expert_summary_profile"):
            return
        profile_name = self.expert_package_profile.currentData()
        profile_labels = {
            "none": "None",
            "pentest": "Pentest",
            "daily": "Daily",
            "carma": "Carma",
        }
        package_count = len(self.get_selected_packages())
        self.expert_summary_profile.setText(
            f"Profile: Expert + {profile_labels.get(profile_name, 'None')}"
        )
        self.expert_summary_kernel.setText(
            f"Kernel: {self.expert_kernel.currentData()}"
        )
        if hasattr(self, "display_manager"):
            self.expert_summary_target.setText(
                f"Display: {self.display_manager.currentData()}  •  "
                "Packages → Host / ALGOL"
            )
        self.expert_summary_packages.setText(
            f"Packages: {package_count} selected"
        )
        self.expert_summary_card.setStyleSheet(
            """
            QFrame#expertSummaryCard {
                background-color: #0d1117;
                border: 1px solid #303846;
                border-radius: 8px;
            }
            """
        )
        self.update_expert_flow_cards()

    def update_expert_flow_cards(self):
        if not hasattr(self, "expert_host_card"):
            return
        kernel = self.expert_kernel.currentData()
        package_profile = self.expert_package_profile.currentData()
        package_count = len(self.get_selected_packages())
        self.expert_host_card.detail_label.setText(
            f"Kernel: {kernel}\n"
            f"Filesystem: {self.expert_controls['filesystem'].currentData()}\n"
            f"Bootloader: {self.expert_controls['bootloader'].currentData()}"
        )
        self.expert_algol_card.detail_label.setText(
            f"Profile: {package_profile.title()}\n"
            f"Packages: {package_count}\n"
            "Repository: BlackArch"
        )
        ready = package_profile != "none" and package_count > 0
        if ready:
            self.expert_ready_label.setText(
                "✓ READY TO DEPLOY  •  Host system + Algol container configured"
            )
            self.expert_ready_label.setStyleSheet(
                "padding: 8px; font-weight: bold; color: #38d996;"
            )
        else:
            self.expert_ready_label.setText(
                "✓ READY TO DEPLOY  •  Expert settings only"
            )
            self.expert_ready_label.setStyleSheet(
                "padding: 8px; font-weight: bold; color: #8f96a3;"
            )

    def get_selected_packages(self):
        _profile, _kernel, groups = self.active_profile()
        selected = []
        selected_names = set()
        for group in groups.values():
            for checkbox in group:
                package = checkbox.text()
                if checkbox.isChecked() and package not in selected_names:
                    selected.append(package)
                    selected_names.add(package)
        return selected

    def expert_config_values(self):
        values = {key: combo.currentData() for key, combo in self.expert_controls.items()}
        values["kernel"] = self.expert_kernel.currentData()
        values["package_profile"] = self.expert_package_profile.currentData()
        return values

    def write_selection_file(self, path):
        profile, kernel, _groups = self.active_profile()
        packages = self.get_selected_packages()
        if not profile:
            return False

        with open(path, "w", encoding="utf-8") as selection:
            selection.write(f"PROFILE:{profile}\n")
            selection.write(
                f"KERNELS:{kernel}\n" if "," in kernel else f"KERNEL:{kernel}\n"
            )
            selection.write(
                f"DISPLAY_MANAGER:{self.display_manager.currentData()}\n"
            )
            selection.write(f"PACKAGES:{','.join(packages)}\n")
        return True

    def write_expert_config(self, path):
        with open(path, "w", encoding="utf-8") as config:
            for key, value in self.expert_config_values().items():
                config.write(f"{key.upper()}={value}\n")

    def validate_packages(self, packages):
        pacman_path = "/usr/bin/pacman"
        if not packages or not os.path.exists(pacman_path):
            return True

        try:
            result = subprocess.run(
                [pacman_path, "-Si", *packages],
                capture_output=True,
                text=True,
                timeout=20,
                check=False
            )
        except (OSError, subprocess.TimeoutExpired):
            return True

        found = set(re.findall(r"^Name\s*:\s*(\S+)", result.stdout, re.MULTILINE))
        missing = [package for package in packages if package not in found]
        if not missing:
            return True

        message = "These packages were not found in the currently enabled repositories:\n\n"
        message += ", ".join(missing[:16])
        if len(missing) > 16:
            message += f"\n... and {len(missing) - 16} more"
        message += (
            "\n\nContinue anyway? BlackArch packages may resolve inside Algol after "
            "its repository is configured. AUR packages are not built automatically."
        )
        answer = QMessageBox.question(
            self,
            "Package availability warning",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return answer == QMessageBox.StandardButton.Yes

    def show_install_summary(self, packages, kernel):
        profile, _kernel, _groups = self.active_profile()
        preview = ", ".join(packages[:24])
        if len(packages) > 24:
            preview += f", ... ({len(packages) - 24} more)"
        summary = (
            f"Profile: {profile}\n"
            f"Kernel: {kernel}\n"
            f"Packages: {len(packages)}\n\n"
            f"{preview or 'No packages selected'}"
        )
        if profile == "expert":
            expert_lines = "\n".join(
                f"{key.title()}: {value}" for key, value in self.expert_config_values().items()
            )
            summary += f"\n\nExpert configuration:\n{expert_lines}"
        answer = QMessageBox.question(
            self,
            "Review deployment",
            summary,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return answer == QMessageBox.StandardButton.Yes

    def save_profile(self):
        profile, _kernel, _groups = self.active_profile()
        if not profile:
            QMessageBox.warning(self, "Deployment mode required", "Select a profile before saving it.")
            return

        profile_dir = os.path.expanduser("~/alcor-profiles")
        os.makedirs(profile_dir, exist_ok=True)
        profile_path = os.path.join(profile_dir, f"{profile}.conf")
        expert_path = os.path.join(profile_dir, f"{profile}.expert.conf")
        self.write_selection_file(profile_path)
        self.write_expert_config(expert_path)
        QMessageBox.information(self, "Profile saved", f"Profile saved to:\n{profile_path}")

    def save_and_launch(self):
        profile, kernel, _groups = self.active_profile()
        if not profile:
            QMessageBox.warning(self, "Deployment mode required", "Select a deployment mode before continuing.")
            return

        packages = self.get_selected_packages()
        if not packages and not (
            profile == "expert"
            and self.expert_package_profile.currentData() == "none"
        ):
            QMessageBox.warning(self, "No packages selected", "Select at least one package before continuing.")
            return
        if not self.validate_packages(packages) or not self.show_install_summary(packages, kernel):
            return

        expert_path = self.expert_file
        self.write_selection_file(self.selection_file)
        self.write_expert_config(expert_path)

        self.btn_launch.setEnabled(False)
        self.launch_progress = QProgressDialog("Starting Calamares...", None, 0, 0, self)
        self.launch_progress.setWindowTitle("Alcor Deployment")
        self.launch_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.launch_progress.setCancelButton(None)
        self.launch_progress.show()
        QApplication.processEvents()
        try:
            calamares_command = " ".join([
                "sudo",
                "env",
                shlex.quote(f"ALCOR_SELECTION_FILE={self.selection_file}"),
                shlex.quote(f"ALCOR_EXPERT_FILE={expert_path}"),
                "calamares",
            ])
            subprocess.Popen([
                "xfce4-terminal",
                "--hold",
                "--command",
                calamares_command,
            ])
            QTimer.singleShot(900, self.launch_progress.close)
            QTimer.singleShot(1000, self.close)
        except OSError as error:
            self.launch_progress.close()
            self.btn_launch.setEnabled(True)
            QMessageBox.critical(self, "Calamares could not start", str(error))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = AlcorFrontend()
    win.show()
    sys.exit(app.exec())