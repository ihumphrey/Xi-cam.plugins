from xicam.plugins import OperationPlugin


def _test_output_names():
    import numpy
    @output_names('sum')
    def sum(a, b):
        return numpy.sum(a, b)

    assert sum._output_names == ('sum',)


def _test_common_interface():
    import numpy as np

    def sum(a, b):
        return np.sum(a, b)

    op = OperationPlugin(sum)

    # assert op.inputs ==


def test_workflow():
    from xicam.core.execution.workflow import Workflow
    from xicam.core.execution.daskexecutor import DaskExecutor
    from xicam.plugins.operationplugin import output_names
    from qtpy.QtWidgets import QApplication

    executor = DaskExecutor()

    @OperationPlugin
    @output_names('square')
    def square(a=3):
        return a ** 2

    @OperationPlugin
    @output_names('sum')
    def my_sum(a, b=3):
        return a + b

    wf = Workflow()

    wf.addOperation(square)
    # sq_op2 = wf.addOperation(square)
    wf.addOperation(my_sum)
    my_sum.link(output_name='square', input_name='a', output_operation=square)

    assert wf.execute_synchronous(executor=executor) == [{'sum': 12}]
