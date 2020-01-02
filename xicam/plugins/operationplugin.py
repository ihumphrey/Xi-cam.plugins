# from .hints import PlotHint
import inspect


class OperationPlugin():
    def __init__(self, func):
        self._func = func
        self._output_names = tuple()

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

# def set_or_init(func, attribute_name, value, default):
#     attr = getattr(func, attribute_name, default)
#     attr[attribute_name]


def input_only(arg_name):
    def decorator(func):
        accepts_output = getattr(func, '_accepts_output', {})
        accepts_output[arg_name] = False
        func._accepts_output = accepts_output
    return decorator


def output_only(arg_name):
    def decorator(func):
        accepts_input = getattr(func, '_accepts_input', {})
        accepts_input[arg_name] = False
        func._accepts_input = accepts_input
    return decorator

# There shouldn't be more than one way to do things, let's not provide default decorator
# def default(arg_name, value):
#     def decorator(func):
#         index = func.func_code.co_varnames.index(arg_name)
#         func.func_defaults[index] = value
#     return decorator


def dtype(argname, type):
    ...


def plothint(*args, **kwargs):
    def decorator(func):
        func._hints.append(PlotHint(*args, **kwargs))
    return decorator


def output_names(*names):
    def decorator(func):
        func._output_names = names
        return func
    return decorator


def output_shape(name, shape):
    def decorator(func):
        func._output_shape[name]


def test_output_names():
    import numpy
    @output_names('sum')
    def sum(a, b):
        return numpy.sum(a, b)

    assert sum._output_names == ('sum',)


def test_common_interface():
    def sum(a, b):
        return numpy.sum(a, b)

    op = OperationPlugin(sum)

    assert op.inputs ==


if __name__ == '__main__':
    test_output_names()
    test_input_names()