class Logger(object):
    def info(self, message: str):
        raise NotImplementedError()

    def warn(self, message: str):
        raise NotImplementedError()

    def error(self, message: str):
        raise NotImplementedError()


class Console(Logger):
    def info(self, message: str):
        print("[INFO] {}".format(message))

    def warn(self, message: str):
        print("[WARNING] {}".format(message))

    def error(self, message: str):
        print("[ERROR] {}".format(message))