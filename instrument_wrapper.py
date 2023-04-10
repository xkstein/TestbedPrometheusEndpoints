import socket

class InstrumentWrapper:
    def __init__(self, constructor, name='', connection=None, **kwargs):
        self.constructor = constructor
        self.name = name
        self.kwargs = kwargs
        self.connection = connection
        self.connect()

    def connect(self):
        try:
            self.connection = self.constructor(**self.kwargs)
            print('Connected sucessfully')
        except Exception as e:
#             logging.exception('Failed to connect to instrument')
            print('Connected failed')

    def __getattr__(self, attr):
        if self.connection is None:
            self.connect()

        try:
            wrapped_method = getattr(self.connection, attr)
            return wrapped_method
        except (ConnectionError, socket.timeout, BrokenPipeError):
            self.connect()
        except AttributeError as e:
            if self.connection is not None:
                raise e
            else:
                raise ConnectionError


    def __del__(self):
        try:
            self.connection.close()
        except AttributeError:
            pass

