from xicam.plugins import OperationPlugin
from xicam.plugins.operationplugin import (fixed, input_only, limits, output_names,
                                           output_only, output_shape, plot_hint, units)


class TestFixed:

    def test_none(self):
        def func(a, b):
            return

        # assert func._fixed == {}
        assert not hasattr(func, '_fixed')

    def test_one(self):
        @fixed('a')
        def func(a, b):
            return
        assert func._fixed == {'a': True}

    def test_multiple(self):
        @fixed('a')
        @fixed('b')
        def func(a, b, c):
            return
        assert func._fixed == {'a': True, 'b': True}

    def test_explicit(self):
        @fixed('a', True)
        @fixed('b', False)
        def func(a, b, c):
            return
        assert func._fixed == {'a': True, 'b': False}

    def test_redundant(self):
        @fixed('b')
        @fixed('b')
        def func(a, b, c):
            return
        assert func._fixed == {'b': True}

    def test_no_parameter_with_name(self):
        @fixed('dne')
        def func(a, b, c):
            return
        # TODO: what should this do? Should there be checking here?
        assert func._fixed == {'dne': True}

    def test_bad(self):
        # TODO: do we need to test unexpected types?
        @fixed(3)
        def func(a):
            return
        assert True


# TODO: What is @input_only supposed to do?
def test_input_only():
    @input_only('a')
    def func(a):
        return
    assert not func._accepts_output['a']


def test_limits():
    @limits('a', [0.0, 1.0])
    def func(a):
        return
    assert func._limits == {'a': [0.0, 1.0]}


def test_output_names():
    import numpy
    @output_names('sum')
    def sum(a, b):
        return numpy.sum(a, b)

    assert sum._output_names == ('sum',)


# TODO: What is ouput_only supposed to do?
def test_output_only():
    @output_only('a')
    def func(a, b, c):
        return
    assert not func._accepts_input['a']


def test_output_shape():
    # TODO: what should the expected shape be? A collection (list/tuple)?
    import numpy as np
    @output_shape('out', (10, 10))
    def func(a) -> np.ndarray:
        return np.zeros(shape=(10, 10))
    assert func._output_shape == {'out': (10, 10)}


def test_plot_hint():
    print('tlaktj')
    assert False, 'bnlah'


def test_units():
    @units('a', 'mm')
    def func(a):
        return
    assert func._units == {'a': 'mm'}


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
