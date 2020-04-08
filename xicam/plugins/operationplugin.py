"""TODO Module docstring"""
import inspect
from typing import Collection, Tuple, Type, Union
from collections import namedtuple, OrderedDict

from pyqtgraph.parametertree.Parameter import PARAM_TYPES
from xicam.core import msg

from .hints import PlotHint


class OperationError(Exception):
    """Base exception for this module."""
    pass


class ValidationError(OperationError):
    """Exception raised for invalid OperationPlugin configurations.

    Attributes
    ----------
    operation : OperationPlugin
        Reference to the operation that failed its validation check.
    message : str
        Explanation of the error.
    """
    def __init__(self, operation, message):
        self.operation = operation
        self.message = message

    # def __repr__(self):
    #     return f"ValidationError({self.operation!r}, {self.message!r})"

    def __str__(self):
        """Returns a readable string for this exception."""
        return f"Validation failed for {self.operation}: {self.message}"


# TODO: make it so order of OperationPlugin decorator doesn't matter
class OperationPlugin:
    """A plugin that can be used to define an operation, which can be used in a Workflow.

    At its simplest level, an operation can be though of as a function.
    Any arguments (parameters) defined in the python function are treated as inputs for the operation.
    An operation's outputs are defined by the returned values of the python function.

    There are various methods available to help with modifying the operation's parameters.

    For more information on the attributes, see the documentation for their respective method
    (e.g. for more information on `limits`, see the `limits` method documentation).

    For an easy way to expose parameters in the GUI, use `OperationPlugin.as_parameter` in conjunction with
    `pyqtgraph.Parameter.create`.
    Note that only input parameters that have type hinting annotations will be included in the return value
    of `OperationPlugin.as_parameter`.

    Attributes
    ----------
    filled_values : dict
        Keys are the parameter names, values are the current values for the parameter.
    fixable : dict
        Keys are the parameter names, values are bools indicating whether or not the parameter
        is able to be fixed.
    fixed : dict
        Keys are the parameter names, values are bools indicating whether or not the parameter
        is fixed.
    input_names : Tuple[str, ...]
        Names (in order) of the input argument(s) for the operation. Note that if not provided,
        input names default to the argument names in the function signature.
    limits : dict
        Keys are the parameter names, values are the limits (which are a collection of floats).
    opts : dict
        Any additional options (kwargs) to be passed to the parameter (useful with pyqtgraph).
    output_names : Tuple[str, ...]
        Names (in order) of the output(s) for the operation.
    output_shape : dict
        Keys are the output parameter names, values are the expected shape of the output
        (which are of type list).
    units : dict
        Keys are the parameter names, values are units (of type str).
    visible : dict
        Keys are the pareameter names, values are bools indicating whehter or not the parameter
        is visible (when exposed using pyqtgraph).
    hints : list

    See Also
    --------
    xicam.core.execution.Workflow
    xicam.plugins.GUIPlugin

    Notes
    -----
    This class formally deprecates usage of the `ProcessingPlugin` API.

    Examples
    --------
    Here, we define a function, then wrap it with the OperationPlugin decorator to make it an operation.
    >>>@OperationPlugin\
    def my_operation(x: int, y: int):\
        return x + y

    """
    def __init__(self, func, filled_values=None, fixable: dict = None, fixed: dict = None, input_names: Tuple[str, ...] = None,
                 limits: dict = None, opts: dict = None, output_names: Tuple[str, ...] = None,
                 output_shape: dict = None, units: dict = None, visible: dict = None):
        """Create an Operation explicitly with __init__.

        Note that an OperationPlugin can be created by using the decorator `@OperationPlugin` (recommended)
        or using the constructor explicitly.
        When using the decorator, use the decorators provided in this module to set the operation's attributes.
        The `@OperationPlugin` decorator must be used before the attribute decorators.

        Parameters
        ----------
        func : Callable
            Function that this operation will call.
        filled_values : dict, optional
            Values to fill for the parameters.
        fixable : dict, optional
            Indicates which parameters are able to be fixed.
        fixed :  dict, optional
            Indicates whether or not a parameter is fixed.
        limits : dict, optional
            Defines limits for parameters.
        opts : dict, optional
            Additional options (kwargs) for the parameter
            (useful with pyqtgraph's Parameter/ParameterTree).
        output_names : tuple, optional
            Names for the outputs, or returned values, of the operation.
        output_shape : dict, optional
            Defines expected shapes for the outputs.
        units : dict, optional
            Defines units for the parameters in the operation.
        visible : dict, optional
            Indicates if a parameter is visible or not (see pyqtgraph.Parameter).
        """
        self._func = func
        self.name = getattr(func, 'name', getattr(func, '__name__', None))
        if self.name is None:
            raise NameError('The provided operation is unnamed.')
        # Allow passing a string
        if type(input_names) is str:
            input_names = (input_names,)
        # Fallback to inspecting the function arg names if no input names provided
        self.input_names = input_names or getattr(func,
                                                  'input_names',
                                                  tuple(inspect.signature(self._func).parameters.keys()))
        if type(output_names) is str:
            output_names = (output_names,)
        self.output_names = output_names or getattr(func, 'output_names', tuple())
        self.output_shape = output_shape or getattr(func, 'output_shape', {})
        self.filled_values = filled_values or {}
        self.limits = limits or getattr(func, 'limits', {})
        self.units = units or getattr(func, 'units', {})
        self.fixed = fixed or getattr(func, 'fixed', {})
        self.fixable = fixable or getattr(func, 'fixable', {})
        self.visible = visible or getattr(func, 'visible', {})
        self.opts = opts or getattr(func, 'opts', {})
        self.hints = getattr(func, 'hints', [])  # TODO: does hints need an arg

        self._validate()

    def _validate(self):
        """Validates the OperationPlugin's inputs and outputs."""

        # Capture any validation issues for use later when raising
        invalid_msg = ""
        # Define which "input" arg properties we want to check
        input_properties = {"fixable": self.fixable,
                            "fixed": self.fixed,
                            "limits": self.limits,
                            "opts": self.opts,
                            "units": self.units,
                            "visible": self.visible}
        # Check if all the attributes have a default value for each input param
        for arg in self.input_names:
            for name, prop in input_properties.items():
                if prop and arg not in prop:
                    pass    # Do we want to enforce input default values?

        # Check if there is a 1:1 mapping from user-specified input_names to function args
        num_names = len(self.input_names)
        num_args = len(inspect.signature(self._func).parameters.keys())
        if num_names != num_args:
            invalid_msg += (f"Number of input_names given ({num_names}) "
                            f"must match number of inputs for the operation ({num_args}).")
        # Check if there are any input args that are not actually defined in the operation
        # e.g. 'x' is not a valid input in the case below:
        # @visible('x')
        # def func(a): return
        for name, prop in input_properties.items():
            for arg in prop.keys():
                if arg not in self.input_names:
                    invalid_msg += f"\"{arg}\" is not a valid input for \"{name}\". "

        # Warn if there are no output_names defined
        if not len(self.output_names):
            warning_msg = (f"No output_names have been specified for your operation {self}; "
                           f"you will not be able to connect your operation's output(s) to "
                           f"any other operations.")
            msg.logMessage(warning_msg, level=msg.WARNING)

        # Define which "output" arg properties we want to check
        output_properties = {"output_shape": self.output_shape}
        # Check if there are any output args that are not actually defined in the operation
        for name, prop in output_properties.items():
            for arg in prop.keys():
                if arg not in self.output_names:
                    invalid_msg += f"\"{arg}\" is not a valid output for \"{name}\". "

        if invalid_msg:
            raise ValidationError(self, invalid_msg)
        else:
            msg.logMessage(f"All args for {self} are valid.")

    def __call__(self, **kwargs):
        """Allows this class to be used as a function decorator."""
        filled_kwargs = self.filled_values.copy()
        filled_kwargs.update(kwargs)
        return self._func(**filled_kwargs)

    def __str__(self):
        return f"OperationPlugin named {self.name}"

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

    def __reduce__(self):
        return OperationPlugin, (self._func,), {'filled_values': self.filled_values,
                                                'input_names': self.input_names,
                                                'output_names': self.output_names}

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


def display_name(name):
    """Set the display name for the operation.

    Display name is how this operation's name will be displayed in Xi-cam.

    Parameters
    ----------
    name : str
        Name for the operation.

    Examples
    --------
    Create an operation whose display name is "Cube Operation."

    >>>@OperationPlugin\
    @display_name('Cube Operation')\
    def cube(n: int) -> int:\
        return n**3
    """
    def decorator(func):
        func.name = name
        return func
    return decorator


def units(arg_name, unit):
    """Decorator to define units for an input.

    Associates a unit of measurement with an input.

    Parameters
    ----------
    arg_name : str
        Name of the input to attach a unit to.
    unit : str
        Unit of measurement descriptor to use (e.g. "mm").

    Examples
    --------
    Create an operation where its `x` parameter has its units defined in microns.

    >>>@OperationPlugin\
    @units('x', '\u03BC'+'m')\
    def op(x:float) -> float:\
        ...
    """
    def decorator(func):
        _quick_set(func, 'units', arg_name, unit, {})
        return func

    return decorator


def fixed(arg_name, fix=True):
    #TODO is this a toggleable 'lock' on the parameter's value?
    """Decorator to set whether or not an input's value is fixed.

    By default, sets the `arg_name` input to fixed, meaning its value cannot
    be changed.

    Parameters
    ----------
    arg_name : str
        Name of the input to change fix-state for.
    fix : bool, optional
        Whether or not to fix `arg_name` (default is True).

    TODO example
    """
    def decorator(func):
        _quick_set(func, 'fixed', arg_name, fix, {})
        return func

    return decorator


def limits(arg_name, limit):
    """Decorator to define limits for an input.

    Limits restrict the allowable values for the input
    (inclusive lower-bound, inclusive upper-bound).

    Parameters
    ----------
    arg_name : str
        Name of the input to define limits for.
    limit : tuple[float]
        A 2-element sequence representing the lower and upper limit.

    Examples
    --------
    Make an operation that has a limit on the `x` parameter from [0, 100].

    >>>@OperationPlugin\
    @limits('x', [0, 100])\
    def op(x):\
        ...

    Make an operation that has a limit on the `x` parameter from [0.0, 1.0].

    >>>@OperationPlugin\
    @limits('x', [0.0, 1.0])\
    @opts('x', step=0.1)\
    def op(x):\
        ...

    """
    def decorator(func):
        _quick_set(func, 'limits', arg_name, limit, {})
        return func

    return decorator


# TODO: need an image_hint decorator? coplot_hint decorator?

def plot_hint(*args, **kwargs):
    """Decorator to define plot hints for 1-dimensional outputs.

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


def input_names(*names):
    """Decorator to define input names for the operation.

    The number of names provided must match the number of arguments for the operation/function.

    If not provided, input names will be determined by examining the names of the arguments
    to the operation function.

    Examples
    --------
    Create an addition operation and use the names "first" and "second" for the input names
    instead of the function arg names (x and y).

    >>>@OperationPlugin\
    @input_names("first", "second")\
    def my_add(x, y):\
        return x + y
    """
    def decorator(func):
        func.input_names = names
        return func
    return decorator


def output_names(*names):
    """Decorator to define the names of the outputs for an operation.

    Defines N-number of output names. These names will be used (in-order)
    to define any outputs that the operation has.

    Parameters
    ----------
    names : str (any number of strings separated by comma)
        Names for the outputs in the operation.

    Examples
    --------
    Define an operation that has the outputs `x` and `y`.

    >>>@OperationPlugin\
    @output_names("x", "y")\
    def some_operation(a: int, b: int):\
        return a, b

    """
    def decorator(func):
        func.output_names = names
        return func

    return decorator


def output_shape(arg_name, shape: Union[int, Collection[int]]):
    # TODO: how does this work? How do we know the shape before runtime?
    """Decorator to set the shape of an output in an operation."

    Parameters
    ----------
    arg_name : str
        Name of the output to define a shape for.
    shape : int or tuple of ints
        N-element tuple representing the shape (dimensions) of the output.

    Examples
    --------
    TODO
    """
    def decorator(func):
        _quick_set(func, 'output_shape', arg_name, shape, {})
        return func

    return decorator


def visible(arg_name, is_visible=True):
    """Decorator to set whether an input is visible (shown in GUI) or not.

    Parameters
    ----------
    arg_name : str
        Name of the input to change visibility for.
    is_visible : bool, optional
        Whether or not to make the input visible or not (default is True).

    Examples
    --------
    Define an operation that makes the data_image invisible to the GUI (when using `as_parameter()` and pyqtgraph).

    >>>@OperationPlugin\
    @visible('data_image')\
    def threshold(data_image: np.ndarray, threshold: float = 0.5) -> np.ndarray:\
        return ...

    """
    def decorator(func):
        _quick_set(func, 'visible', arg_name, is_visible, {})
        return func
    return decorator


def opts(arg_name, **options):
    """Decorator to set the opts (pyqtgraph Parameter opts) for `arg_name`.

    This is useful for attaching any extra attributes onto an operation input argument.

    These options correspond to the optional opts expected by pyqtgraph.Parameter.
    The options are typically used to add extra configuration to a Parameter.

    Parameters
    ----------
    arg_name : str
        Name of the input to add options for.
    options : keyword args
        Keyword arguments that can be used for the rendering backend (pyqtgraph).

    Examples
    --------
    Define an operation where the `x` input is readonly.

    >>>@OperationPlugin\
    @opts('x', 'readonly'=True)\
    def op(x: str = 100) -> str:\
        return x
    """
    def decorator(func):
        _quick_set(func, 'opts', arg_name, options, {})
        return func
    return decorator
