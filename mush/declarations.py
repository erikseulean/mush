from mush import missing
from mush import nothing


def name_or_repr(obj):
    return getattr(obj, '__name__', None) or repr(obj)


class requires(object):
    """
    Represents requirements for a particular callable.

    The passed in `args` and `kw` should map to the types, including
    any required :class:`when` or :class:`how`, for the matching
    arguments or keyword parameters the callable requires.
    """

    def __init__(self, *args, **kw):
        self.args = args
        self.kw = kw

    def __iter__(self):
        """
        When iterated over, yields tuples representing individual
        types required by arguments or keyword parameters in the form
        ``(keyword_name, decorated_type)``.

        If the keyword name is ``None``, then the type is for
        a positional argument.
        """
        for arg in self.args:
            yield None, arg
        for k, v in self.kw.items():
            yield k, v

    def __repr__(self):
        bits = []
        for arg in self.args:
            bits.append(name_or_repr(arg))
        for k, v in sorted(self.kw.items()):
            bits.append('%s=%s' % (k, name_or_repr(v)))
        txt = 'requires(%s)' % ', '.join(bits)
        return txt

    def __call__(self, obj):
        obj.__mush_requires__ = self
        return obj


class returns_result_type(object):

    def __call__(self, obj):
        obj.__mush_returns__ = self
        return obj

    def process(self, obj):
        if obj is not None:
            yield obj.__class__, obj

    def __repr__(self):
        return self.__class__.__name__ + '()'


class returns_mapping(returns_result_type):

    def process(self, mapping):
        return mapping.items()


class returns(returns_result_type):

    def __init__(self, *args):
        self.args = args

    def process(self, obj):
        if len(self.args) == 1:
            yield self.args[0], obj
        else:
            for t, o in zip(self.args, obj):
                yield t, o

    def __repr__(self):
        args_repr = ', '.join(name_or_repr(arg) for arg in self.args)
        return self.__class__.__name__ + '(' + args_repr + ')'


class how(object):
    """
    The base class for type decorators that indicate which part of a
    resource is required by a particular callable.

    :param type: The type to be decorated.
    :param name: The part of the type required by the callable.
    """
    type_pattern = '%(type)s'
    name_pattern = ''

    def __init__(self, type, *names):
        self.type = type
        self.names = names

    def __repr__(self):
        txt = self.type_pattern % dict(type=name_or_repr(self.type))
        for name in self.names:
            txt += self.name_pattern % dict(name=name)
        return txt


class optional(how):
    """
    A :class:`how` that indicates the callable requires the wrapped
    requirement only if it's present in the :class:`context`
    """
    type_pattern = 'optional(%(type)s)'

    def process(self, o):
        if o is missing:
            return nothing
        return o


class attr(how):
    """
    A :class:`how` that indicates the callable requires the named
    attribute from the decorated type.
    """
    name_pattern = '.%(name)s'

    def process(self, o):
        try:
            for name in self.names:
                o = getattr(o, name)
        except AttributeError:
            return missing
        else:
            return o


class item(how):
    """
    A :class:`how` that indicates the callable requires the named
    item from the decorated type.
    """
    name_pattern = '[%(name)r]'

    def process(self, o):
        try:
            for name in self.names:
                o = o[name]
        except KeyError:
            return missing
        else:
            return o

