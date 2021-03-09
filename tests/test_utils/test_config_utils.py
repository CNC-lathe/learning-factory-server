from collections import deque, UserString
import unittest

from server.utils import instantiate


class TestConfigUtils(unittest.TestCase):
    """Tests methods of config_utils module"""
    def test_instantiate_no_target(self):
        """Tests instantiate method, where object config has no _target_ directive"""
        # create test configs
        test_configs = [
            {},
            {"a": 1, "b": 2}
        ]

        # check that instantiate raises ValueError for each test config
        for test_conf in test_configs:
            self.assertRaises(ValueError, instantiate, test_conf)

    def test_instantiate_non_existent_module(self):
        """Tests instantiate method, where target module doesn't exist"""
        # create test configs
        test_configs = [
            {"_target_": "non_existent_module.some_class"},
            {"_target_": "another_non_existent_module.some_class", "a": 1, "b": 2}
        ]

        # check that instantiate raises ModuleNotFoundError for each test config
        for test_conf in test_configs:
            self.assertRaises(ModuleNotFoundError, instantiate, test_conf)

    def test_instantiate_non_existent_class(self):
        """Tests instantiate method, where target class doesn't exist"""
        # create test configs
        test_configs = [
            {"_target_": "collections.NonExistentClass"},
            {"_target_": "collections.OtherNonExistentClass", "a": 1, "b": 2}
        ]

        # check that instantiate raises AttributeError for each test config
        for test_conf in test_configs:
            self.assertRaises(AttributeError, instantiate, test_conf)

    def test_instantiate_valid_target(self):
        """Tests instantiate method with valid target module and class"""
        # create test configs
        test_configs = [
            {"_target_": "collections.deque"},
            {"_target_": "collections.UserString", "seq": "test string"}
        ]

        # create truth objects
        truth_objs = [deque(), UserString("test string")]

        # check that instantiate returns truth object for each config
        for truth_obj, test_config in zip(truth_objs, test_configs):
            self.assertEqual(truth_obj, instantiate(test_config))
