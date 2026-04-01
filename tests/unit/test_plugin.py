"""Tests for the plugin system."""

from bulbe.core.plugin import (
    PLUGIN_CATEGORIES,
    PluginRegistry,
    bulbe_plugin,
    register_plugin,
)


class TestPluginRegistry:
    def setup_method(self):
        PluginRegistry.reset()

    def test_singleton(self):
        r1 = PluginRegistry.get()
        r2 = PluginRegistry.get()
        assert r1 is r2

    def test_reset(self):
        r1 = PluginRegistry.get()
        PluginRegistry.reset()
        r2 = PluginRegistry.get()
        assert r1 is not r2

    def test_register_and_get(self):
        class MyScheduler:
            name = "test"

        registry = PluginRegistry.get()
        registry.register("scheduler", "test", cls=MyScheduler)

        plugin = registry.get_plugin("scheduler", "test")
        assert isinstance(plugin, MyScheduler)
        assert plugin.name == "test"

    def test_lazy_instantiation(self):
        call_count = 0

        class ExpensivePlugin:
            name = "expensive"

            def __init__(self):
                nonlocal call_count
                call_count += 1

        registry = PluginRegistry.get()
        registry.register("scheduler", "expensive", cls=ExpensivePlugin)
        assert call_count == 0  # Not instantiated yet

        registry.get_plugin("scheduler", "expensive")
        assert call_count == 1  # Instantiated on first access

        registry.get_plugin("scheduler", "expensive")
        assert call_count == 1  # Cached

    def test_invalid_category(self):
        registry = PluginRegistry.get()
        try:
            registry.register("invalid_category", "test", cls=object)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unknown plugin category" in str(e)

    def test_get_nonexistent(self):
        registry = PluginRegistry.get()
        try:
            registry.get_plugin("scheduler", "nonexistent")
            assert False, "Should raise KeyError"
        except KeyError:
            pass

    def test_has_plugin(self):
        registry = PluginRegistry.get()
        assert not registry.has_plugin("scheduler", "test")

        registry.register("scheduler", "test", cls=object)
        assert registry.has_plugin("scheduler", "test")

    def test_list_plugins(self):
        registry = PluginRegistry.get()
        registry.register("scheduler", "slurm", cls=object)
        registry.register("scheduler", "pbs", cls=object)
        registry.register("sweep", "scaling", cls=object)

        all_plugins = registry.list_plugins()
        assert len(all_plugins) == 3

        schedulers = registry.list_plugins("scheduler")
        assert len(schedulers) == 2

        sweeps = registry.list_plugins("sweep")
        assert len(sweeps) == 1


class TestBulbePluginDecorator:
    def setup_method(self):
        PluginRegistry.reset()

    def test_decorator_with_name(self):
        @bulbe_plugin("scheduler", "my_scheduler")
        class MyScheduler:
            name = "my_scheduler"

        registry = PluginRegistry.get()
        assert registry.has_plugin("scheduler", "my_scheduler")

    def test_decorator_default_name(self):
        @bulbe_plugin("sweep")
        class FrequencySweep:
            name = "FrequencySweep"

        registry = PluginRegistry.get()
        assert registry.has_plugin("sweep", "FrequencySweep")

    def test_register_plugin_imperative(self):
        class MyPlugin:
            name = "imperative"

        register_plugin("analysis", "imperative", MyPlugin)
        registry = PluginRegistry.get()
        assert registry.has_plugin("analysis", "imperative")
