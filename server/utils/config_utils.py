from typing import Any, Dict
import importlib


def instantiate(obj_cfg: Dict, recursive: bool = True) -> Any:
    """Insantiates object from config dictionary

    If recursive, will instantiate any children in-place

    Parameters
    ----------
    obj_cfg : Dict
        config dictionary to instantiate object from
    recursive : bool, optional
        if should recursively instantiate, by default True

    Returns
    -------
    Any
        instantiated object, created from dict config

    Raises
    ------
    ValueError
        If no '_target_' directive in object config
    ModuleNotFoundError
        If module does not exist
    AttributeError
        If callable does not exist in module
    """
    # determine if object config is instantiable
    if not can_instantiate(obj_cfg):
        raise ValueError("No '_target_' directive in object config, cannot instantiate")

    # get module, class names
    target_module, target_class = obj_cfg["_target_"].rsplit(".", 1)

    # get callable object
    obj_callable = getattr(importlib.import_module(target_module), target_class)

    # get kwargs dict
    kwargs_dict = obj_cfg
    del kwargs_dict["_target_"]

    # recursively instantiate configs
    if recursive:
        for kwarg_name, kwarg_val in kwargs_dict.items():
            if isinstance(kwarg_val, dict) and can_instantiate(kwarg_val):
                kwargs_dict[kwarg_name] = instantiate(kwarg_val, recursive=recursive)

    # return object
    return obj_callable(**kwargs_dict)


def can_instantiate(obj_cfg: Dict) -> bool:
    """Returns true if '_target_' directive exists in object config

    Parameters
    ----------
    obj_cfg : Dict
        object config to determine if instantiable

    Returns
    -------
    bool
        if the object config is instantiable
    """
    return "_target_" in obj_cfg
