"""Tkinter PC Control Center for Vita Desktop Node host actions."""
from __future__ import annotations

import shlex
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from vdn.action_manager import ActionError, ActionManager
from vdn.config import AppPaths

try:
    from vdn.app_catalog import scan_linux_applications
except ImportError:
    scan_linux_applications = None


def parse_command_line(command: str) -> list[str]:
    if not isinstance(command, str) or not command.strip():
        raise ValueError('Enter an executable and optional arguments.')
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f'Invalid command quoting: {exc}') from exc
    if not argv:
        raise ValueError('Enter an executable and optional arguments.')
    return argv


class ControlCenter:
    """Host-local GUI for catalog discovery, approvals, custom actions and audit."""

    def __init__(self, parent: tk.Misc):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Vita Desktop Node — PC Control Center")
        self.window.geometry("900x610")
        self.window.minsize(720, 460)
        self.paths = AppPaths.discover()
        self.manager = ActionManager(self.paths.state / "actions")
        self._build()
        self.refresh()
        self.window.transient(parent)

    def _build(self):
        outer = ttk.Frame(self.window, padding=12)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="PC CONTROL CENTER", font=("TkDefaultFont", 15, "bold")).pack(side="left")
        ttk.Label(header, text="Local host actions · approval required", foreground="#666").pack(side="right")

        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True, pady=(12, 8))
        self.actions_tab = ttk.Frame(self.tabs, padding=8)
        self.audit_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.actions_tab, text="Applications & Actions")
        self.tabs.add(self.audit_tab, text="Activity Log")

        toolbar = ttk.Frame(self.actions_tab)
        toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(toolbar, text="Scan installed apps", command=self.scan).pack(side="left")
        ttk.Button(toolbar, text="Add custom action", command=self.add_custom).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Refresh", command=self.refresh).pack(side="left")

        columns = ("name", "category", "origin", "approval", "confirmation")
        list_frame = ttk.Frame(self.actions_tab)
        list_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        for key, title, width in (
            ("name", "Application / Action", 260), ("category", "Category", 150),
            ("origin", "Source", 110), ("approval", "Approval / State", 130),
            ("confirmation", "Run confirmation", 130),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        ybar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=ybar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        ybar.pack(side="right", fill="y")

        actions = ttk.Frame(self.actions_tab)
        actions.pack(fill="x", pady=(8, 0))
        for label, callback in (
            ("Approve + Enable", self.approve),
            ("Disable", self.disable),
            ("Run…", self.run_selected),
            ("Revoke", self.revoke),
        ):
            ttk.Button(actions, text=label, command=callback).pack(side="left", padx=(0, 6))

        ttk.Label(self.actions_tab,
                  text="Commands stay on this PC. The Vita-facing catalog contains metadata and action IDs only.",
                  foreground="#555", wraplength=800).pack(anchor="w", pady=(10, 0))

        audit_bar = ttk.Frame(self.audit_tab)
        audit_bar.pack(fill="x")
        ttk.Button(audit_bar, text="Refresh activity", command=self.refresh_audit).pack(side="left")
        self.audit_text = tk.Text(self.audit_tab, height=20, wrap="none", state="disabled",
                                  font=("TkFixedFont", 9))
        self.audit_text.pack(fill="both", expand=True, pady=(8, 0))
        self.status = ttk.Label(outer, text="Ready", anchor="w")
        self.status.pack(fill="x")

    def _selected_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("PC Control Center", "Select an action first.", parent=self.window)
            return None
        return selected[0]

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for action in self.manager.public_catalog():
            state = "Enabled" if action["enabled"] else "Disabled"
            if not action["approved"]:
                state = "Needs approval"
            categories = ", ".join(action.get("categories") or []) or "—"
            confirmation = "Required" if action.get("requires_confirmation") else "Not required"
            self.tree.insert("", "end", iid=action["action_id"],
                             values=(action["name"], categories, action.get("origin") or "host",
                                     state, confirmation))
        self.status.configure(text=f"{len(self.tree.get_children())} registered action(s) · local host only")
        self.refresh_audit()

    def scan(self):
        if not sys.platform.startswith("linux") or scan_linux_applications is None:
            messagebox.showinfo("Application scan",
                                "Automatic application discovery currently supports Linux XDG desktop entries. "
                                "Windows discovery will be added in a later milestone.",
                                parent=self.window)
            return
        try:
            applications = scan_linux_applications()
            imported = 0
            for app in applications:
                self.manager.register_application(app)
                imported += 1
            self.refresh()
            self.status.configure(text=f"Scanned {len(applications)} desktop entries · {imported} imported or refreshed")
            messagebox.showinfo("Application scan",
                                f"Found {len(applications)} visible applications.\n"
                                "New or changed launch commands remain unapproved and disabled.",
                                parent=self.window)
        except (OSError, ActionError, ValueError) as exc:
            messagebox.showerror("Application scan", str(exc), parent=self.window)

    def add_custom(self):
        name = simpledialog.askstring("New custom action", "Display name:", parent=self.window)
        if name is None:
            return
        command = simpledialog.askstring(
            "New custom action", "Executable and arguments (parsed as argv; no shell):",
            parent=self.window)
        if command is None:
            return
        try:
            argv = parse_command_line(command)
            # IDs are stable, readable and namespaced. Collisions are rejected by the manager.
            import re
            slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")[:48] or "action"
            import hashlib
            digest = hashlib.sha256((name + "\0" + command).encode("utf-8")).hexdigest()[:10]
            action_id = f"custom.{slug}.{digest}"
            self.manager.add_custom_action(action_id=action_id, name=name, argv=argv)
            self.refresh()
            self.status.configure(text=f"Added {name} · awaiting local approval")
        except (ValueError, ActionError) as exc:
            messagebox.showerror("New custom action", str(exc), parent=self.window)

    def approve(self):
        action_id = self._selected_id()
        if not action_id:
            return
        try:
            details = self.manager.local_details(action_id)
            command_preview = shlex.join(details.get("argv") or [])
            approved = messagebox.askyesno(
                "Review and approve action",
                f"Approve '{details['name']}' and enable it on this PC?\\n\\n"
                f"Executable and arguments:\\n{command_preview}\\n\\n"
                "This command remains stored on this PC. Each launch will still require confirmation.",
                parent=self.window,
            )
            if not approved:
                return
            self.manager.approve(action_id, enabled=True)
            self.refresh()
            self.status.configure(text=f"Approved and enabled: {action_id}")
        except ActionError as exc:
            messagebox.showerror("Approval failed", str(exc), parent=self.window)

    def disable(self):
        action_id = self._selected_id()
        if not action_id:
            return
        try:
            self.manager.set_enabled(action_id, False)
            self.refresh()
            self.status.configure(text=f"Disabled: {action_id}")
        except ActionError as exc:
            messagebox.showerror("Disable failed", str(exc), parent=self.window)

    def revoke(self):
        action_id = self._selected_id()
        if not action_id:
            return
        if not messagebox.askyesno("Revoke action", f"Remove '{action_id}' from the host catalog?",
                                   parent=self.window):
            return
        try:
            self.manager.revoke(action_id)
            self.refresh()
            self.status.configure(text=f"Revoked: {action_id}")
        except ActionError as exc:
            messagebox.showerror("Revoke failed", str(exc), parent=self.window)

    def run_selected(self):
        action_id = self._selected_id()
        if not action_id:
            return
        try:
            action = self.manager.public_action(action_id)
            if not action["approved"] or not action["enabled"]:
                raise ActionError("This action must be approved and enabled first.")
            if not messagebox.askyesno(
                "Confirm application launch",
                f"Start '{action['name']}' on this PC?\n\n"
                "The saved host-side executable and arguments will be launched without a shell.",
                parent=self.window,
            ):
                return
            self.status.configure(text=f"Starting {action['name']}…")
            def worker():
                try:
                    result = self.manager.launch(action_id, confirmed=True)
                    detail = f"Started successfully · PID {result['pid']}"
                    self.window.after(0, lambda: self.status.configure(text=f"{action['name']}: {detail}"))
                    self.window.after(0, self.refresh_audit)
                except Exception as exc:
                    self.window.after(0, lambda: messagebox.showerror(
                        "Launch failed", str(exc), parent=self.window))
            threading.Thread(target=worker, daemon=True).start()
        except ActionError as exc:
            messagebox.showerror("Launch unavailable", str(exc), parent=self.window)

    def refresh_audit(self):
        try:
            lines = self.manager.audit_file.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            lines = []
        self.audit_text.configure(state="normal")
        self.audit_text.delete("1.0", "end")
        self.audit_text.insert("end", "\n".join(lines[-500:]) or "No recorded activity yet.")
        self.audit_text.configure(state="disabled")


def open_control_center(parent: tk.Misc) -> ControlCenter:
    """Create and return a Control Center window."""
    return ControlCenter(parent)
