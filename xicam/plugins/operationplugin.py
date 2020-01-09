# from .hints import PlotHint
import inspect
import weakref
from pyqtgraph.parametertree.Parameter import Parameter, PARAM_TYPES
from functools import partial
from typing import Tuple, Dict, Type
from collections import OrderedDict


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

    def __call__(self, **kwargs):
        filled_kwargs = self.filled_values.copy()
        filled_kwargs.update(kwargs)
        return self._func(**filled_kwargs)

    @property
    def input_types(self) -> 'OrderedDict[str, Type]':
        signature = inspect.signature(self._func)
        input_type_map = signature.parameters
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


def as_parameter(operation: OperationPlugin):
    parameter_dicts = []
    for name, parameter in inspect.signature(operation._func).parameters.items():
        if getattr(parameter.annotation, '__name__', None) in PARAM_TYPES:
            parameter_dict = dict(name=name,
                                  value=operation.filled_values[
                                      name] if name in operation.filled_values else parameter.default,
                                  default=parameter.default,
                                  limits=operation.limits[name],
                                  type=getattr(operation.input_types[name],
                                               '__name__',
                                               None),
                                  units=operation.units['name'],
                                  fixed=operation.fixed['name'],
                                  fixable=operation.fixable['name'],
                                  visible=operation.visible['name'],
                                  **operation.opts['name'])
            parameter_dicts.append(parameter_dict)
        elif getattr(operation.input_types[name], "__name__", None) == "Enum":
            parameter_dict = Parameter.create(
                name=name,
                value=operation.filled_values[
                    name] if name in operation.filled_values else parameter.default,
                values=operation.limits[name] or ["---"],
                default=parameter.default,
                type="list",
            )
            parameter_dicts.append(parameter_dict)


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
