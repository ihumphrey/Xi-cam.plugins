from xicam.plugins import OperationPlugin
from xicam.plugins.operationplugin import (fixed, limits, opts, output_names,
                                           output_shape, plot_hint, units, visible)


class TestFixed:

    def test_none(self):
        def func(a, b):
            return

        # assert func.fixed == {}
        assert not hasattr(func, 'fixed')

    def test_one(self):
        @fixed('a')
        def func(a, b):
            return
        assert func.fixed == {'a': True}

    def test_multiple(self):
        @fixed('a')
        @fixed('b')
        def func(a, b, c):
            return
        assert func.fixed == {'a': True, 'b': True}

    def test_explicit(self):
        @fixed('a', True)
        @fixed('b', False)
        def func(a, b, c):
            return
        assert func.fixed == {'a': True, 'b': False}

    def test_redundant(self):
        @fixed('b')
        @fixed('b')
        def func(a, b, c):
            return
        assert func.fixed == {'b': True}

    def test_no_parameter_with_name(self):
        @fixed('dne')
        def func(a, b, c):
            return
        # TODO: what should this do? Should there be checking here?
        assert func.fixed == {'dne': True}

    def test_bad(self):
        # TODO: do we need to test unexpected types?
        @fixed(3)
        def func(a):
            return
        assert True


def test_limits():
    @limits('a', [0.0, 1.0])
    def func(a):
        return
    assert func.limits == {'a': [0.0, 1.0]}


def test_output_names():
    import numpy
    @output_names('sum')
    def sum(a, b):
        return numpy.sum(a, b)

    assert sum.output_names == ('sum',)


def test_output_shape():
    # TODO: what should the expected shape be? A collection (list/tuple)?
    import numpy as np
    @output_shape('out', (10, 10))
    def func(a) -> np.ndarray:
        return np.zeros(shape=(10, 10))
    assert func.output_shape == {'out': (10, 10)}


# def test_plot_hint():
#     print('tlaktj')
#     assert False, 'bnlah'


def test_units():
    @units('a', 'mm')
    def func(a):
        return
    assert func.units == {'a': 'mm'}


class TestVisible:
    def test_default(self):
        # TODO: what should this return?
        @output_names('z')
        def func(a):
            return
        # assert func.visible == {'a': True}  # Expects a default to be set regardless
        assert not hasattr(func, 'visible')        # does not expect any defaults to be set; must be explicit

    def test_true(self):
        @visible('a', True)
        def func(a, b):
            return
        assert func.visible == {'a': True}

    def test_false(self):
        @visible('a', False)
        def func(a, b):
            return
        assert func.visible == {'a': False}


def test_opts():
    # TODO: what happens if you pass in an 'invalid' opt? what is an invalid opt?
    @opts('a', someopt='opt')
    def func(a, b):
        return
    assert func.opts == {'a': {'someopt': 'opt'}}


def test_as_parameter():
    @OperationPlugin
    @fixed('fixed_param')
    @limits('limits_param', [0, 100])
    @opts('opts_param', opt='value')
    @output_names('out1', 'out2')
    @output_shape('out1', [1])
    @units('units_param', 'km')
    @visible('invisible_param', False)
    def func(fixed_param: int,
             invisible_param: int,
             limits_param: int,
             opts_param: list,
             units_param: float,
             unseen_param,
             default_param: int = 0):
        return

    expected_as_parameter = [{'default': None,
                              'fixable': None,
                              'fixed': True,
                              'name': 'fixed_param',
                              'type': 'int',
                              'units': None,
                              'value': None,
                              'visible': True},
                             {'default': None,
                              'fixable': None,
                              'fixed': None,
                              'name': 'invisible_param',
                              'type': 'int',
                              'units': None,
                              'value': None,
                              'visible': False},
                             {'default': None,
                              'fixable': None,
                              'fixed': None,
                              'limits': [0, 100],
                              'name': 'limits_param',
                              'type': 'int',
                              'units': None,
                              'value': None,
                              'visible': True},
                             {'default': None,
                              'fixable': None,
                              'fixed': None,
                              'name': 'opts_param',
                              'opt': 'value',
                              'type': 'list',
                              'units': None,
                              'value': None,
                              'visible': True},
                             {'default': None,
                              'fixable': None,
                              'fixed': None,
                              'name': 'units_param',
                              'type': 'float',
                              'units': 'km',
                              'value': None,
                              'visible': True},
                             {'default': 0,
                              'fixable': None,
                              'fixed': None,
                              'name': 'default_param',
                              'type': 'int',
                              'units': None,
                              'value': 0,
                              'visible': True}]

    assert func.as_parameter() == expected_as_parameter


def _test_common_interface():
    import numpy as np

    def sum(a, b):
        return np.sum(a, b)

    op = OperationPlugin(sum)

    # assert op.inputs ==


# TODO: BrokenPipe and ValueError: I/O operation on closed file exceptions occur:
# * more than one of these workflow tests is run
# * one of the workflow tests is run, and a test above has a print() in it

# def test_workflow():
#     from xicam.core.execution.workflow import Workflow
#     from xicam.core.execution.daskexecutor import DaskExecutor
#     from xicam.plugins.operationplugin import output_names
#
#     executor = DaskExecutor()
#
#     @OperationPlugin
#     @output_names('square')
#     def square(a=3) -> int:
#         return a ** 2
#
#     @OperationPlugin
#     @output_names('sum')
#     def my_sum(a, b=3) -> int:
#         return a + b
#
#     wf = Workflow()
#
#     wf.add_operation(square)
#     wf.add_operation(my_sum)
#     wf.add_link(square, my_sum, 'square', 'a')
#
#     assert wf.execute_synchronous(executor=executor) == [{'sum': 12}]
#
#
# def test_autoconnect():
#     from xicam.core.execution.workflow import Workflow
#     from xicam.core.execution.daskexecutor import DaskExecutor
#     from xicam.plugins.operationplugin import output_names
#
#     executor = DaskExecutor()
#
#     @OperationPlugin
#     @output_names('square')
#     def square(a=3) -> int:
#         return a ** 2
#
#     @OperationPlugin
#     @output_names('sum')
#     def my_sum(square, b=3) -> int:
#         return square + b
#
#     wf = Workflow()
#
#     wf.add_operation(square)
#     wf.add_operation(my_sum)
#     wf.auto_connect_all()
#
#     assert wf.execute_synchronous(executor=executor) == [{'sum': 12}]
