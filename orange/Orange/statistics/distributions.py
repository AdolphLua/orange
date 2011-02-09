"""

Orange has several classes for computing and storing basic statistics about
features, distributions and contingencies.

    
=========================================
Basic statistics for continuous variables
=========================================

The are two simple classes for computing basic statistics
for continuous features, such as their minimal and maximal value
or average: :class:`BasicStatistics` holds the statistics for a single variable
and :class:`DomainBasicStatistics` behaves like a list of instances of
the above class for all variables in the domain.

.. class:: BasicStatistics

    ``BasicStatistics`` computes and stores minimal, maximal, average and
    standard deviation of a variable. It does not include the median or any
    other statistics that can be computed on the fly, without remembering the
    data; such statistics can be obtained using :obj:`ContDistribution`.

    Instances of this class are seldom constructed manually; they are more often
    returned by :obj:`DomainBasicStatistics` described below.

    .. attribute:: variable
    
        The variable to which the data applies.

    .. attribute:: min

        Minimal value encountered

    .. attribute:: max

        Maximal value encountered

    .. attribute:: avg

        Average value

    .. attribute:: dev

        Standard deviation

    .. attribute:: n

        Number of instances for which the value was defined.
        If instances were weighted, :obj:`n` holds the sum of weights
        
    .. attribute:: sum

        Weighted sum of values

    .. attribute:: sum2

        Weighted sum of squared values

    ..
        .. attribute:: holdRecomputation
    
            Holds recomputation of the average and standard deviation.

    .. method:: add(value[, weight=1])
    
        Add a value to the statistics: adjust :obj:`min` and :obj:`max` if
        necessary, increase :obj:`n` and recompute :obj:`sum`, :obj:`sum2`,
        :obj:`avg` and :obj:`dev`.

        :param value: Value to be added to the statistics
        :type value: float
        :param weight: Weight assigned to the value
        :type weight: float

    ..
        .. method:: recompute()

            Recompute the average and deviation.

.. class:: DomainBasicStatistics

    ``DomainBasicStatistics`` behaves like a ordinary list, except that its
    elements can also be indexed by variable names or descriptors.

    .. method:: __init__(data[, weight=None])

        Compute the statistics for all continuous features in the data, and put
        :obj:`None` to the places corresponding to variables of other types.

        :param data: A table of instances
        :type data: Orange.data.Table
        :param weight: The id of the meta-attribute with weights
        :type weight: `int` or none
        
    .. method:: purge()
    
        Remove the :obj:`None`'s corresponding to non-continuous features; this
        truncates the list, so the indices do not respond to indices of
        variables in the domain.
    
    part of `distributions-basic-stat.py`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-basic-stat.py
        :lines: 1-10

    Output::

             feature   min   max   avg
        sepal length 4.300 7.900 5.843
         sepal width 2.000 4.400 3.054
        petal length 1.000 6.900 3.759
         petal width 0.100 2.500 1.199


    part of `distributions-basic-stat`_ (uses iris.tab)
    
    .. literalinclude:: code/distributions-basic-stat.py
        :lines: 11-

    Output::

        5.84333467484 

.. _distributions-basic-stat: code/distributions-basic-stat.py
.. _distributions-basic-stat.py: code/distributions-basic-stat.py


================================
Distributions of variable values
================================

Class :obj:`Distribution` and derived classes are used for storing empirical
distributions of discrete and continuous variables.

.. class:: Distribution

    A base class for storing distributions of variable values. The class can
    store absolute or relative frequencies. Provides a convenience constructor
    which constructs instances of derived classes. ::

        >>> import Orange
        >>> data = Orange.data.Table("adult_sample")
	>>> disc = orange.statistics.distribution.Distribution("workclass", data)
	>>> print disc
	<685.000, 72.000, 28.000, 29.000, 59.000, 43.000, 2.000>
	>> print type(disc)
	<type 'DiscDistribution'>

    The resulting distribution is of type :obj:`DiscDistribution` since variable
    `workclass` is discrete. The printed numbers are counts of examples that have particular
    attribute value. ::

    	>>> workclass = data.domain["workclass"]
	>>> for i in range(len(workclass.values)):
 	... print "%20s: %5.3f" % (workclass.values[i], disc[i])
                 Private: 685.000
        Self-emp-not-inc: 72.000
            Self-emp-inc: 28.000
             Federal-gov: 29.000
               Local-gov: 59.000
               State-gov: 43.000
             Without-pay: 2.000
            Never-worked: 0.000

    Distributions resembles dictionaries, supporting indexing by instances of
    :obj:`Orange.data.Value`, integers or floats (depending on the distribution
    type), and symbolic names (if :obj:`variable` is defined).

    For instance, the number of examples with `workclass="private"`, can be
    obtained in three ways::
    
        print "Private: ", disc["Private"]
        print "Private: ", disc[0]
        print "Private: ", disc[orange.Value(workclass, "Private")]

    Elements cannot be removed from distributions.

    Length of distribution equals the number of possible values for discrete
    distributions (if :obj:`variable` is set), the value with the highest index
    encountered (if distribution is discrete and :obj: `variable` is
    :obj:`None`) or the number of different values encountered (for continuous
    distributions).

    .. attribute:: variable

        Variable to which the distribution applies; may be :obj:`None` if not
        applicable.

    .. attribute:: unknowns

        The number of instances for which the value of the variable was
        undefined.

    .. attribute:: abs

        Sum of all elements in the distribution. Usually it equals either
        :obj:`cases` if the instance stores absolute frequencies or 1 if the
        stored frequencies are relative, e.g. after calling :obj:`normalize`.

    .. attribute:: cases

        The number of instances from which the distribution is computed,
        excluding those on which the value was undefined. If instances were
        weighted, this is the sum of weights.

    .. attribute:: normalized

        :obj:`True` if distribution is normalized.

    .. attribute:: randomGenerator

        A pseudo-random number generator used for method :obj:`random`.

    .. method:: __init__(variable[, data[, weightId=0]])

        Construct either :obj:`DiscDistribution` or :obj:`ContDistribution`,
        depending on the variable type. If the variable is the only argument, it
        must be an instance of :obj:`Orange.data.feature.Feature`. In that case,
        an empty distribution is constructed. If data is given as well, the
        variable can also be specified by name or index in the
        domain. Constructor then computes the distribution of the specified
        variable on the given data. If instances are weighted, the id of
        meta-attribute with weights can be passed as the third argument.

	If variable is given by descriptor, it doesn't need to exist in the
	domain, but it must be computable from given instances. For example, the
	variable can be a discretized version of a variable from data.

    .. method:: keys()

        Return a list of possible values (if distribution is discrete and
        :obj:`variable` is set) or a list encountered values otherwise.

    .. method:: values()

        Return a list of frequencies of values such as described above.

    .. method:: items()

        Return a list of pairs of elements of the above lists.

    .. method:: native()

        Return the distribution as a list (for discrete distributions) or as a
        dictionary (for continuous distributions)

    .. method:: add(value[, weight=1])

        Increase the count of the element corresponding to ``value`` by
        ``weight``.

        :param value: Value
        :type value: :obj:`Orange.data.Value`, string (if :obj:`variable` is set), :obj:`int` for discrete distributions or :obj:`float` for continuous distributions
        :param weight: Weight to be added to the count for ``value``
        :type weight: float

    .. method:: normalize()

        Divide the counts by their sum, set :obj:`normalized` to :obj:`True` and
        :obj:`abs` to 1. Attributes :obj:`cases` and :obj:`unknowns` are
        unchanged. This changes absoluted frequencies into relative.

    .. method:: modus()

        Return the most common value. If there are multiple such values, one is
        chosen at random, although the chosen value will always be the same for
        the same distribution.

    .. method:: random()

        Return a random value based on the stored empirical probability
        distribution. For continuous distributions, this will always be one of
        the values which actually appeared (e.g. one of the values from
        :obj:`keys`).

        The method uses :obj:`randomGenerator`. If none has been constructed or
        assigned yet, a new one is constructed and stored for further use.


.. class:: DiscDistribution

    Stores a discrete distribution of values. The class differs from its parent
    class in having a few additional constructors.

    .. method:: __init__(variable)

        Construct an instance of :obj:`DiscDistribution` and set the variable
        attribute.

        :param variable: A discrete variable
        :type variable: Orange.data.feature.Discrete

    .. method:: __init__(frequencies)

        Construct an instance and initialize the frequencies from the list, but
	leave `Distribution.variable` empty.

        :param frequencies: A list of frequencies
        :type frequencies: list

        Distribution constructed in this way can be used, for instance, to
	generate random numbers from a given discrete distribution::

            disc = orange.DiscDistribution([0.5, 0.3, 0.2])
            for i in range(20):
                print disc.random(),

        This prints out approximatelly ten 0's, six 1's and four 2's. The values
	can be named by assigning a variable::

            v = orange.EnumVariable(values = ["red", "green", "blue"])
            disc.variable = v

    .. method:: __init__(distribution)

        Copy constructor; makes a shallow copy of the given distribution

        :param distribution: An existing discrete distribution
        :type distribution: DiscDistribution


.. class:: ContDistribution

    Stores a continuous distribution, that is, a dictionary-like structure with
    values and their frequencies.

    .. method:: __init__(variable)

        Construct an instance of :obj:`ContDistribution` and set the variable
        attribute.

        :param variable: A continuous variable
        :type variable: Orange.data.feature.Continuous

    .. method:: __init__(frequencies)

        Construct an instance of :obj:`ContDistribution` and initialize it from
        the given dictionary with frequencies, whose keys and values must be integers.

        :param frequencies: Values and their corresponding frequencies
        :type frequencies: dict

    .. method:: __init__(distribution)

        Copy constructor; makes a shallow copy of the given distribution

        :param distribution: An existing continuous distribution
        :type distribution: ContDistribution

    .. method:: average()

        Return the average value. Note that the average can also be computed
        using a simpler and faster class
        :obj:`Orange.statistics.distributions.BasicStatistics`.

    .. method:: var()

        Return the variance of distribution.

    .. method:: dev()

        Return the standard deviation.

    .. method:: error()

        Return the standard error.

    .. method:: percentile(p)

        Return the value at the `p`-th percentile.

        :param p: The percentile, must be between 0 and 100
        :type p: float
        :rtype: float

        For example, if `d_age` is a continuous distribution, the quartiles can
	be printed by ::

            print "Quartiles: %5.3f - %5.3f - %5.3f" % ( 
                 dage.percentile(25), dage.percentile(50), dage.percentile(75))

   .. method:: density(x)

        Return the probability density at `x`. If the value is not in
	:obj:`Distribution.keys`, it is interpolated.


.. class:: GaussianDistribution

    A class imitating :obj:`ContDistribution` by returning the statistics and
    densities for Gaussian distribution. The class is not meant only for a
    convenient substitution for code which expects an instance of
    :obj:`Distribution`. For general use, Python module :obj:`random`
    provides a comprehensive set of functions for various random distributions.

    .. attribute:: mean

        The mean value parameter of the Gauss distribution.

    .. attribute:: sigma

        The standard deviation of the distribution

    .. attribute:: abs

        The simulated number of instances; in effect, the Gaussian distribution
        density, as returned by method :obj:`density` is multiplied by
        :obj:`abs`.

    .. method:: __init__([mean=0, sigma=1])

        Construct an instance, set :obj:`mean` and :obj:`sigma` to the given
        values and :obj:`abs` to 1.

    .. method:: __init__(distribution)

        Construct a distribution which approximates the given distribution,
        which must be either :obj:`ContDistribution`, in which case its
	average and deviation will be used for mean and sigma, or and existing
        :obj:`GaussianDistribution`, which will be copied. Attribute :obj:`abs`
        is set to the given distribution's ``abs``.

    .. method:: average()

        Return :obj:`mean`.

    .. method:: dev()

        Return :obj:`sigma`.

    .. method:: var()

        Return square of :obj:`sigma`.

    .. method:: density(x)

        Return the density at point ``x``, that is, the Gaussian distribution
	density multiplied by :obj:`abs`.


Class distributions
===================

There is a convenience function for computing empirical class distributions from
data.

.. function:: getClassDistribution(data[, weightID=0])

    Return a class distribution for the given data.

    :param data: A set of instances.
    :type data: Orange.data.Table
    :param weightID: An id for meta attribute with weights of instances
    :type weightID: int
    :rtype: :obj:`DiscDistribution` or :obj:`ContDistribution`, depending on the class type

Distributions of all variables
==============================

Distributions of all variables can be computed and stored in
:obj:`DomainDistributions`. The list-like object can be indexed by variable
indices in the domain, as well as by variables and their names.

.. class:: DomainDistributions

    .. method:: __init__(data[, weightID=0])

        Construct an instance with distributions of all discrete and continuous
        variables from the given data.

    :param data: A set of instances.
    :type data: Orange.data.Table
    :param weightID: An id for meta attribute with weights of instances
    :type weightID: int

The script below computes distributions for all attributes in the data and
prints out distributions for discrete and averages for continuous attributes. ::

    dist = orange.DomainDistributions(data)

        for d in dist:
	    if d.variable.varType == orange.VarTypes.Discrete:
                 print "%30s: %s" % (d.variable.name, d)
	    else:
                 print "%30s: avg. %5.3f" % (d.variable.name, d.average())

The distribution for, say, attribute `age` can be obtained by its index and also
by its name::

    dist_age = dist["age"]

==================
Contingency matrix
==================

Contingency matrix contains conditional distributions. Unless explicitly
'normalized', they contain absolute frequencies, that is, the number of
instances with a particular combination of two variables' values. If they are
normalized by dividing each cell by the row sum, the represent conditional
probabilities of the column variable (here denoted as ``innerVariable``)
conditioned by the row variable (``outerVariable``).

Contingency matrices are usually constructed for discrete variables. Matrices
for continuous variables have certain limitations described in a :ref:`separate
section <contcont>`.

The example below loads the monks-1 data set and prints out the conditional
class distribution given the value of `e`.

.. _distributions-contingency: code/distributions-contingency.py

part of `distributions-contingency`_ (uses monks-1.tab)

.. literalinclude:: code/distributions-contingency.py
    :lines: 1-8

This code prints out::

    1 <0.000, 108.000>
    2 <72.000, 36.000>
    3 <72.000, 36.000>
    4 <72.000, 36.000> 

Contingencies behave like lists of distributions (in this case, class
distributions) indexed by values (of `e`, in this
example). Distributions are, in turn indexed by values (class values,
here). The variable `e` from the above example is called the outer
variable, and the class is the inner. This can also be reversed. It is
also possible to use features for both, outer and inner variable, so
the matrix shows distributions of one variable's values given the
value of another.  There is a corresponding hierarchy of classes:
:obj:`Contingency` is a base class for :obj:`ContingencyVarVar` (both
variables are attribtes) and :obj:`ContingencyClass` (one variable is
the class).  The latter is the base class for
:obj:`ContingencyVarClass` and :obj:`ContingencyClassVar`.

The most commonly used of the above classes is :obj:`ContingencyVarClass` which
can compute and store conditional probabilities of classes given the feature value.

Contingency matrices
====================

.. class:: Contingency

    Provides a base class for storing and manipulating contingency
    matrices. Although it is not abstract, it is seldom used directly but rather
    through more convenient derived classes described below.

    .. attribute:: outerVariable

       Outer variable (:class:`Orange.data.feature.Feature`) whose values are
       used as the first, outer index.

    .. attribute:: innerVariable

       Inner variable(:class:`Orange.data.feature.Feature`), whose values are
       used as the second, inner index.
 
    .. attribute:: outerDistribution

        The marginal distribution (:class:`Distribution`) of the outer variable.

    .. attribute:: innerDistribution

        The marginal distribution (:class:`Distribution`) of the inner variable.
        
    .. attribute:: innerDistributionUnknown

        The distribution (:class:`Distribution`) of the inner variable for
        instances for which the outer variable was undefined. This is the
        difference between the ``innerDistribution`` and (unconditional)
        distribution of inner variable.
      
    .. attribute:: varType

        The type of the outer variable (:obj:`Orange.data.Type`, usually
        :obj:`Orange.data.feature.Discrete` or
        :obj:`Orange.data.feature.Continuous`); equals
        ``outerVariable.varType`` and ``outerDistribution.varType``.

    .. method:: __init__(outer_variable, inner_variable)
     
        Construct an instance of ``Contingency`` for the given pair of
        variables.
     
        :param outer_variable: Descriptor of the outer variable
        :type outer_variable: Orange.data.feature.Feature
        :param outer_variable: Descriptor of the inner variable
        :type inner_variable: Orange.data.feature.Feature
        
    .. method:: add(outer_value, inner_value[, weight=1])
    
        Add an element to the contingency matrix by adding ``weight`` to the
        corresponding cell.

        :param outer_value: The value for the outer variable
        :type outer_value: int, float, string or :obj:`Orange.data.Value`
        :param inner_value: The value for the inner variable
        :type inner_value: int, float, string or :obj:`Orange.data.Value`
        :param weight: Instance weight
        :type weight: float

    .. method:: normalize()

        Normalize all distributions (rows) in the matrix to sum to ``1``::
        
            >>> cont.normalize()
            >>> for val, dist in cont.items():
                   print val, dist

        Output: ::

            1 <0.000, 1.000>
            2 <0.667, 0.333>
            3 <0.667, 0.333>
            4 <0.667, 0.333>

        .. note::
       
            This method does not change the ``innerDistribution`` or
            ``outerDistribution``.
        
    With respect to indexing, contingency matrix is a cross between dictionary
    and a list. It supports standard dictionary methods ``keys``, ``values`` and
    ``items``. ::

        >> print cont.keys()
        ['1', '2', '3', '4']
        >>> print cont.values()
        [<0.000, 108.000>, <72.000, 36.000>, <72.000, 36.000>, <72.000, 36.000>]
        >>> print cont.items()
        [('1', <0.000, 108.000>), ('2', <72.000, 36.000>),
        ('3', <72.000, 36.000>), ('4', <72.000, 36.000>)] 

    Although keys returned by the above functions are strings, contingency can
    be indexed by anything that can be converted into values of the outer
    variable: strings, numbers or instances of ``Orange.data.Value``. ::

        >>> print cont[0]
        <0.000, 108.000>
        >>> print cont["1"]
        <0.000, 108.000>
        >>> print cont[orange.Value(data.domain["e"], "1")] 

    The length of ``Contingency`` equals the number of values of the outer
    variable. However, iterating through contingency
    does not return keys, as with dictionaries, but distributions. ::

        >>> for i in cont:
            ... print i
        <0.000, 108.000>
        <72.000, 36.000>
        <72.000, 36.000>
        <72.000, 36.000>
        <72.000, 36.000> 


.. class:: ContingencyClass

    An abstract base class for contingency matrices that contain the class,
    either as the inner or the outer variable.

    .. attribute:: classVar (read only)
    
        The class attribute descriptor; always equal to either
        :obj:`Contingency.innerVariable` or :obj:``Contingency.outerVariable``.

    .. attribute:: variable
    
        Variable; always equal either to either innerVariable or outerVariable

    .. method:: add_attrclass(variable_value, class_value[, weight=1])

        Add an element to contingency by increasing the corresponding count. The
        difference between this and :obj:`Contigency.add` is that the variable
        value is always the first argument and class value the second,
        regardless of which one is inner and which one is outer.

        :param attribute_value: Variable value
        :type attribute_value: int, float, string or :obj:`Orange.data.Value`
        :param class_value: Class value
        :type class_value: int, float, string or :obj:`Orange.data.Value`
        :param weight: Instance weight
        :type weight: float


.. class:: ContingencyVarClass

    A class derived from :obj:`ContingencyVarClass` in which the variable is
    used as :obj:`Contingency.outerVariable` and class as the
    :obj:`Contingency.innerVariable`. This form is a form suitable for
    computation of conditional class probabilities given the variable value.
    
    Calling :obj:`ContingencyVarClass.add_attrclass(v, c)` is equivalent to
    :obj:`Contingency.add(v, c)`. Similar as :obj:`Contingency`,
    :obj:`ContingencyVarClass` can compute contingency from instances.

    .. method:: __init__(feature, class_variable)

        Construct an instance of :obj:`ContingencyVarClass` for the given pair of
        variables. Inherited from :obj:`Contingency`.

        :param feature: Outer variable
        :type feature: Orange.data.feature.Feature
        :param class_attribute: Class variable; used as ``innerVariable``
        :type class_attribute: Orange.data.feature.Feature
        
    .. method:: __init__(feature, data[, weightId])

        Compute the contingency from data.

        :param feature: Outer variable
        :type feature: Orange.data.feature.Feature
        :param data: A set of instances
        :type data: Orange.data.Table
        :param weightId: meta attribute with weights of instances
        :type weightId: int

    .. method:: p_class(value)

        Return the probability distribution of classes given the value of the
        variable.

        :param value: The value of the variable
        :type value: int, float, string or :obj:`Orange.data.Value`
        :rtype: Orange.statistics.distribution.Distribution


    .. method:: p_class(value, class_value)

        Returns the conditional probability of the class_value given the
        feature value, p(class_value|value) (note the order of arguments!)
        
        :param value: The value of the variable
        :type value: int, float, string or :obj:`Orange.data.Value`
        :param class_value: The class value
        :type value: int, float, string or :obj:`Orange.data.Value`
        :rtype: float

    .. _distributions-contingency3.py: code/distributions-contingency3.py

    part of `distributions-contingency3.py`_ (uses monks-1.tab)

    .. literalinclude:: code/distributions-contingency3.py
        :lines: 1-25

    The inner and the outer variable and their relations to the class are
    as follows::

        Inner variable:  y
        Outer variable:  e
    
        Class variable:  y
        Feature:         e

    Distributions are normalized, and probabilities are elements from the
    normalized distributions. Knowing that the target concept is
    y := (e=1) or (a=b), distributions are as expected: when e equals 1, class 1
    has a 100% probability, while for the rest, probability is one third, which
    agrees with a probability that two three-valued independent features
    have the same value. ::

        Distributions:
          p(.|1) = <0.000, 1.000>
          p(.|2) = <0.662, 0.338>
          p(.|3) = <0.659, 0.341>
          p(.|4) = <0.669, 0.331>
    
        Probabilities of class '1'
          p(1|1) = 1.000
          p(1|2) = 0.338
          p(1|3) = 0.341
          p(1|4) = 0.331
    
        Distributions from a matrix computed manually:
          p(.|1) = <0.000, 1.000>
          p(.|2) = <0.662, 0.338>
          p(.|3) = <0.659, 0.341>
          p(.|4) = <0.669, 0.331>


.. class:: ContingencyClassVar

    :obj:`ContingencyClassVar` is similar to :obj:`ContingencyVarClass` except
    that the class is outside and the variable is inside. This form of
    contingency matrix is suitable for computing conditional probabilities of
    variable given the class. All methods get the two arguments in the same
    order as :obj:`ContingencyVarClass`.

    .. method:: __init__(feature, class_variable)

        Construct an instance of :obj:`ContingencyVarClass` for the given pair of
        variables. Inherited from :obj:`Contingency`, except for the reversed
        order of arguments.

        :param feature: Outer variable
        :type feature: Orange.data.feature.Feature
        :param class_variable: Class variable
        :type class_variable: Orange.data.feature.Feature
        
    .. method:: __init__(feature, data[, weightId])

        Compute contingency from the data.

        :param feature: Descriptor of the outer variable
        :type feature: Orange.data.feature.Feature
        :param data: A set of instances
        :type data: Orange.data.Table
        :param weightId: meta attribute with weights of instances
        :type weightId: int

    .. method:: p_attr(class_value)

        Return the probability distribution of variable given the class.

        :param class_value: The value of the variable
        :type class_value: int, float, string or :obj:`Orange.data.Value`
        :rtype: Orange.statistics.distribution.Distribution

    .. method:: p_attr(value, class_value)

        Returns the conditional probability of the value given the
        class, p(value|class_value).
        Equivalent to `self[class][value]`, except for normalization.

        :param value: Value of the variable
        :type value: int, float, string or :obj:`Orange.data.Value`
        :param class_value: Class value
        :type value: int, float, string or :obj:`Orange.data.Value`
        :rtype: float

    .. _distributions-contingency4.py: code/distributions-contingency4.py
    
    part of the output from `distributions-contingency4.py`_ (uses monk1.tab)
    
    The role of the feature and the class are reversed compared to
    :obj:`ContingencyClassVar`::
    
        Inner variable:  e
        Outer variable:  y
    
        Class variable:  y
        Feature:         e
    
    Distributions given the class can be printed out by calling :meth:`p_attr`.
    
    part of `distributions-contingency4.py`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-contingency4.py
        :lines: 31-
    
    will print::
        p(.|0) = <0.000, 0.333, 0.333, 0.333>
        p(.|1) = <0.500, 0.167, 0.167, 0.167>
    
    If the class value is '0', the attribute `e` cannot be `1` (the first
    value), while distribution across other values is uniform.  If the class
    value is `1`, `e` is `1` for exactly half of instances, and distribution of
    other values is again uniform.

.. class:: ContingencyVarVar

    Contingency matrices in which none of the variables is the class.  The class
    is derived from :obj:`Contingency`, and adds an additional constructor and
    method for getting conditional probabilities.

    .. method:: ContingencyVarVar(outer_variable, inner_variable)

        Inherited from :obj:`Contingency`.

    .. method:: __init__(outer_variable, inner_variable, data[, weightId])

        Compute the contingency from the given instances.

        :param outer_variable: Outer variable
        :type outer_variable: Orange.data.feature.Feature
        :param inner_variable: Inner variable
        :type inner_variable: Orange.data.feature.Feature
        :param data: A set of instances
        :type data: Orange.data.Table
        :param weightId: meta attribute with weights of instances
        :type weightId: int

    .. method:: p_attr(outer_value)

        Return the probability distribution of the inner variable given the
        outer variable value.

        :param outer_value: The value of the outer variable
        :type outer_value: int, float, string or :obj:`Orange.data.Value`
        :rtype: Orange.statistics.distribution.Distribution
 
    .. method:: p_attr(outer_value, inner_value)

        Return the conditional probability of the inner_value
        given the outer_value.

        :param outer_value: The value of the outer variable
        :type outer_value: int, float, string or :obj:`Orange.data.Value`
        :param inner_value: The value of the inner variable
        :type inner_value: int, float, string or :obj:`Orange.data.Value`
        :rtype: float

    The following example investigates which material is used for
    bridges of different lengths.
    
    .. _distributions-contingency5: code/distributions-contingency5.py
    
    part of `distributions-contingency5`_ (uses bridges.tab)
    
    .. literalinclude:: code/distributions-contingency5.py
        :lines: 1-19

    Short bridges are mostly wooden or iron, and the longer (and most of the
    middle sized) are made from steel::
    
        SHORT:
           WOOD (56%)
           IRON (44%)
    
        MEDIUM:
           WOOD (9%)
           IRON (11%)
           STEEL (79%)
    
        LONG:
           STEEL (100%)
    
    As all other contingency matrices, this one can also be computed "manually".
    
    .. literalinclude:: code/distributions-contingency5.py
        :lines: 20-


Contingencies for entire domain
===============================

A list of contingencies, either :obj:`ContingencyVarClass` or
:obj:`ContingencyClassVar`.

.. class:: DomainContingency

    .. method:: __init__(data[, weightId=0, classOuter=0|1])

        Compute a list of contingencies.

        :param data: A set of instances
        :type data: Orange.data.Table
        :param weightId: meta attribute with weights of instances
        :type weightId: int
        :param classOuter: `True`, if class is the outer variable
        :type classOuter: bool

        .. note::
        
            ``classIsOuter`` cannot be given as positional argument,
            but needs to be passed by keyword.

    .. attribute:: classIsOuter (read only)

        Tells whether the class is the outer or the inner variable.

    .. attribute:: classes

        Contains the distribution of class values on the entire dataset.

    .. method:: normalize()

        Call normalize for all contingencies.

    The following script prints the contingencies for features
    "a", "b" and "e" for the dataset Monk 1.
    
    .. _distributions-contingency8: code/distributions-contingency8.py
    
    part of `distributions-contingency8`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-contingency8.py
        :lines: 1-11

    Contingencies are of type :obj:`ContingencyVarClass` give
    the conditional distributions of classes, given the value of the variable.
    
    .. _distributions-contingency8: code/distributions-contingency8.py
    
    part of `distributions-contingency8`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-contingency8.py
        :lines: 13- 


.. _contcont:

Contingencies for continuous variables
======================================

If the outer variable is continuous, the index must be one of the values that do
exist in the contingency matrix. Using other values raises an exception::

    .. _distributions-contingency6: code/distributions-contingency6.py
    
    part of `distributions-contingency6`_ (uses monks-1.tab)
    
    .. literalinclude:: code/distributions-contingency6.py
        :lines: 1-5,18,19

Since even rounding can be a problem, the only safe way to get the key is to
take it from from the contingencies' ``keys``.

Contingencies with discrete outer variable and continuous inner variables are
more useful, since methods :obj:`ContingencyClassVar.p_class` and 
:obj:`ContingencyVarClass.p_attr` use the primitive density estimation
provided by :obj:`Orange.statistics.distribution.Distribution`.

For example, :obj:`ContingencyClassVar` on the iris dataset can return the
probability of the sepal length 5.5 for different classes::

    .. _distributions-contingency7: code/distributions-contingency7.py
    
    part of `distributions-contingency7`_ (uses iris.tab)
    
    .. literalinclude:: code/distributions-contingency7.py

The script outputs::

    Estimated frequencies for e=5.5
      f(5.5|Iris-setosa) = 2.000
      f(5.5|Iris-versicolor) = 5.000
      f(5.5|Iris-virginica) = 1.000

"""



from Orange.core import \
     DomainContingency, \
     DomainDistributions, \
     DistributionList, \
     ComputeDomainContingency, \
     Contingency

from Orange.core import BasicAttrStat as BasicStatistics
from Orange.core import DomainBasicAttrStat as DomainBasicStatistics
from Orange.core import ContingencyAttrAttr as ContingencyVarVar
from Orange.core import ContingencyClass as ContingencyClass
from Orange.core import ContingencyAttrClass as ContingencyVarClass
from Orange.core import ContingencyClassAttr as ContingencyClassVar
