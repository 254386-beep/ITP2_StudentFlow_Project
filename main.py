"""Student Flow: premium CustomTkinter desktop UI for study planning."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from tkinter import messagebox

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).with_name(".matplotlib_cache")))

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkcalendar import Calendar

from completed_task_manager import CompletedTaskManager
from course_manager import CourseManager
from task import TASK_TYPES, Task
from task_manager import TaskManager
from theme_manager import ThemeManager
from utils import deadline_human_label, is_valid_date


THEMES = {
    "Dark": {
        "app": "#101114",
        "sidebar": "#15171c",
        "panel": "#1b1e24",
        "panel_soft": "#222630",
        "panel_hover": "#2a2f3a",
        "field": "#171a20",
        "border": "#303642",
        "text": "#f7f7fb",
        "muted": "#9aa3b2",
        "chart": "#1b1e24",
    },
    "Light": {
        "app": "#f5f6fb",
        "sidebar": "#ffffff",
        "panel": "#ffffff",
        "panel_soft": "#eef0f6",
        "panel_hover": "#e2e5ee",
        "field": "#f6f7fb",
        "border": "#d7dbe7",
        "text": "#171923",
        "muted": "#687083",
        "chart": "#ffffff",
    },
}

ACCENT = "#7c5cff"
ACCENT_HOVER = "#6d4df2"
SUCCESS = "#2fbf71"
WARNING = "#f2b84b"
DANGER = "#ef5d60"
BLUE = "#4fa3ff"

ICONS = {
    "app": "\U0001f393",
    "dashboard": "\U0001f4ca",
    "add": "\u2795",
    "tasks": "\U0001f4cb",
    "search": "\U0001f50d",
    "stats": "\U0001f4c8",
    "courses": "\U0001f4da",
    "deadlines": "\u23f0",
    "done": "\u2713",
    "completed": "\u2705",
    "save": "\U0001f4be",
    "delete": "\U0001f5d1",
    "edit": "\u270e",
    "calendar": "\U0001f4c5",
}

NAV_ITEMS = [
    ("dashboard", "Dashboard", ICONS["dashboard"]),
    ("add_task", "Add Task", ICONS["add"]),
    ("view_tasks", "View Tasks", ICONS["tasks"]),
    ("completed_tasks", "Completed Tasks", ICONS["completed"]),
    ("search", "Search", ICONS["search"]),
    ("statistics", "Statistics", ICONS["stats"]),
    ("courses", "Courses", ICONS["courses"]),
    ("deadlines", "Deadlines", ICONS["deadlines"]),
]

FILTERS = ("All", "Homework", "Project", "Exam", "Pending", "Overdue")


class StudentFlowApp(ctk.CTk):
    """Main window and page coordinator."""

    def __init__(self) -> None:
        super().__init__()
        self.theme_manager = ThemeManager()
        saved_theme = self.theme_manager.load_theme()
        self.theme_name = saved_theme.title()
        ctk.set_appearance_mode(saved_theme)
        ctk.set_default_color_theme("dark-blue")

        self.task_manager = TaskManager()
        self.completed_manager = CompletedTaskManager()
        self.course_manager = CourseManager()
        self._migrate_completed_tasks()
        self.pages: dict[str, BasePage] = {}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.active_page = "dashboard"

        self.title("Student Flow")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self._build_shell()
        self.show_page("dashboard")
        self.after(450, self.show_deadline_notification)

    @property
    def colors(self) -> dict[str, str]:
        return THEMES[self.theme_name]

    def _migrate_completed_tasks(self) -> None:
        for task in self.task_manager.extract_completed_tasks():
            if self.completed_manager.get_completed(task.id) is None:
                self.completed_manager.add_completed(task)

    def _build_shell(self) -> None:
        self.configure(fg_color=self.colors["app"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color=self.colors["app"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self._register_pages()

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=236, corner_radius=0, fg_color=self.colors["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(28, 22))
        ctk.CTkLabel(
            brand,
            text=f'{ICONS["app"]}  Student Flow',
            font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=self.colors["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Notion calm. Todoist focus.",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["muted"],
        ).pack(anchor="w", pady=(5, 0))

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.pack(fill="x", padx=12)
        for page_id, label, icon in NAV_ITEMS:
            button = ctk.CTkButton(
                nav,
                text=f"  {icon}   {label}",
                anchor="w",
                height=46,
                corner_radius=14,
                fg_color="transparent",
                text_color=self.colors["muted"],
                hover_color=self.colors["panel_hover"],
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda pid=page_id: self.show_page(pid),
            )
            button.pack(fill="x", pady=4)
            self.nav_buttons[page_id] = button

        hint = ctk.CTkFrame(self.sidebar, fg_color=self.colors["panel"], corner_radius=16)
        hint.pack(side="bottom", fill="x", padx=16, pady=18)
        ctk.CTkLabel(
            hint,
            text="Active tasks stay here.\nCompleted work moves to history.",
            justify="left",
            text_color=self.colors["muted"],
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w", padx=14, pady=14)

    def _register_pages(self) -> None:
        factories = {
            "dashboard": DashboardPage,
            "add_task": AddTaskPage,
            "view_tasks": ViewTasksPage,
            "completed_tasks": CompletedTasksPage,
            "search": SearchPage,
            "statistics": StatisticsPage,
            "courses": CoursesPage,
            "deadlines": DeadlinesPage,
        }
        for page_id, page_class in factories.items():
            page = page_class(self.content, self)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
            self.pages[page_id] = page

    def set_theme(self, theme_name: str) -> None:
        self.theme_name = theme_name
        self.theme_manager.save_theme(theme_name.lower())
        ctk.set_appearance_mode(self.theme_name.lower())
        for child in self.winfo_children():
            child.destroy()
        self.pages.clear()
        self.nav_buttons.clear()
        self._build_shell()
        self.show_page(self.active_page)

    def show_page(self, page_id: str) -> None:
        if page_id not in self.pages:
            return
        self.task_manager.refresh_statuses()
        self.pages[self.active_page].grid_remove()
        self.active_page = page_id
        page = self.pages[page_id]
        page.grid()
        page.refresh()
        self._sync_nav()

    def _sync_nav(self) -> None:
        for page_id, button in self.nav_buttons.items():
            active = page_id == self.active_page
            button.configure(
                fg_color=ACCENT if active else "transparent",
                text_color="#ffffff" if active else self.colors["muted"],
                hover_color=ACCENT_HOVER if active else self.colors["panel_hover"],
            )

    def refresh_all(self) -> None:
        self.task_manager.refresh_statuses()
        for page in self.pages.values():
            page.refresh()

    def show_deadline_notification(self) -> None:
        due_soon = self.task_manager.tasks_due_within(1)
        if due_soon:
            count = len(due_soon)
            noun = "task" if count == 1 else "tasks"
            days = {task.days_until_deadline() for task in due_soon}
            when = "today" if days == {0} else "tomorrow" if days == {1} else "within 1 day"
            messagebox.showinfo("Upcoming Deadline", f"You have {count} {noun} due {when}")


class BasePage(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, fg_color=app.colors["app"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    @property
    def colors(self) -> dict[str, str]:
        return self.app.colors

    @property
    def tasks(self) -> TaskManager:
        return self.app.task_manager

    @property
    def courses(self) -> CourseManager:
        return self.app.course_manager

    @property
    def completed(self) -> CompletedTaskManager:
        return self.app.completed_manager

    def refresh(self) -> None:
        pass

    def page_header(self, title: str, subtitle: str) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(30, 18))
        header.grid_columnconfigure(0, weight=1)
        title_area = ctk.CTkFrame(header, fg_color="transparent")
        title_area.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_area,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=self.colors["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_area,
            text=subtitle,
            font=ctk.CTkFont(size=14),
            text_color=self.colors["muted"],
        ).pack(anchor="w", pady=(4, 0))
        self.theme_toggle = ctk.CTkSegmentedButton(
            header,
            values=["☀ Light", "🌙 Dark"],
            selected_color=ACCENT,
            selected_hover_color=ACCENT_HOVER,
            unselected_color=self.colors["panel"],
            unselected_hover_color=self.colors["panel_hover"],
            text_color="#ffffff" if self.app.theme_name == "Dark" else self.colors["text"],
            command=self._change_theme,
        )
        self.theme_toggle.grid(row=0, column=1, sticky="e")
        self.theme_toggle.set("☀ Light" if self.app.theme_name == "Light" else "🌙 Dark")

    def _change_theme(self, value: str) -> None:
        self.app.set_theme("Light" if "Light" in value else "Dark")

    def clear(self, frame: ctk.CTkFrame) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def empty_state(self, parent: ctk.CTkFrame, text: str) -> None:
        ctk.CTkLabel(parent, text=text, text_color=self.colors["muted"], font=ctk.CTkFont(size=14)).pack(pady=38)

    def status_color(self, task: Task) -> str:
        if task.is_completed:
            return SUCCESS
        if task.is_overdue:
            return DANGER
        return WARNING


class HoverCard(ctk.CTkFrame):
    """Small hover transition used by cards for a desktop-app feel."""

    def __init__(self, master: ctk.CTkBaseClass, page: BasePage, **kwargs: object) -> None:
        super().__init__(
            master,
            fg_color=page.colors["panel"],
            corner_radius=18,
            border_width=1,
            border_color=page.colors["border"],
            **kwargs,
        )
        self.page = page
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event: object) -> None:
        self.configure(fg_color=self.page.colors["panel_soft"], border_width=2)

    def _on_leave(self, _event: object) -> None:
        self.configure(fg_color=self.page.colors["panel"], border_width=1)


class DashboardPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Dashboard", "Your study flow at a glance")
        self.cards = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.cards.grid(row=1, column=0, sticky="nsew", padx=26, pady=(0, 28))
        for column in range(4):
            self.cards.grid_columnconfigure(column, weight=1, uniform="dashboard")

    def refresh(self) -> None:
        self.clear(self.cards)
        active_stats = self.tasks.statistics()
        completed_total = self.completed.count()
        total = active_stats["total"] + completed_total
        completion_rate = round((completed_total / total) * 100) if total else 0
        stats = {
            **active_stats,
            "total": total,
            "completed": completed_total,
            "completion_rate": completion_rate,
            "completed_this_week": self.completed.completed_this_week(),
        }
        cards = [
            ("Total Tasks", stats["total"], ICONS["tasks"], ACCENT),
            ("Completed", stats["completed"], ICONS["done"], SUCCESS),
            ("Pending", stats["pending"], ICONS["deadlines"], WARNING),
            ("Courses Count", self.courses.count(), ICONS["courses"], BLUE),
            ("Overdue", stats["overdue"], "!", DANGER),
            ("Completed This Week", stats["completed_this_week"], ICONS["completed"], SUCCESS),
        ]
        for index, (label, value, icon, color) in enumerate(cards):
            self._stat_card(index // 4, index % 4, label, value, icon, color)
        self._progress_card(1, 1, stats)
        self._next_deadline_card(1, 2)

    def _stat_card(self, row: int, column: int, label: str, value: int, icon: str, color: str) -> None:
        card = HoverCard(self.cards, self)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8, ipady=20)
        ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=30), text_color=color).pack(anchor="w", padx=22, pady=(18, 4))
        ctk.CTkLabel(card, text=str(value), font=ctk.CTkFont(size=34, weight="bold"), text_color=color).pack(anchor="w", padx=22)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["muted"]).pack(anchor="w", padx=22, pady=(4, 18))

    def _progress_card(self, row: int, column: int, stats: dict[str, int]) -> None:
        card = HoverCard(self.cards, self)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8, ipady=24)
        rate = stats["completion_rate"]
        ctk.CTkLabel(card, text="Semester Progress", text_color=self.colors["muted"], font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=22, pady=(24, 8))
        ctk.CTkLabel(card, text=f"{rate}%", text_color=ACCENT, font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w", padx=22)
        progress = ctk.CTkProgressBar(card, height=12, corner_radius=8, progress_color=ACCENT, fg_color=self.colors["panel_soft"])
        progress.pack(fill="x", padx=22, pady=(12, 24))
        progress.set(rate / 100 if rate else 0)

    def _next_deadline_card(self, row: int, column: int) -> None:
        card = HoverCard(self.cards, self)
        card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8, ipady=24)
        task = self.tasks.next_deadline()
        ctk.CTkLabel(card, text="Next Deadline", text_color=self.colors["muted"], font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=22, pady=(24, 8))
        ctk.CTkLabel(card, text=task.title if task else "Nothing pending", text_color=self.colors["text"], font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=22)
        ctk.CTkLabel(card, text=deadline_human_label(task) if task else "Clear schedule", text_color=WARNING, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=22, pady=(8, 24))


class AddTaskPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Add Task", "Create homework, projects, and exams")
        self.selected_deadline = ctk.StringVar(value="")
        self.form = ctk.CTkFrame(self, fg_color=self.colors["panel"], corner_radius=18)
        self.form.grid(row=1, column=0, sticky="new", padx=34, pady=(0, 30))
        self.form.grid_columnconfigure(0, weight=1)
        self.title_entry = self._entry("Task title", 0, "e.g. Assignment 4")
        self._date_picker(2)
        self.type_var = ctk.StringVar(value=TASK_TYPES[0])
        self.type_menu = self._menu("Task type", 4, list(TASK_TYPES), self.type_var)
        self.course_var = ctk.StringVar(value="")
        self.course_menu = self._menu("Course", 6, ["No courses"], self.course_var)
        ctk.CTkButton(
            self.form,
            text=f'  {ICONS["save"]}  Save Task',
            height=54,
            corner_radius=16,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.save_task,
        ).grid(row=8, column=0, sticky="ew", padx=22, pady=(18, 10))
        self.status = ctk.CTkLabel(self.form, text="", text_color=self.colors["muted"])
        self.status.grid(row=9, column=0, sticky="w", padx=22, pady=(0, 20))

    def _entry(self, label: str, row: int, placeholder: str) -> ctk.CTkEntry:
        ctk.CTkLabel(self.form, text=label, text_color=self.colors["muted"], font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, sticky="w", padx=22, pady=(20 if row == 0 else 12, 6))
        entry = ctk.CTkEntry(self.form, placeholder_text=placeholder, height=46, corner_radius=14, fg_color=self.colors["field"], border_color=self.colors["border"], border_width=1)
        entry.grid(row=row + 1, column=0, sticky="ew", padx=22)
        return entry

    def _date_picker(self, row: int) -> None:
        ctk.CTkLabel(self.form, text="Deadline", text_color=self.colors["muted"], font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, sticky="w", padx=22, pady=(12, 6))
        self.deadline_button = ctk.CTkButton(
            self.form,
            text=f'{ICONS["calendar"]}  Choose date',
            anchor="w",
            height=46,
            corner_radius=14,
            fg_color=self.colors["field"],
            hover_color=self.colors["panel_hover"],
            border_color=self.colors["border"],
            border_width=1,
            text_color=self.colors["text"],
            command=self.open_calendar,
        )
        self.deadline_button.grid(row=row + 1, column=0, sticky="ew", padx=22)

    def _menu(self, label: str, row: int, values: list[str], variable: ctk.StringVar) -> ctk.CTkOptionMenu:
        ctk.CTkLabel(self.form, text=label, text_color=self.colors["muted"], font=ctk.CTkFont(size=13, weight="bold")).grid(row=row, column=0, sticky="w", padx=22, pady=(12, 6))
        menu = ctk.CTkOptionMenu(self.form, values=values, variable=variable, height=46, corner_radius=14, fg_color=self.colors["field"], button_color=ACCENT, button_hover_color=ACCENT_HOVER, dropdown_fg_color=self.colors["panel_soft"])
        menu.grid(row=row + 1, column=0, sticky="ew", padx=22)
        return menu

    def open_calendar(self) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("Choose Deadline")
        popup.geometry("330x330")
        popup.resizable(False, False)
        popup.configure(fg_color=self.colors["panel"])
        popup.transient(self.app)
        popup.grab_set()
        calendar = Calendar(
            popup,
            selectmode="day",
            date_pattern="yyyy-mm-dd",
            mindate=date(2000, 1, 1),
            background=self.colors["panel"],
            foreground=self.colors["text"],
            bordercolor=self.colors["border"],
            headersbackground=self.colors["panel_soft"],
            headersforeground=self.colors["text"],
            normalbackground=self.colors["panel"],
            normalforeground=self.colors["text"],
            weekendbackground=self.colors["panel"],
            weekendforeground=self.colors["muted"],
            othermonthbackground=self.colors["field"],
            othermonthforeground=self.colors["muted"],
            selectbackground=ACCENT,
            selectforeground="#ffffff",
        )
        calendar.pack(fill="both", expand=True, padx=14, pady=(14, 8))

        def choose() -> None:
            selected = calendar.get_date()
            self.selected_deadline.set(selected)
            self.deadline_button.configure(text=f'{ICONS["calendar"]}  {selected}')
            popup.destroy()

        ctk.CTkButton(popup, text="Choose", height=40, corner_radius=12, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=choose).pack(fill="x", padx=14, pady=(0, 14))

    def refresh(self) -> None:
        values = self.courses.courses or ["No courses"]
        self.course_menu.configure(values=values)
        if self.course_var.get() not in values:
            self.course_var.set(values[0])

    def save_task(self) -> None:
        title = self.title_entry.get().strip()
        deadline = self.selected_deadline.get().strip()
        course = self.course_var.get().strip()
        if not title:
            self._set_status("Empty title is not allowed.", True)
            return
        if not is_valid_date(deadline):
            self._set_status("Choose a valid deadline from the calendar.", True)
            return
        if not course or course == "No courses":
            self._set_status("Add a course before saving tasks.", True)
            return
        try:
            self.tasks.add_task(title, course, deadline, self.type_var.get())
        except ValueError as exc:
            self._set_status(str(exc), True)
            return
        self.title_entry.delete(0, "end")
        self.selected_deadline.set("")
        self.deadline_button.configure(text=f'{ICONS["calendar"]}  Choose date')
        self._set_status("Task saved successfully", False)
        self.app.refresh_all()

    def _set_status(self, message: str, error: bool) -> None:
        self.status.configure(text=message, text_color=DANGER if error else SUCCESS)


class ViewTasksPage(BasePage):
    HEADERS = ("Title", "Course", "Deadline", "Type", "Status", "Actions")
    WEIGHTS = (3, 2, 2, 2, 2, 3)

    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("View Tasks", "Live search, filters, and nearest-deadline sorting")
        holder = ctk.CTkFrame(self, fg_color="transparent")
        holder.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(2, weight=1)
        self.query = ctk.StringVar()
        self.filter_var = ctk.StringVar(value="All")
        controls = ctk.CTkFrame(holder, fg_color="transparent")
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls.grid_columnconfigure(0, weight=1)
        search = ctk.CTkEntry(controls, textvariable=self.query, placeholder_text="Search title, course, type, or status", height=46, corner_radius=15, fg_color=self.colors["field"], border_color=self.colors["border"])
        search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        search.bind("<KeyRelease>", lambda _event: self.refresh())
        self.filter_menu = ctk.CTkOptionMenu(controls, values=list(FILTERS), variable=self.filter_var, width=180, height=46, corner_radius=15, fg_color=self.colors["field"], button_color=ACCENT, button_hover_color=ACCENT_HOVER, command=lambda _value: self.refresh())
        self.filter_menu.grid(row=0, column=1)
        self._table_header(holder)
        self.rows = ctk.CTkScrollableFrame(holder, fg_color=self.colors["panel"], corner_radius=18, border_width=1, border_color=self.colors["border"])
        self.rows.grid(row=2, column=0, sticky="nsew")

    def _table_header(self, parent: ctk.CTkFrame) -> None:
        header = ctk.CTkFrame(parent, fg_color=self.colors["panel_soft"], corner_radius=14, height=46)
        header.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        header.grid_propagate(False)
        for column, (text, weight) in enumerate(zip(self.HEADERS, self.WEIGHTS)):
            header.grid_columnconfigure(column, weight=weight)
            ctk.CTkLabel(header, text=text, text_color=self.colors["muted"], font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=column, sticky="w", padx=12)

    def refresh(self) -> None:
        self.clear(self.rows)
        tasks = self.tasks.filtered_tasks(self.filter_var.get(), self.query.get())
        if not tasks:
            self.empty_state(self.rows, "No tasks match the current search and filter.")
            return
        for index, task in enumerate(tasks):
            self._task_row(index, task)

    def _task_row(self, index: int, task: Task) -> None:
        row = ctk.CTkFrame(self.rows, fg_color=self.colors["panel_soft"] if index % 2 else self.colors["panel"], corner_radius=12, height=58)
        row.pack(fill="x", padx=10, pady=4)
        row.pack_propagate(False)
        for column, weight in enumerate(self.WEIGHTS):
            row.grid_columnconfigure(column, weight=weight)
        for column, value in enumerate((task.title, task.course, task.deadline, task.task_type, task.status)):
            color = self.status_color(task) if column == 4 else self.colors["text"]
            ctk.CTkLabel(row, text=value, text_color=color, font=ctk.CTkFont(size=13), anchor="w").grid(row=0, column=column, sticky="w", padx=12)
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=5, sticky="e", padx=8)
        if not task.is_completed:
            ctk.CTkButton(actions, text="Complete", width=92, height=34, corner_radius=12, fg_color=SUCCESS, hover_color="#269f5f", command=lambda task_id=task.id: self.complete_task(task_id)).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Delete", width=82, height=34, corner_radius=12, fg_color=DANGER, hover_color="#d94d50", command=lambda task_id=task.id: self.delete_task(task_id)).pack(side="left", padx=4)

    def complete_task(self, task_id: str) -> None:
        try:
            task = self.tasks.complete_task(task_id)
            self.completed.add_completed(task)
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Task Error", str(exc))

    def delete_task(self, task_id: str) -> None:
        if messagebox.askyesno("Delete Task", "Delete this task?"):
            self.tasks.delete_task(task_id)
            self.app.refresh_all()


class CompletedTasksPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Completed Tasks", "Finished work, newest first")
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.colors["panel"],
            corner_radius=18,
            border_width=1,
            border_color=self.colors["border"],
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))

    def refresh(self) -> None:
        self.clear(self.list_frame)
        completed_tasks = list(self.completed.iter_completed())
        if not completed_tasks:
            self.empty_state(self.list_frame, "No completed tasks yet.")
            return
        for task in completed_tasks:
            self._completed_card(task)

    def _completed_card(self, task: dict[str, object]) -> None:
        card = ctk.CTkFrame(self.list_frame, fg_color=self.colors["panel_soft"], corner_radius=16)
        card.pack(fill="x", padx=12, pady=7, ipady=7)
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=16, pady=12)
        ctk.CTkLabel(
            info,
            text=f'{ICONS["completed"]}  {task.get("title", "")}',
            text_color=self.colors["text"],
            font=ctk.CTkFont(size=17, weight="bold"),
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f'{task.get("course", "")} • {task.get("type", task.get("task_type", ""))}',
            text_color=self.colors["muted"],
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(
            info,
            text=f'Completed: {task.get("completed_date", "")}',
            text_color=SUCCESS,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=14, pady=12)
        task_id = str(task.get("id", ""))
        ctk.CTkButton(
            actions,
            text="Restore",
            width=86,
            height=36,
            corner_radius=12,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda tid=task_id: self.restore_task(tid),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions,
            text="Delete",
            width=82,
            height=36,
            corner_radius=12,
            fg_color=DANGER,
            hover_color="#d94d50",
            command=lambda tid=task_id: self.delete_completed(tid),
        ).pack(side="left", padx=4)

    def restore_task(self, task_id: str) -> None:
        try:
            task = self.completed.pop_for_restore(task_id)
            self.tasks.restore_task(task)
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Completed Task Error", str(exc))

    def delete_completed(self, task_id: str) -> None:
        if not messagebox.askyesno("Delete Completed Task", "Permanently delete this completed task?"):
            return
        try:
            self.completed.delete_completed(task_id)
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Completed Task Error", str(exc))


class SearchPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Search", "Results update instantly while you type")
        self.query = ctk.StringVar()
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="new", padx=34, pady=(0, 10))
        bar.grid_columnconfigure(0, weight=1)
        entry = ctk.CTkEntry(bar, textvariable=self.query, placeholder_text="Search by title, course, type, or status", height=48, corner_radius=16, fg_color=self.colors["field"], border_color=self.colors["border"])
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<KeyRelease>", lambda _event: self.refresh())
        self.results = ctk.CTkScrollableFrame(self, fg_color=self.colors["panel"], corner_radius=18, border_width=1, border_color=self.colors["border"])
        self.results.grid(row=2, column=0, sticky="nsew", padx=34, pady=(0, 30))
        self.grid_rowconfigure(2, weight=1)

    def refresh(self) -> None:
        self.clear(self.results)
        query = self.query.get().strip()
        if not query:
            self.empty_state(self.results, "Type a task title or course name to search.")
            return
        matches = self.tasks.search(query)
        if not matches:
            self.empty_state(self.results, "No matching tasks found.")
            return
        for task in matches:
            TaskSummaryCard(self.results, task, self).pack(fill="x", padx=12, pady=6)


class StatisticsPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Statistics", "Completion rate and task breakdown")
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=26, pady=(0, 30))
        self.body.grid_columnconfigure(0, weight=1)

    def refresh(self) -> None:
        self.clear(self.body)
        active_stats = self.tasks.statistics()
        completed_total = self.completed.count()
        total = active_stats["total"] + completed_total
        stats = {
            **active_stats,
            "total": total,
            "completed": completed_total,
            "completion_rate": round((completed_total / total) * 100) if total else 0,
        }
        cards = ctk.CTkFrame(self.body, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew")
        for column in range(4):
            cards.grid_columnconfigure(column, weight=1, uniform="stats")
        items = [("Total", stats["total"], ACCENT), ("Completed", stats["completed"], SUCCESS), ("Pending", stats["pending"], WARNING), ("Overdue", stats["overdue"], DANGER)]
        for column, (label, value, color) in enumerate(items):
            card = ctk.CTkFrame(cards, fg_color=self.colors["panel"], corner_radius=18)
            card.grid(row=0, column=column, sticky="nsew", padx=8, ipady=26)
            ctk.CTkLabel(card, text=str(value), text_color=color, font=ctk.CTkFont(size=40, weight="bold")).pack(pady=(22, 2))
            ctk.CTkLabel(card, text=label, text_color=self.colors["muted"], font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 20))
        chart_panel = ctk.CTkFrame(self.body, fg_color=self.colors["panel"], corner_radius=18)
        chart_panel.grid(row=1, column=0, sticky="ew", padx=8, pady=16)
        ctk.CTkLabel(chart_panel, text=f'Completion rate: {stats["completion_rate"]}%', text_color=ACCENT, font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=22, pady=(18, 0))
        self._pie_chart(chart_panel, stats)

    def _pie_chart(self, parent: ctk.CTkFrame, stats: dict[str, int]) -> None:
        values = [stats["completed"], stats["pending"], stats["overdue"]]
        labels = ["Completed", "Pending", "Overdue"]
        if sum(values) == 0:
            values = [1]
            labels = ["No tasks"]
            colors = [self.colors["panel_soft"]]
        else:
            colors = [SUCCESS, WARNING, DANGER]
        figure = Figure(figsize=(5.4, 3.2), dpi=100, facecolor=self.colors["chart"])
        axis = figure.add_subplot(111)
        axis.set_facecolor(self.colors["chart"])
        axis.pie(values, labels=labels, colors=colors, autopct=None if labels == ["No tasks"] else "%1.0f%%", textprops={"color": self.colors["text"]})
        axis.axis("equal")
        canvas = FigureCanvasTkAgg(figure, master=parent)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=self.colors["chart"], highlightthickness=0)
        widget.pack(fill="both", expand=True, padx=18, pady=18)


class CoursesPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Courses", "Add, edit, and delete courses")
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=1, column=0, sticky="new", padx=34, pady=(0, 12))
        top.grid_columnconfigure(0, weight=1)
        self.course_entry = ctk.CTkEntry(top, placeholder_text="New course name", height=48, corner_radius=16, fg_color=self.colors["field"], border_color=self.colors["border"])
        self.course_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.course_entry.bind("<Return>", lambda _event: self.add_course())
        ctk.CTkButton(top, text=f'  {ICONS["add"]}  Add Course', width=164, height=48, corner_radius=16, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.add_course).grid(row=0, column=1)
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=self.colors["panel"], corner_radius=18, border_width=1, border_color=self.colors["border"])
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=34, pady=(0, 30))
        self.grid_rowconfigure(2, weight=1)

    def refresh(self) -> None:
        self.clear(self.list_frame)
        names = self.courses.courses
        if not names:
            self.empty_state(self.list_frame, "No courses yet. Add your first course above.")
            return
        for name in names:
            self._course_row(name)

    def _course_row(self, name: str) -> None:
        row = ctk.CTkFrame(self.list_frame, fg_color=self.colors["panel_soft"], corner_radius=14)
        row.pack(fill="x", padx=12, pady=6, ipady=5)
        count = self.tasks.count_by_course(name)
        ctk.CTkLabel(row, text=f'{ICONS["courses"]}  {name} ({count} tasks)', text_color=self.colors["text"], font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=16, pady=13)
        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.pack(side="right", padx=12, pady=8)
        ctk.CTkButton(actions, text=f'{ICONS["edit"]}  Edit', width=84, height=36, corner_radius=12, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=lambda old=name: self.edit_course(old)).pack(side="left", padx=4)
        ctk.CTkButton(actions, text=f'{ICONS["delete"]}  Delete', width=94, height=36, corner_radius=12, fg_color=DANGER, hover_color="#d94d50", command=lambda course=name: self.delete_course(course)).pack(side="left", padx=4)

    def add_course(self) -> None:
        try:
            self.courses.add_course(self.course_entry.get().strip())
            self.course_entry.delete(0, "end")
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Course Error", str(exc))

    def edit_course(self, old_name: str) -> None:
        dialog = ctk.CTkInputDialog(text=f"Rename '{old_name}'", title="Edit Course")
        new_name = dialog.get_input()
        if not new_name:
            return
        try:
            cleaned = new_name.strip()
            self.courses.edit_course(old_name, cleaned)
            self.tasks.rename_course_in_tasks(old_name, cleaned)
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Course Error", str(exc))

    def delete_course(self, name: str) -> None:
        if not messagebox.askyesno("Delete Course", f"Delete '{name}' and unassign its tasks?"):
            return
        try:
            self.courses.delete_course(name)
            self.tasks.remove_course_from_tasks(name)
            self.app.refresh_all()
        except ValueError as exc:
            messagebox.showerror("Course Error", str(exc))


class DeadlinesPage(BasePage):
    def __init__(self, master: ctk.CTkFrame, app: StudentFlowApp) -> None:
        super().__init__(master, app)
        self.page_header("Deadlines", "Nearest deadlines are sorted automatically")
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=self.colors["panel"], corner_radius=18, border_width=1, border_color=self.colors["border"])
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=34, pady=(0, 30))

    def refresh(self) -> None:
        self.clear(self.list_frame)
        ordered = self.tasks.tasks_by_deadline(pending_only=False)
        if not ordered:
            self.empty_state(self.list_frame, "No deadlines to show.")
            return
        for number, task in enumerate(ordered, start=1):
            self._deadline_row(number, task)

    def _deadline_row(self, number: int, task: Task) -> None:
        row = ctk.CTkFrame(self.list_frame, fg_color=self.colors["panel_soft"], corner_radius=14)
        row.pack(fill="x", padx=12, pady=6, ipady=8)
        badge = ctk.CTkFrame(row, width=46, height=46, fg_color=self.status_color(task), corner_radius=14)
        badge.pack(side="left", padx=(16, 12), pady=12)
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=str(number), text_color="#ffffff", font=ctk.CTkFont(size=17, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=12)
        ctk.CTkLabel(info, text=task.title, text_color=self.colors["text"], font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(anchor="w")
        ctk.CTkLabel(info, text=f"{task.course} - {task.task_type} - {task.status} - {task.deadline}", text_color=self.colors["muted"], font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(4, 0))
        ctk.CTkLabel(row, text=deadline_human_label(task), text_color=self.status_color(task), font=ctk.CTkFont(size=15, weight="bold")).pack(side="right", padx=20)


class TaskSummaryCard(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, task: Task, page: BasePage) -> None:
        super().__init__(master, fg_color=page.colors["panel_soft"], corner_radius=14)
        ctk.CTkLabel(self, text=task.title, text_color=page.colors["text"], font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(anchor="w", padx=16, pady=(13, 3))
        ctk.CTkLabel(self, text=f"{task.course} - {task.deadline} - {task.task_type} - {task.status}", text_color=page.status_color(task), font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", padx=16, pady=(0, 13))


def main() -> None:
    app = StudentFlowApp()
    app.mainloop()


if __name__ == "__main__":
    main()
