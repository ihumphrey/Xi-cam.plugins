# from .hints import PlotHint
import inspect
import weakref
from pyqtgraph.parametertree.Parameter import Parameter, PARAM_TYPES
from functools import partial
from typing import Collection, Dict, List, Tuple, Type, Union
from collections import OrderedDict

from xicam.core import msg

from .hints import PlotHint


# TODO: make it so order of OperationPlugin decorator doesn't matter

class OperationPlugin:
    """A plugin that can be used to define an operation, which can be used in a Workflow.

    At its simplest level, an operation can be though of as a function.
    An operation essentially wraps a python function definition.
    Any arguments (parameters) defined in the python function are treated as inputs for the operation.
    An operation's outputs are defined by the returned values of the python function.

    TODO example usage? usage within workflow?

    Attributes
    ----------
    disabled
    filled_values
    fixable
    fixed
    hints
    limits
    name
    opts
    output_names
    units
    visible

    Methods
    -------

    See Also
    --------
    (Workflow) TODO Fill in ref correctly
    (GUIPlugin) TODO fill in ref correctly

    Notes
    -----
    This class formally deprecates usage of the `ProcessingPlugin` API.

    Examples
    --------
    """

    def __init__(self, func, filled_values=None, output_names: Tuple[str, ...] = None, limits: dict = None,
                 fixed: dict = None, fixable: dict = None, visible: dict = None, opts: dict = None, units: dict = None,
                 output_shape: dict = None):
        self._func = func
        self.name = getattr(func, 'name', getattr(func, '__name__', None))
        if self.name is None:
            raise NameError('The provided operation is unnamed.')
        self.output_names = output_names or getattr(func, 'output_names', tuple())
        self.output_shape = output_shape or getattr(func, 'output_shape', {})

        self.disabled = False  # TODO: does this need a setter for more explicit API?
        self.filled_values = filled_values or {}  # TODO: what is the purpose of filled_values?
        self.limits = limits or getattr(func, 'limits', {})
        self.units = units or getattr(func, 'units', {})
        self.fixed = fixed or getattr(func, 'fixed', {})
        self.fixable = fixable or getattr(func, 'fixable', {})
        self.visible = visible or getattr(func, 'visible', {})
        self.opts = opts or getattr(func, 'opts', {})
        self.hints = getattr(func, 'hints', [])  # TODO: does hints need an arg

        self._validate()

    def _validate(self):
        invalid_msg = ""
        # TODO make this an actual property?
        input_properties = {"fixable": self.fixable,
                            "fixed": self.fixed,
                            "limits": self.limits,
                            "opts": self.opts,
                            "units": self.units,
                            "visible": self.visible}
        # Ensure all the referenced parameters in the operation's state are part of the operation
        # TODO: this checks if all the properties have default values for each input param. Do we want this?
        for arg in self.input_names:
            for name, prop in input_properties.items():
                if prop and arg not in prop:
                    pass  # print(f"{name}: {prop}")  # TODO: this passes...

        # Check if there are any input args that are not actually defined in the operation
        # e.g. 'x' is not a valid input in the case below:
        # @visible('x')
        # def func(a): return
        for name, prop in input_properties.items():
            for arg in prop.keys():
                if arg not in self.input_names:
                    invalid_msg += f"\"{arg}\" is not a valid input for \"{name}\". "

        # Check if there are any output args that are not actually defined in the operation
        output_properties = {"output_shape": self.output_shape}
        for name, prop in output_properties.items():
            for arg in prop.keys():
                if arg not in self.output_names:
                    invalid_msg += f"\"{arg}\" is not a valid output for \"{name}\". "

        if invalid_msg:
            raise TypeError(f"Validation for operation named \"{self.name}\" failed: " + invalid_msg)
        else:
            msg.logMessage(f"All args for operation \"{self.name}\" are valid.")

    def __call__(self, **kwargs):
        filled_kwargs = self.filled_values.copy()
        filled_kwargs.update(kwargs)
        return self._func(**filled_kwargs)

    @property
    def input_types(self) -> 'OrderedDict[str, Type]':
        """Returns the types of the inputs for the operation."""
        signature = inspect.signature(self._func)
        input_type_map = OrderedDict([(name, parameter.annotation) for name, parameter in signature.parameters.items()])
        return input_type_map

    @property
    def output_types(self) -> 'OrderedDict[str, Type]':
        """Returns the types of the outputs for the operation."""
        return_annotation = inspect.signature(self._func).return_annotation
        if not return_annotation or return_annotation is inspect.Signature.empty:
            return_annotation = tuple()

        if type(return_annotation) is not tuple:
            return_annotation = (return_annotation,)

        output_type_map = OrderedDict(zip(self.output_names, return_annotation))
        return output_type_map

    @property
    def input_names(self):
        """Returns the names of the inputs in the operation."""
        return tuple(inspect.signature(self._func).parameters.keys())

    def __reduce__(self):
        return OperationPlugin, (self._func, self.filled_values, self.output_names)

    def as_parameter(self):
        """Return the operation's inputs as a ready-to-use object with pyqtgraph.

        A list of dictionaries is returned with each dictionary representing one of the operation's input parameters.
        Each dictionary represents the state of the input parameter;
        for example, its name, its default value, its type, etc.
        Note that only inputs that have been annotated with type-hinting
        and whose types are registered with pyqtgraph (PARAM_TYPES) will be included in this list.
        This list can be passed to `pyqtgraph.Parameter.create` to create a parameter tree widget.

        Alternative text:
        A list of dictionaries is returned where each dict is a best-effort attempt to represent each input parameter as a pyqtgraph Parameter.

        Returns
        -------
        parameters : list
            List of dictionaries; each dictionary represents the state of an input parameter
            (only applies to input parameters that are annotated with type-hinting).

        See Also
        --------
        For more information about pyqtgraph, see _Parameter.create.

        .. _Parameter.create: http://www.pyqtgraph.org/documentation/parametertree/parameter.html?highlight=create#pyqtgraph.parametertree.Parameter.create

        """
        parameter_dicts = []
        for name, parameter in inspect.signature(self._func).parameters.items():
            if getattr(parameter.annotation, '__name__', None) in PARAM_TYPES:
                parameter_dict = dict()
                parameter_dict.update(self.opts.get(name, {}))
                parameter_dict['name'] = name
                parameter_dict['default'] = parameter.default if parameter.default is not inspect.Parameter.empty else None
                parameter_dict['value'] = self.filled_values[
                    name] if name in self.filled_values else parameter_dict['default']

                parameter_dict['type'] = getattr(self.input_types[name], '__name__', None)
                if name in self.limits:
                    parameter_dict['limits'] = self.limits[name]
                parameter_dict['units'] = self.units.get(name)
                parameter_dict['fixed'] = self.fixed.get(name)
                parameter_dict['fixable'] = self.fixable.get(name)
                parameter_dict['visible'] = self.visible.get(name, True)
                parameter_dict.update(self.opts.get(name, {}))

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
                parameter_dict['fixed'] = self.fixed.get(name)  # TODO: Does this need a default value
                parameter_dict['fixable'] = self.fixable.get(name)
                parameter_dict['visible'] = self.visible.get(name, True)  # TODO: should we store the defaults at top?
                parameter_dict.update(self.opts.get(name, {}))

                parameter_dicts.append(parameter_dict)
        return parameter_dicts


def _quick_set(func, attr_name, key, value, init):
    # TODO: does this need to be called initially to provide valid defaults?
    if not hasattr(func, attr_name):
        setattr(func, attr_name, init)
    getattr(func, attr_name)[key] = value


def units(arg_name, unit):
    """Define units for an input.

    Associates a unit of measurement with an input.

    Parameters
    ----------
    arg_name : str
        Name of the input to attach a unit to.
    unit : str
        Unit of measurement descriptor to use (e.g. "mm").
    """
    def decorator(func):
        _quick_set(func, 'units', arg_name, unit, {})
        return func

    return decorator


def fixed(arg_name, fix=True):
    """Set whether or not an input's value is fixed.

    By default, sets the `arg_name` input to fixed, meaning its value cannot
    be changed.

    Parameters
    ----------
    arg_name : str
        Name of the input to change fix-state for.
    fix : bool, optional
        Whether or not to fix `arg_name` (default is True).
    """
    def decorator(func):
        _quick_set(func, 'fixed', arg_name, fix, {})
        return func

    return decorator


def limits(arg_name, limit):
    """Define limits for an input.

    Limits restrict the allowable values for the input
    (inclusive lower-bound, inclusive upper-bound).

    Parameters
    ----------
    arg_name : str
        Name of the input to define limits for.
    limit : tuple[float]
        A 2-element sequence representing the lower and upper limit.
    """
    def decorator(func):
        _quick_set(func, 'limits', arg_name, limit, {})
        return func

    return decorator


# TODO: need an image_hint decorator? coplot_hint decorator?

def plot_hint(*args, **kwargs):
    """Defines plot hints for 1-dimensional outputs.

    Parameters
    ----------
    args
        Arguments for `PlotHint`.
    kwargs
        Keyword arguments for `PlotHint`.

    TODO examples may be helpful in these...
    """
    def decorator(func):
        if not hasattr(func, 'hints'):
            func.hints = []
        func.hints.append(PlotHint(*args, **kwargs))
        return func

    return decorator


def output_names(*names):
    """Define the names of the outputs for the operation.

    Defines N-number of output names. These names will be used (in-order)
    to define any outputs that the operation has.

    Parameters
    ----------
    names : str (any number of strings separated by comma)
        Names for the outputs in the operation.

    """
    def decorator(func):
        func.output_names = names
        return func

    return decorator


def output_shape(arg_name, shape: Union[int, Collection[int]]):
    """

    Parameters
    ----------
    arg_name : str
        Name of the output to define a shape for.
    shape : int or tuple of ints
        N-element tuple representing the shape (dimensions) of the output.
    """
    def decorator(func):
        _quick_set(func, 'output_shape', arg_name, shape, {})
        return func

    return decorator


def visible(arg_name, is_visible):
    """Set whether an input is visible (shown in GUI) or not.

    Parameters
    ----------
    arg_name : str
        Name of the input to change visibility for.
    is_visible : bool, optional
        Whether or not to make the input visible or not (default is True).
    """
    def decorator(func):
        _quick_set(func, 'visible', arg_name, is_visible, {})
        return func
    return decorator


def opts(arg_name, options):
    """Set the opts (pyqtgraph Parameter opts) for `arg_name`.

    TODO: more details

    Parameters
    ----------
    arg_name : str
        Name of the input to change options for.
    options : dict
        Dictionary of options that can be used for the rendering backend (pyqtgraph).
    """
    def decorator(func):
        _quick_set(func, 'opts', arg_name, options, {})
        return func
    return decorator
