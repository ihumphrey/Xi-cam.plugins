from yapsy.IPlugin import IPlugin
viewTypes = ["ListView", "TreeView", ""]

try:
    from qtpy.QtCore import *


    class DataSourceListModel(QAbstractListModel):
        """
        Represents the data model for a data resource.

        #TODO how does a data_source_list_model keep its rowCount, columnCount,
        #TODOcont with the data_resource?
        """

        def __init__(self, dataresource):
            super(DataSourceListModel, self).__init__()
            self.dataresource = dataresource
            self.dataresource.model = self
            self.rowCount = dataresource.rowCount
            self.data = dataresource.data
            self.columnCount = dataresource.columnCount
            self.refresh = dataresource.refresh

        @property
        def config(self):
            return self.dataresource.config

        @property
        def uri(self):
            return self.dataresource.uri

        @uri.setter
        def uri(self, value):
            self.dataresource.uri = value

        def __getattr__(self, attr):  ## implicitly wrap methods from leftViewer
            if hasattr(self.dataresource, attr):
                m = getattr(self.dataresource, attr)
                return m
            raise NameError(attr)


except ImportError:
    # TODO: how should this be handled?
    pass


class DataResourcePlugin(IPlugin):
    """
    Interface to a data resource.

    Attributes
    ----------
    config
        Keyword arguments to define access to the data resource.
    flags : Dict, optional
        Defines flags to set on the data data resource. By default, if no flags
        are provided, flags are set to {'isFlat': True, 'canPush': False}.
    """

    from xicam.gui.widgets.dataresourcebrowser import DataResourceList, DataBrowser
    model = DataSourceListModel
    view = DataResourceList
    controller = DataBrowser

    isSingleton = False

    name = ''

    def __init__(self, flags: dict = None, **config):
        """
        Config keys should follow RFC 3986 URI format:
            scheme:[//[user[:password]@]host[:port]][/path][?query][#fragment]

        Should provide the abstract methods required of QAbstractItemModel. While this plugin does not depend on Qt, it
        mimics the same functionality, and so can easily be wrapped in a QAbstractItemModel for GUI views. A parent
        model assigns itself to self.model
        """
        super(DataResourcePlugin, self).__init__()
        # self.model = None
        self.config = config
        self.flags = flags if flags else {'isFlat': True, 'canPush': False}
        # self.uri=''

    def pushData(self, *args, **kwargs):
        """
        Push data to the data resource.

        Parameters
        ----------
        args
            TODO
        kwargs
            TODO

        Returns
        -------

        """
        raise NotImplementedError

    def dataChanged(self, topleft=None, bottomright=None):
        """
        TODO brief

        When wrapping this plugin with a QAbstractItemModel, this method
        overrides a signal that is emitted when a data item changes.

        Parameters
        ----------
        topleft : QModelIndex, optional
        bottomright : QModelIndex, optional

        """
        if self.model:
            self.model.dataChanged.emit(topleft, bottomright)

    def columnCount(self, index=None):
        raise NotImplementedError

    def rowCount(self, index=None):
        # When index is provided (QModelIndex), gets the number of rows at the
        # passed index (number of children at the index)
        raise NotImplementedError

    def data(self, index, role):
        """

        Parameters
        ----------
        index
        role

        Returns
        -------

        """
        raise NotImplementedError

    def headerData(self, column, orientation, role):
        """

        Parameters
        ----------
        column
        orientation
        role

        Returns
        -------

        """
        raise NotImplementedError

    def index(self, row, column, parent):
        """

        Parameters
        ----------
        row : int
        column : int
        parent : Union[QModelIndex, None]

        Returns
        -------
            QModelIndex

        """
        raise NotImplementedError

    def parent(self, index):
        raise NotImplementedError

    @property
    def host(self): return self.config['host']

    @property
    def path(self): return self.config['path']

    def refresh(self): pass

    # TODO: convenience properties for each config
