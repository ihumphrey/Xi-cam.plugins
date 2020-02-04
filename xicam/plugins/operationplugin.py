# from .hints import PlotHint
import inspect
import weakref
from pyqtgraph.parametertree.Parameter import Parameter, PARAM_TYPES
from functools import partial
from typing import Tuple, Dict, Type
from collections import OrderedDict

from .hints import PlotHint


# TODO: make it so order of OperationPlugin decorator doesn't matter

class OperationPlugin:

    def __init__(self, func, filled_values=None, output_names: Tuple[str] = None, limits: dict = None,
                 fixed: dict = None, fixable: dict = None, visible: dict = None, opts: dict = None, units: dict = None):
        self._func = func
        self.name = getattr(func, 'name', getattr(func, '__name__', None))
        if self.name is None:
            raise NameError('The provided operation is unnamed.')
        self.output_names = output_names or getattr(func, '_output_names', tuple())

        self.disabled = False
        self.filled_values = filled_values or {}
        self.limits = limits or getattr(func, '_limits', {})
        self.units = units or getattr(func, '_units', {})
        self.fixed = fixed or {}
        self.fixable = fixable or {}
        self.visible = visible or {}
        self.opts = opts or {}
        self.hints = []

    def __call__(self, **kwargs):
        filled_kwargs = self.filled_values.copy()
        filled_kwargs.update(kwargs)
        return self._func(**filled_kwargs)

    @property
    def input_types(self) -> 'OrderedDict[str, Type]':
        signature = inspect.signature(self._func)
        input_type_map = OrderedDict([(name, parameter.annotation) for name, parameter in signature.parameters.items()])
        return input_type_map

    @property
    def output_types(self) -> 'OrderedDict[str, Type]':
        return_annotation = inspect.signature(self._func).return_annotation
        if not return_annotation or return_annotation is inspect._empty:
            return_annotation = tuple()

        if type(return_annotation) is not tuple:
            return_annotation = (return_annotation,)

        output_type_map = OrderedDict(zip(self.output_names, return_annotation))
        return output_type_map

    @property
    def input_names(self):
        return tuple(inspect.signature(self._func).parameters.keys())

    def __reduce__(self):
        return OperationPlugin, (self._func, self.filled_values, self.output_names)

    def as_parameter(self):
        parameter_dicts = []
        for name, parameter in inspect.signature(self._func).parameters.items():
            if getattr(parameter.annotation, '__name__', None) in PARAM_TYPES:
                parameter_dict = dict()
                parameter_dict.update(self.opts.get(name, {}))
                parameter_dict['name'] = name
                parameter_dict['default'] = parameter.default if parameter.default is not inspect._empty else None
                parameter_dict['value'] = self.filled_values[
                    name] if name in self.filled_values else parameter_dict['default']

                parameter_dict['type'] = getattr(self.input_types[name], '__name__', None)
                if name in self.limits:
                    parameter_dict['limits'] = self.limits[name]
                parameter_dict['units'] = self.units.get(name)
                parameter_dict['fixed'] = self.fixed.get(name)
                parameter_dict['fixable'] = self.fixable.get(name)
                parameter_dict['visible'] = self.visible.get(name, True)

                parameter_dicts.append(parameter_dict)

            elif getattr(self.input_types[name], "__name__", None) == "Enum":
                parameter_dict = dict()
                parameter_dict['name'] = name
                parameter_dict['value'] = self.filled_values[
                    name] if name in self.filled_values else parameter.default
                parameter_dict['values'] = self.limits.get(name) or ["---"],
                parameter_dict['default'] = parameter.default
                parameter_dict['type'] = "list",
                if name in self.limits:
                    parameter_dict['limits'] = self.limits[name]
                parameter_dict['units'] = self.units.get(name)
                parameter_dict['fixed'] = self.fixed.get(name)
                parameter_dict['fixable'] = self.fixable.get(name)
                parameter_dict['visible'] = self.visible.get(name, True)

                parameter_dicts.append(parameter_dict)
        return parameter_dicts


def _quick_set(func, attr_name, key, value, init):
    if not hasattr(func, attr_name):
        setattr(func, attr_name, init)
    getattr(func, attr_name)[key] = value


def units(arg_name, unit):
    def decorator(func):
        _quick_set(func, '_units', arg_name, unit, {})

    return decorator


def fixed(arg_name, fix=True):
    def decorator(func):
        _quick_set(func, '_fixed', arg_name, fix, {})

    return decorator


def input_only(arg_name, value=True):
    def decorator(func):
        _quick_set(func, '_accepts_output', arg_name, not value, {})

    return decorator


def output_only(arg_name, value=True):
    def decorator(func):
        _quick_set(func, '_accepts_input', arg_name, not value, {})

    return decorator


def limits(arg_name, limit):
    def decorator(func):
        _quick_set(func, '_limits', arg_name, limit, {})

    return decorator


def plot_hint(*args, **kwargs):
    def decorator(func):
        if not hasattr(func, '_hints'):
            func._hints = []
        func._hints.append(PlotHint(*args, **kwargs))

    return decorator


def output_names(*names):
    def decorator(func):
        func._output_names = names
        return func

    return decorator


def output_shape(arg_name, shape):
    def decorator(func):
        _quick_set(func, '_output_shape', arg_name, shape, {})

    return decorator
