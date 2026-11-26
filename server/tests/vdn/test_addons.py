import unittest

from vdn.addons.api import AddonManifest
from vdn.addons.manager import AddonManager
from vdn.addons.registry import AddonRegistry


class FakeAddon:
    manifest = AddonManifest(
        addon_id="org.vdn.tests.fake",
        name="Fake",
        version="0.1.0",
        description="Test add-on",
        permissions=("host.metrics.read",),
    )

    def __init__(self):
        self.events = []

    def register(self, context):
        self.events.append(("register", context.granted_permissions))

    def start(self):
        self.events.append(("start",))

    def stop(self):
        self.events.append(("stop",))

    def unregister(self):
        self.events.append(("unregister",))


class AddonTests(unittest.TestCase):
    def setUp(self):
        self.instances = []
        self.registry = AddonRegistry()
        def factory():
            addon = FakeAddon()
            self.instances.append(addon)
            return addon
        self.registry.register(factory)
        self.manager = AddonManager(self.registry)

    def test_enable_requires_explicit_permissions(self):
        with self.assertRaises(PermissionError):
            self.manager.enable("org.vdn.tests.fake")
        self.assertEqual(self.manager.running(), ())

    def test_lifecycle(self):
        self.manager.enable(
            "org.vdn.tests.fake",
            granted_permissions=frozenset({"host.metrics.read"}),
        )
        self.assertEqual(self.manager.running(), ("org.vdn.tests.fake",))
        self.manager.disable("org.vdn.tests.fake")
        self.assertEqual(self.manager.running(), ())
        self.assertEqual(
            [event[0] for event in self.instances[-1].events],
            ["register", "start", "stop", "unregister"],
        )

    def test_rejects_non_builtin_addons(self):
        class External:
            manifest = AddonManifest(
                addon_id="com.example.external", name="External",
                version="1", description="Not trusted", built_in=False,
            )
        with self.assertRaises(ValueError):
            self.registry.register(External)

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.register(FakeAddon)


if __name__ == "__main__":
    unittest.main()
