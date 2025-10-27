from __future__ import annotations

import logging
import os
import sys
from importlib import import_module
from types import ModuleType
from logging import warning

from linkml_runtime.utils.compile_python import file_text

logger = logging.getLogger('dump_things_service')


def patched_compile_python(
        text_or_fn: str,
        package_path: str | None = None,
        module_name: str = 'test'
) -> ModuleType:
    """
    Compile the text or file and return the resulting module'test'
    @param text_or_fn: Python text or file name that references python file
    @param package_path: Root package path.  If omitted and we've got a python file, the package is the containing
    directory
    @return: Compiled module
    """
    python_txt = file_text(text_or_fn)
    if package_path is None and python_txt != text_or_fn:
        package_path = text_or_fn
    spec = compile(python_txt, module_name, 'exec')
    module = ModuleType(module_name)
    if package_path:
        package_path_abs = os.path.join(os.getcwd(), package_path)
        # We have to calculate the path to expected path relative to the current working directory
        for path in sys.path:
            if package_path.startswith(path):
                path_from_tests_parent = os.path.relpath(package_path, path)
                break
            if package_path_abs.startswith(path):
                path_from_tests_parent = os.path.relpath(package_path_abs, path)
                break
        else:
            warning(f"There is no established path to {package_path} - compile_python may or may not work")
            path_from_tests_parent = os.path.relpath(package_path, os.path.join(os.getcwd(), '..'))
        module.__package__ = os.path.dirname(os.path.relpath(path_from_tests_parent, os.getcwd())).replace(os.path.sep, '.')
    sys.modules[module.__name__] = module
    exec(spec, module.__dict__)
    return module


def patched_compile_module(self, module_name, **kwargs) -> ModuleType:
    """
    Compiles generated python code to a module
    :return:
    """
    pycode = self.serialize(**kwargs)
    try:
        return patched_compile_python(pycode, module_name=module_name)
    except NameError as e:
        logger.error(f"Code:\n{pycode}")
        logger.error(f"Error compiling generated python code: {e}")
        raise e


logger.info('patching linkml.generators.pydanticgen.pydanticgen.PydanticGenerator.compile_module')

mod = import_module('linkml.generators.pydanticgen.pydanticgen')
mod.PydanticGenerator.compile_module = patched_compile_module
