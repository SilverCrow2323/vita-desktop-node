from __future__ import annotations
import json, sys
from types import SimpleNamespace
import pytest
from server.vdn.action_manager import ActionError, ActionManager

def test_approval_confirmation_and_execution(tmp_path):
    m=ActionManager(tmp_path)
    p=m.add_custom_action(action_id="test.echo",name="Echo",argv=[sys.executable,"-c","print('ok')"])
    assert not p["approved"] and not p["enabled"] and "argv" not in p
    with pytest.raises(ActionError,match="approved"): m.run("test.echo",confirmed=True)
    m.approve("test.echo")
    with pytest.raises(ActionError,match="confirmation"): m.run("test.echo")
    result=m.run("test.echo",confirmed=True)
    assert result["returncode"]==0 and result["stdout"].strip()=="ok"

def test_persistence_and_public_argv_secrecy(tmp_path):
    m=ActionManager(tmp_path)
    m.add_custom_action(action_id="test.persist",name="Persist",argv=[sys.executable,"--version"])
    n=ActionManager(tmp_path)
    assert "argv" not in n.public_catalog()[0]
    assert json.loads(n.state_file.read_text())["test.persist"]["argv"][0]==sys.executable

def test_scanned_app_starts_disabled(tmp_path):
    m=ActionManager(tmp_path)
    app=SimpleNamespace(action_id="linux.desktop.abcdef1234567890",name="Editor",categories=("Utility",),
        icon="editor",platform="linux",launch_argv=(sys.executable,"--version"))
    p=m.register_application(app)
    assert not p["approved"] and not p["enabled"] and "argv" not in p

@pytest.mark.parametrize("argv",[["bash","-c","echo unsafe"],["sh","-c","id"],["sudo","true"],["pkexec","true"],["powershell","-Command","x"]])
def test_shell_and_privilege_escalation_blocked(tmp_path,argv):
    with pytest.raises(ActionError):
        ActionManager(tmp_path).add_custom_action(action_id="test.block",name="Blocked",argv=argv)

def test_enable_requires_approval_and_revoke(tmp_path):
    m=ActionManager(tmp_path); m.add_custom_action(action_id="test.switch",name="Switch",argv=[sys.executable,"--version"])
    with pytest.raises(ActionError,match="approved"): m.set_enabled("test.switch",True)
    m.approve("test.switch"); m.set_enabled("test.switch",False); m.revoke("test.switch")
    with pytest.raises(ActionError,match="unknown"): m.public_action("test.switch")

def test_timeout_and_extra_args_validation(tmp_path):
    m=ActionManager(tmp_path); m.add_custom_action(action_id="test.args",name="Args",argv=[sys.executable,"--version"])
    m.approve("test.args")
    with pytest.raises(ActionError,match="timeout"): m.run("test.args",confirmed=True,timeout=999)
    with pytest.raises(ActionError,match="extra arguments"): m.run("test.args",confirmed=True,extra_args=["x"]*17)
