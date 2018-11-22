import recollection


# ------------------------------------------------------------------------------
class EmptyTestClass(object):
    def __init__(self):
        pass


# ------------------------------------------------------------------------------
class SetterTestClass(object):
    def __init__(self):
        self.target = None
        self.distance = 0

    def getTarget(self):
        return self.target

    def setTarget(self, target):
        self.target = target

    def getDistance(self):
        return self.distance

    def setDistance(self, distance):
        self.distance = distance


# ------------------------------------------------------------------------------
class DecoratedTestClass(object):
    def __init__(self):
        self._foo = 0


# ------------------------------------------------------------------------------
class EventCalledException(Exception):
    pass


# ------------------------------------------------------------------------------
class EventExceptingClass(object):
    def __init__(self):
        pass

    def raise_exception(self):
        raise EventCalledException()
