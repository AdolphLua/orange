"""
Data instances in Orange can contain several types of features:
:ref:`discrete <discrete>`, :ref:`continuous <continuous>`,
:ref:`strings <string>`, and :ref:`Python <Python>` and types derived from it.
The latter represent arbitrary Python objects.
The names, types, values (where applicable), functions for computing the
feature value from other features, and other properties of the
features are stored in descriptors contained in this module.

Feature descriptors
-------------------

Feature descriptors can be constructed directly, using constructors and passing
attributes as parameters, or by a factory function
:func:`Orange.data.feature.make`, which either retrieves an existing descriptor
or constructs a new one.

.. class:: Feature

    An abstract base class for feature descriptors.

    .. attribute:: name

        Each feature has a name. The names do not need to be unique since two
        features are considered the same only if they have the same descriptor
        (e.g. even multiple features in the same table can have the same name).
        This should however be avoided since it may result in unpredictable
        behaviour.
    
    .. attribute:: varType
       
        Stores the feature type; it can be Orange.data.Type.Discrete,
        Orange.data.Type.Continuous, Orange.data.Type.String or
        Orange.data.Type.Other.  

    .. attribute:: getValueFrom

        A function (an instance of :obj:`Orange.core.Clasifier`) which computes
        a value of the feature from values of one or more other features. This
        is used, for instance, in discretization where the features describing
        the discretized feature are computed from the original feature. 

    .. attribute:: ordered
    
        A flag telling whether the values of a discrete feature are ordered. At
        the moment, no builtin method treats ordinal features differently than
        nominal.
    
    .. attribute:: distributed
    
        A flag telling whether the values of this features are distributions.
        As for flag ordered, no methods treat such features in any special
        manner.
    
    .. attribute:: randomGenerator
    
        A local random number generator used by method
        :obj:`Feature.randomvalue`.
    
    .. attribute:: defaultMetaId
    
        A proposed (but not guaranteed) meta id to be used for that feature.
        This is used, for instance, by the data loader for tab-delimited file
        format instead of assigning an arbitrary new value, or by
        :obj:`Orange.core.newmetaid` if the feature is passed as an argument. 
        
    .. method:: __call__(obj)
    
           Convert a string, number or other suitable object into a feature
           value.
           
           :param obj: An object to be converted into a feature value
           :type o: any suitable
           :rtype: :class:`Orange.data.Value`
       
    .. method:: randomvalue()

           Return a random value of the feature.
       
           :rtype: :class:`Orange.data.Value`
       
    .. method:: computeValue(inst)

           Compute the value of the feature given the instance by calling
           `getValueFrom` through a mechanism that prevents deadlocks by
           circular calls.

           :rtype: :class:`Orange.data.Value`

.. _discrete:
.. class:: Discrete

    Bases: :class:`Feature`
   
    Descriptor for discrete features.
    
    .. attribute:: values
    
        A list with symbolic names for feature's values. Values are stored as
        indices referring to this list. Therefore, modifying this list 
        instantly changes (symbolic) names of values as they are printed out or
        referred to by user.
    
        .. note::
        
            The size of the list is also used to indicate the number of
            possible values for this feature. Changing the size, especially
            shrinking the list can have disastrous effects and is therefore not
            really recommendable. Also, do not add values to the list by
            calling its append or extend method: call the :obj:`addValue`
            method instead.

            It is also assumed that this attribute is always defined (but can
            be empty), so never set it to None.
    
    .. attribute:: baseValue

            Stores the base value for the feature as an index into `values`.
            This can be, for instance, a "normal" value, such as "no
            complications" as opposed to abnormal "low blood pressure". The
            base value is used by certain statistics, continuization etc.
            potentially, learning algorithms. Default is -1 and means that
            there is no base value.
    
    .. method:: addValue
    
            Add a value to values. Always call this function instead of
            appending to values.

.. _continuous:
.. class:: Continuous

    Bases: :class:`Feature`

    Descriptor for continuous features.
    
    .. attribute:: numberOfDecimals
    
        The number of decimals used when the value is printed out, converted to
        a string or saved to a file.
    
    .. attribute:: scientificFormat
    
        If ``True``, the value is printed in scientific format whenever it
        would have more than 5 digits. In this case, `numberOfDecimals` is
        ignored.

    .. attribute:: adjustDecimals
    
        Tells Orange to monitor the number of decimals when the value is
        converted from a string (when the values are read from a file or
        converted by, e.g. ``inst[0]="3.14"``). The value of ``0`` means that
        the number of decimals should not be adjusted, while 1 and 2 mean that
        adjustments are on, with 2 denoting that no values have been converted
        yet.

        By default, adjustment of number of decimals goes as follows.
    
        If the feature was constructed when data was read from a file, it will 
        be printed with the same number of decimals as the largest number of 
        decimals encountered in the file. If scientific notation occurs in the 
        file, `scientificFormat` will be set to ``True`` and scientific format 
        will be used for values too large or too small. 
    
        If the feature is created in a script, it will have, by default, three
        decimals places. This can be changed either by setting the value
        from a string (e.g. ``inst[0]="3.14"``, but not ``inst[0]=3.14``) or by
        manually setting the `numberOfDecimals`.

    .. attribute:: startValue, endValue, stepValue
    
        The range used for :obj:`randomvalue`.

.. _String:
.. class:: String

    Bases: :class:`Feature`

    Descriptor for features that contains strings. No method can use them for 
    learning; some will complain and other will silently ignore them when they 
    encounter them. They can be, however, useful for meta-attributes; if 
    instances in dataset have unique id's, the most efficient way to store them 
    is to read them as meta-attributes. In general, never use discrete 
    attributes with many (say, more than 50) values. Such attributes are 
    probably not of any use for learning and should be stored as string
    attributes.

    When converting strings into values and back, empty strings are treated 
    differently than usual. For other types, an empty string can be used to
    denote undefined values, while :obj:`StringVariable` will take empty string
    as an empty string -- that is, except when loading or saving into file.
    Empty strings in files are interpreted as undefined; to specify an empty
    string, enclose the string into double quotes; these get removed when the
    string is loaded.

.. _Python:
.. class:: Python

    Bases: :class:`Feature`

    Base class for descriptors defined in Python. It is fully functional,
    and can be used as a descriptor for attributes that contain arbitrary Python
    values. Since this is an advanced topic, PythonVariables are described on a 
    separate page. !!TODO!!
    
    
Features computed from other features
-------------------------------------

Values of features are often computed from other features, such as in
discretization. The mechanism described below usually occurs behind the scenes,
so understanding it is required only for implementing specific transformations.

Monk 1 is a well-known dataset with target concept ``y := a==b or e==1``.
It can help the learning algorithm if the four-valued attribute ``e`` is
replaced with a binary attribute having values `"1"` and `"not 1"`. The
new feature will be computed from the old one on the fly. 

.. literalinclude:: code/feature-getValueFrom.py
    :lines: 7-17
    
The new feature is named ``e2``; we define it by descriptor of type 
:obj:`Discrete`, with appropriate name and values ``"not 1"`` and ``1`` (we 
chose this order so that the ``not 1``'s index is ``0``, which can be, if 
needed, interpreted as ``False``). Finally, we tell e2 to use 
``checkE`` to compute its value when needed, by assigning ``checkE`` to 
``e2.getValueFrom``. 

``checkE`` is a function that is passed an instance and another argument we 
don't care about here. If the instance's ``e`` equals ``1``, the function 
returns value ``1``, otherwise it returns ``not 1``. Both are returned as 
values, not plain strings.

In most circumstances, value of ``e2`` can be computed on the fly - we can 
pretend that the feature exists in the data, although it doesn't (but 
can be computed from it). For instance, we can compute the information gain of
feature ``e2`` or its distribution without actually constructing data containing
the new feature.

.. literalinclude:: code/feature-getValueFrom.py
    :lines: 19-22

There are methods which cannot compute values on the fly because it would be
too complex or time consuming. In such cases, the data need to be converted
to a new :obj:`Orange.data.Table`::

    newDomain = Orange.data.Domain([data.domain["a"], data.domain["b"], e2, data.domain.classVar])
    newData = Orange.data.Table(newDomain, data) 

Automatic computation is useful when the data is split onto training and 
testing examples. Training instanced can be modified by adding, removing 
and transforming features (in a typical setup, continuous features 
are discretized prior to learning, therefore the original features are 
replaced by new ones), while test instances are left as they 
are. When they are classified, the classifier automatically converts the 
testing instances into the new domain, which includes recomputation of 
transformed features. 

.. literalinclude:: code/feature-getValueFrom.py
    :lines: 24-

Reuse of descriptors
--------------------

There are situations when feature descriptors need to be reused. Typically, the 
user loads some training examples, trains a classifier and then loads a separate
test set. For the classifier to recognize the features in the second data set,
the descriptors, not just the names, need to be the same. 

When constructing new descriptors for data read from a file or at unpickling,
Orange checks whether an appropriate descriptor (with the same name and, in case
of discrete features, also values) already exists and reuses it. When new
descriptors are constructed by explicitly calling the above constructors, this
always creates new descriptors and thus new features, although the feature with
the same name may already exist.

The search for existing feature is based on four attributes: the feature's name,
type, ordered values and unordered values. As for the latter two, the values can 
be explicitly ordered by the user, e.g. in the second line of the tab-delimited 
file, for instance to order sizes as small-medium-big.

The search for existing variables can end with one of the following statuses.

Orange.data.feature.Feature.MakeStatus.NotFound (4)
    The feature with that name and type does not exist.

Orange.data.feature.Feature.MakeStatus.Incompatible (3)
    There is (or are) features with matching name and type, but their
    values are incompatible with the prescribed ordered values. For example,
    if the existing feature already has values ["a", "b"] and the new one
    wants ["b", "a"], the old feature cannot be reused. The existing list can,
    however be appended the new values, so searching for ["a", "b", "c"] would
    succeed. So will also the search for ["a"], since the extra existing value
    does not matter. The formal rule is thus that the values are compatible if ``existing_values[:len(ordered_values)] == ordered_values[:len(existing_values)]``.

Orange.data.feature.Feature.MakeStatus.NoRecognizedValues (2)
    There is a matching feature, yet it has none of the values that the new
    feature will have (this is obviously possible only if the new attribute has
    no prescribed ordered values). For instance, we search for a feature
    "sex" with values "male" and "female", while there is a feature of the same 
    name with values "M" and "F" (or, well, "no" and "yes" :). Reuse of this 
    feature is possible, though this should probably be a new feature since it 
    obviously comes from a different data set. If we do decide for reuse, the 
    old feature will get some unneeded new values and the new one will inherit 
    some from the old.

Orange.data.feature.Feature.MakeStatus.MissingValues (1)
    There is a matching feature with some of the values that the new one 
    requires, but some values are missing. This situation is neither uncommon 
    nor suspicious: in case of separate training and testing data sets there may
    be values which occur in one set but not in the other.

Orange.data.feature.Feature.MakeStatus.OK (0)
    There is a perfect match which contains all the prescribed values in the
    correct order. The existing attribute may have some extra values, though.

Continuous attributes can obviously have only two statuses, ``NotFound`` or
``OK``.

When loading the data using :obj:`Orange.data.Table`, Orange takes the safest 
approach and, by default, reuses everything that is compatible, that is, up to 
and including ``NoRecognizedValues``. Unintended reuse would be obvious from the
feature having too many values, which the user can notice and fix. More on that 
in the page on `loading data`. !!TODO!!

There are two functions for reusing the attributes instead of creating new ones.

.. function:: Orange.data.feature.make(name, type, ordered_values, unordered_values[, createNewOn])

    Find and return an existing feature or create a new one if none existing
    features matches the given name, type and values.
    
    The optional `createOnNew` specifies the status at which a new feature is
    created. The status must be at most ``Incompatible`` since incompatible (or
    non-existing) features cannot be reused. If it is set lower, for instance 
    to ``MissingValues``, a new feature is created even if there exists
    a feature which only misses same values. If set to ``OK``, the function
    always creates a new feature.
    
    The function returns a tuple containing a feature descriptor and the
    status of the best matching feature. So, if ``createOnNew`` is set to
    ``MissingValues``, and there exists a feature whose status is, say,
    ``UnrecognizedValues``, a feature would be created, while the second 
    element of the tuple would contain ``UnrecognizedValues``. If, on the other
    hand, there exists a feature which is perfectly OK, its descriptor is 
    returned and the returned status is ``OK``. The function returns no 
    indicator whether the returned feature is reused or not. This can be,
    however, read from the status code: if it is smaller than the specified
    ``createNewOn``, the feature is reused, otherwise we got a new descriptor.

    The exception to the rule is when ``createNewOn`` is OK. In this case, the 
    function does not search through the existing attributes and cannot know the 
    status, so the returned status in this case is always ``OK``.

    :param name: Feature name
    :param type: Feature type
    :type type: Orange.data.feature.Type
    :param ordered_values: a list of ordered values
    :param unordered_values: a list of values, for which the order does not
        matter
    :param createNewOn: gives condition for constructing a new feature instead
        of using the new one
    
    :return_type: a tuple (:class:`Orange.data.feature.Feature`, int)
    
.. function:: Orange.data.feature.retrieve(name, type, ordered_values, onordered_values[, createNewOn])

    Find and return an existing feature, or ``None`` if no match is found.
    
    :param name: feature name.
    :param type: feature type.
    :type type: Orange.data.feature.Type
    :param ordered_values: a list of ordered values
    :param unordered_values: a list of values, for which the order does not
        matter
    :param createNewOn: gives condition for constructing a new feature instead
        of using the new one

    :return_type: :class:`Orange.data.feature.Feature`
    
.. _`feature-reuse.py`: code/feature-reuse.py

These following examples (from `feature-reuse.py`_) give the shown results if
executed only once (in a Python session) and in this order.

:func:`Orange.data.feature.make` can be used for construction of new features. ::
    
    >>> v1, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, ["a", "b"])
    >>> print s, v1.values
    4 <a, b>

No surprises here: new feature is created and the status is ``NotFound``. ::

    >>> v2, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, ["a"], ["c"])
    >>> print s, v2 is v1, v1.values
    1 True <a, b, c>

The status is 1 (``MissingValues``), yet the feature is reused (``v2 is v1``).
``v1`` gets a new value, ``"c"``, which was given as an unordered value. It does
not matter that the new variable does not need value ``b``. ::

    >>> v3, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, ["a", "b", "c", "d"])
    >>> print s, v3 is v1, v1.values
    1 True <a, b, c, d>

This is similar as before, except that the new value, ``d`` is not among the
ordered values. ::

    >>> v4, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, ["b"])
    >>> print s, v4 is v1, v1.values, v4.values
    3, False, <b>, <a, b, c, d>

The new feature needs to have ``b`` as the first value, so it is incompatible 
with the existing features. The status is thus 3 (``Incompatible``), the two 
features are not equal and have different lists of values. ::

    >>> v5, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, None, ["c", "a"])
    >>> print s, v5 is v1, v1.values, v5.values
    0 True <a, b, c, d> <a, b, c, d>

The new feature has values ``c`` and ``a``, but does not
mind about the order, so the existing attribute is ``OK``. ::

    >>> v6, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, None, ["e"]) "a"])
    >>> print s, v6 is v1, v1.values, v6.values
    2 True <a, b, c, d, e> <a, b, c, d, e>

The new feature has different values than the existing (status is 2,
``NoRecognizedValues``), but the existing is reused nevertheless. Note that we
gave ``e`` in the list of unordered values. If it was among the ordered, the
reuse would fail. ::

    >>> v7, s = Orange.data.feature.make("a", Orange.data.Type.Discrete, None,
            ["f"], Orange.data.feature.make.MakeStatus.NoRecognizedValues)))
    >>> print s, v7 is v1, v1.values, v7.values
    2 False <a, b, c, d, e> <f>

This is the same as before, except that we prohibited reuse when there are no
recognized value. Hence a new feature is created, though the returned status is 
the same as before::

    >>> v8, s = Orange.data.feature.make("a", Orange.data.Type.Discrete,
            ["a", "b", "c", "d", "e"], None, Orange.data.feature.Feature.MakeStatus.OK)
    >>> print s, v8 is v1, v1.values, v8.values
    0 False <a, b, c, d, e> <a, b, c, d, e>

Finally, this is a perfect match, but any reuse is prohibited, so a new 
feature is created.

"""
from orange import Variable as Feature
from orange import EnumVariable as Discrete
from orange import FloatVariable as Continuous
from orange import PythonVariable as Python
from orange import StringVariable as String

from orange import VarList as Features

import orange
make = orange.Variable.make
retrieve = orange.Variable.getExisting
del orange