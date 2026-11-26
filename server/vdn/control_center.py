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
from vdn.security.pairing import PairingError, PairingStore

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
        self.pairing = PairingStore(self.paths.state / "security")
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
        self.pairing_tab = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.actions_tab, text="Applications & Actions")
        self.tabs.add(self.audit_tab, text="Activity Log")
        self.tabs.add(self.pairing_tab, text="Paired Devices")

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

        pair_toolbar = ttk.Frame(self.pairing_tab)
        pair_toolbar.pack(fill="x", pady=(0, 8))
        ttk.Button(pair_toolbar, text="Open pairing window…", command=self.open_pairing).pack(side="left")
        ttk.Button(pair_toolbar, text="Refresh", command=self.refresh_pairing).pack(side="left", padx=6)
        pair_help = ("Pairing requests do not grant access. Review each device locally, "
                     "grant only the permissions it needs, and revoke devices here.")
        ttk.Label(self.pairing_tab, text=pair_help, wraplength=820, foreground="#555").pack(anchor="w", pady=(0, 8))

        ttk.Label(self.pairing_tab, text="Pending requests", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        pending_frame = ttk.Frame(self.pairing_tab)
        pending_frame.pack(fill="both", expand=True, pady=(4, 8))
        self.pending_tree = ttk.Treeview(pending_frame, columns=("device", "permissions", "created"),
                                         show="headings", height=5, selectmode="browse")
        for key, title, width in (("device", "Device", 220), ("permissions", "Requested permissions", 420),
                                  ("created", "Requested at", 150)):
            self.pending_tree.heading(key, text=title)
            self.pending_tree.column(key, width=width, anchor="w")
        self.pending_tree.pack(fill="both", expand=True)
        ttk.Button(self.pairing_tab, text="Review + approve selected…",
                   command=self.approve_pairing).pack(anchor="w", pady=(0, 10))

        ttk.Label(self.pairing_tab, text="Paired devices", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.devices_tree = ttk.Treeview(self.pairing_tab, columns=("device", "permissions", "expiry", "state"),
                                         show="headings", height=5, selectmode="browse")
        for key, title, width in (("device", "Device", 220), ("permissions", "Granted permissions", 380),
                                  ("expiry", "Expires", 140), ("state", "State", 90)):
            self.devices_tree.heading(key, text=title)
            self.devices_tree.column(key, width=width, anchor="w")
        self.devices_tree.pack(fill="both", expand=True, pady=(4, 6))
        ttk.Button(self.pairing_tab, text="Revoke selected device",
                   command=self.revoke_device).pack(anchor="w")
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
        self.refresh_pairing()

    def open_pairing(self):
        try:
            window = self.pairing.open_pairing_window(ttl=180)
            messagebox.showinfo(
                "VDN2 pairing window",
                "A one-time pairing code is active for 3 minutes. Share it only with the Vita you are pairing.\\n\\n"
                f"{window['code']}\\n\\n"
                "The code is shown once and is not stored in plaintext. The device will remain pending until you approve it here.",
                parent=self.window,
            )
            self.refresh_pairing()
        except PairingError as exc:
            messagebox.showerror("Pairing unavailable", str(exc), parent=self.window)

    def refresh_pairing(self):
        if not hasattr(self, "pending_tree"):
            return
        for tree in (self.pending_tree, self.devices_tree):
            for item in tree.get_children():
                tree.delete(item)
        for item in self.pairing.pending_requests():
            requested = ", ".join(item["requested_permissions"])
            self.pending_tree.insert("", "end", iid=item["request_id"],
                                     values=(item["device_name"], requested, str(item["created_at"])))
        for item in self.pairing.paired_devices():
            state = "Revoked" if item["revoked"] else "Active"
            self.devices_tree.insert("", "end", iid=item["device_id"],
                                     values=(item["device_name"], ", ".join(item["permissions"]),
                                             str(item["expires_at"]), state))

    def approve_pairing(self):
        selected = self.pending_tree.selection()
        if not selected:
            messagebox.showinfo("Pairing", "Select a pending device request first.", parent=self.window)
            return
        request_id = selected[0]
        request = next((item for item in self.pairing.pending_requests()
                        if item["request_id"] == request_id), None)
        if request is None:
            self.refresh_pairing()
            return
        requested = request["requested_permissions"]
        summary = (f"Device: {request['device_name']}\\nID: {request['device_id']}\\n\\n"
                   f"Requested permissions: {', '.join(requested) or 'none'}\\n\\n"
                   "Grant only permissions needed. Enter a comma-separated subset below.")
        grant_text = simpledialog.askstring("Review device permissions", summary,
                                            initialvalue="node.info", parent=self.window)
        if grant_text is None:
            return
        granted = [item.strip() for item in grant_text.split(",") if item.strip()]
        try:
            result = self.pairing.approve_request(request_id, permissions=granted)
            messagebox.showinfo(
                "Device paired",
                f"{result['device_name'] if 'device_name' in result else request['device_name']} is now paired.\\n\\n"
                f"Device credential (shown once):\\n{result['credential']}\\n\\n"
                "Store it only on the paired Vita. It will not be shown again.",
                parent=self.window,
            )
            self.refresh_pairing()
        except PairingError as exc:
            messagebox.showerror("Approval failed", str(exc), parent=self.window)

    def revoke_device(self):
        selected = self.devices_tree.selection()
        if not selected:
            messagebox.showinfo("Pairing", "Select a paired device first.", parent=self.window)
            return
        device_id = selected[0]
        if not messagebox.askyesno("Revoke device", f"Revoke access for {device_id}?", parent=self.window):
            return
        try:
            self.pairing.revoke_device(device_id)
            self.refresh_pairing()
            self.status.configure(text=f"Device access revoked: {device_id}")
        except PairingError as exc:
            messagebox.showerror("Revocation failed", str(exc), parent=self.window)

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
