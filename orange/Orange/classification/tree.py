"""

.. index:: classification tree

.. index::
   single: classification; tree

*******************************
Classification trees (``tree``)
*******************************

To build a :obj:`TreeClassifier` from the Iris data set
(with the depth limited to three levels), use (part of `orngTree1.py`_,
uses `iris.tab`_):

.. literalinclude:: code/orngTree1.py
   :lines: 1-4

.. _orngTree1.py: code/orngTree1.py

See `Decision tree learning
<http://en.wikipedia.org/wiki/Decision_tree_learning>`_ on Wikipedia
for introduction to classification trees.

This page first describes the learner and the classifier, and then
defines the base classes (individual components) of the trees and the
tree-building process.

.. autoclass:: TreeLearner
    :members:

.. autoclass:: TreeClassifier
    :members:

.. class:: Node

    Classification trees are represented as a tree-like hierarchy of
    :obj:`Node` classes.

    Node stores the instances belonging to the node, a branch selector,
    a list of branches (if the node is not a leaf) with their descriptions
    and strengths, and a classifier.

    .. attribute:: distribution
    
        A distribution for learning instances in the
        node.

    .. attribute:: contingency

        Complete contingency matrices for the learning instances
        in the node.

    .. attribute:: examples, weightID

        Learning instancess for the node and the corresponding ID
        of weight meta attribute. The root of the tree stores all
        instances, while other nodes store only reference to instances
        in the root node.

    .. attribute:: node_classifier

        A classifier (usually a :obj:`DefaultClassifier`) that can be used
        to classify instances coming to the node. If the node is a leaf,
        this is used to decide the final class (or class distribution)
        of an instance. If it's an internal node, it is stored if
        :obj:`Node`'s flag :obj:`store_node_classifier` is set. Since
        the :obj:`node_classifier` is needed by :obj:`Descender` and
        for pruning (see far below), this is the default behaviour;
        space consumption of the default :obj:`DefaultClassifier` is
        rather small. You should never disable this if you intend to
        prune the tree later.

    If the node is a leaf, the remaining fields are None. If it's
    an internal node, there are several additional fields. The lists
    :obj:`branches`, :obj:`branch_descriptions` and :obj:`branch_sizes`
    are of the same length.

    .. attribute:: branches

        Stores a list of subtrees, given as :obj:`Node`.  An element
        can be None; in this case the node is empty.

    .. attribute:: branch_descriptions

        A list with string descriptions for branches, constructed by
        :obj:`SplitConstructor`. It can contain different kinds of
        descriptions, but basically, expect things like 'red' or '>12.3'.

    .. attribute:: branch_sizes

        Gives a (weighted) number of training instances that went into
        each branch. This can be used later, for instance, for modeling
        probabilities when classifying instances with unknown values.

    .. attribute:: branch_selector

        Gives a branch for each instance. The same object is used
        during learning and classifying. The :obj:`branch_selector`
        is of type :obj:`Orange.classification.Classifier`, since its job is
        similar to that of a classifier: it gets an instance and
        returns discrete :obj:`Orange.data.Value` in range :samp:`[0,
        len(branches)-1]`.  When an instance cannot be classified to
        any branch, the selector can return a :obj:`Orange.data.Value`
        containing a special value (sVal) which should be a discrete
        distribution (DiscDistribution). This should represent a
        :obj:`branch_selector`'s opinion of how to divide the instance
        between the branches. Whether the proposition will be used or not
        depends upon the chosen :obj:`Splitter` (when learning)
        or :obj:`Descender` (when classifying).

    .. method:: tree_size()
        
        Return the number of nodes in the subtrees (including the node,
        excluding null-nodes).



========
Examples
========

For example, here's how to write your own stop function. The example
constructs and prints two trees. For the first one we define the
*defStop* function, which is used by default, and combine it with a
random function so that the stop criteria will also be met in 20% of the
cases when *defStop* is false. For the second tree the stopping criteria
is random. Note that in the second case lambda function still has three
parameters, since this is a necessary number of parameters for the stop
function (:obj:`StopCriteria`).  Part of `tree3.py`_ (uses  `iris.tab`_):

.. _tree3.py: code/tree3.py

.. literalinclude:: code/tree3.py
   :lines: 8-23

The output is not shown here since the resulting trees are rather
big.

Tree Structure
==============

To have something to work on, we'll take the data from lenses dataset and
build a tree using the default components (part of `treestructure.py`_,
uses `lenses.tab`_):

.. literalinclude:: code/treestructure.py
   :lines: 7-10

How big is our tree (part of `treestructure.py`_, uses `lenses.tab`_)?

.. _lenses.tab: code/lenses.tab
.. _treestructure.py: code/treestructure.py

.. literalinclude:: code/treestructure.py
   :lines: 12-21

If node is None, we have a null-node; null nodes don't count, so we
return 0. Otherwise, the size is 1 (this node) plus the sizes of all
subtrees. The node is an internal node if it has a :obj:`branch_selector`;
it there's no selector, it's a leaf. Don't attempt to skip the if
statement: leaves don't have an empty list of branches, they don't have
a list of branches at all.

    >>> treeSize(treeClassifier.tree)
    10

Don't forget that this was only an excercise - :obj:`Node` has a built-in
method :obj:`Node.treeSize` that does exactly the same.

Let us now write a script that prints out a tree. The recursive part of
the function will get a node and its level (part of `treestructure.py`_,
uses `lenses.tab`_).

.. literalinclude:: code/treestructure.py
   :lines: 26-41

Don't waste time on studying formatting tricks (\n's etc.), this is just
for nicer output. What matters is everything but the print statements.
As first, we check whether the node is a null-node (a node to which no
learning instances were classified). If this is so, we just print out
"<null node>" and return.

After handling null nodes, remaining nodes are internal nodes and
leaves.  For internal nodes, we print a node description consisting
of the feature's name and distribution of classes. :obj:`Node`'s
branch description is, for all currently defined splits, an instance
of a class derived from :obj:`Orange.classification.Classifier` 
(in fact, it is
a :obj:`orange.ClassifierFromVarFD`, but a :obj:`Orange.classification.Classifier`
would suffice), and its :obj:`class_var` points to the attribute we seek.
So we print its name. We will also assume that storing class distributions
has not been disabled and print them as well.  Then we iterate through
branches; for each we print a branch description and iteratively call the
:obj:`printTree0` with a level increased by 1 (to increase the indent).

Finally, if the node is a leaf, we print out the distribution of learning
instances in the node and the class to which the instances in the node
would be classified. We again assume that the :obj:`~Node.node_classifier` is
the default one - a :obj:`DefaultClassifier`. A better print function
should be aware of possible alternatives.

Now, we just need to write a simple function to call our printTree0.
We could write something like...

::

    def printTree(x):
        printTree0(x.tree, 0)

... but we won't. Let us learn how to handle arguments of
different types. Let's write a function that will accept either a
:obj:`TreeClassifier` or a :obj:`Node`.  Part of `treestructure.py`_,
uses `lenses.tab`_.

.. literalinclude:: code/treestructure.py
   :lines: 43-49

It's fairly straightforward: if :obj:`x` is of type derived from
:obj:`TreeClassifier`, we print :obj:`x.tree`; if it's :obj:`Node` we
just call :obj:`printTree0` with :obj:`x`. If it's of some other type,
we don't know how to handle it and thus raise an exception. The output::

    >>> printTree(treeClassifier)
    tear_rate (<15.000, 5.000, 4.000>)
    : reduced --> none (<12.000, 0.000, 0.000>)
    : normal
       astigmatic (<3.000, 5.000, 4.000>)
       : no
          age (<1.000, 5.000, 0.000>)
          : young --> soft (<0.000, 2.000, 0.000>)
          : pre-presbyopic --> soft (<0.000, 2.000, 0.000>)
          : presbyopic --> none (<1.000, 1.000, 0.000>)
       : yes
          prescription (<2.000, 0.000, 4.000>)
          : myope --> hard (<0.000, 0.000, 3.000>)
          : hypermetrope --> none (<2.000, 0.000, 1.000>)

For a final exercise, let us write a simple pruning function. It will
be written entirely in Python, unrelated to any :obj:`Pruner`. It will
limit the maximal tree depth (the number of internal nodes on any path
down the tree) given as an argument.  For example, to get a two-level
tree, we would call cutTree(root, 2). The function will be recursive,
with the second argument (level) decreasing at each call; when zero,
the current node will be made a leaf (part of `treestructure.py`_, uses
`lenses.tab`_):

.. literalinclude:: code/treestructure.py
   :lines: 54-62

There's nothing to prune at null-nodes or leaves, so we act only when
:obj:`node` and :obj:`node.branch_selector` are defined. If level is
not zero, we call the function for each branch. Otherwise, we clear the
selector, branches and branch descriptions.

    >>> cutTree(tree.tree, 2)
    >>> printTree(tree)
    tear_rate (<15.000, 5.000, 4.000>)
    : reduced --> none (<12.000, 0.000, 0.000>)
    : normal
       astigmatic (<3.000, 5.000, 4.000>)
       : no --> soft (<1.000, 5.000, 0.000>)
       : yes --> hard (<2.000, 0.000, 4.000>)

Learning
========

You could just call :class:`TreeLearner` and let it fill the empty slots
with the default components. This section will teach you three things:
what are the missing components (and how to set the same components
yourself), how to use alternative components to get a different tree and,
finally, how to write a skeleton for tree induction in Python.

.. _treelearner.py: code/treelearner.py

Let us construct a :obj:`TreeLearner` to play with (`treelearner.py`_,
uses `lenses.tab`_):

.. literalinclude:: code/treelearner.py
   :lines: 7-10

There are three crucial components in learning: the
:obj:`~TreeLearner.split` and :obj:`~TreeLearner.stop` criteria, and the
example :obj:`~TreeLearner.splitter` (there are some others, which become
important during classification; we'll talk about them later). They are
not defined; if you use the learner, the slots are filled temporarily
but later cleared again.

::

    >>> print learner.split
    None
    >>> learner(data)
    <TreeClassifier instance at 0x01F08760>
    >>> print learner.split
    None

Stopping criteria
=================

The stop is trivial. The default is set by

    >>> learner.stop = Orange.classification.tree.StopCriteria_common()

We can now examine the default stopping parameters.

    >>> print learner.stop.max_majority, learner.stop.min_examples
    1.0 0.0

Not very restrictive. This keeps splitting the instances until there's
nothing left to split or all the instances are in the same class. Let us
set the minimal subset that we allow to be split to five instances and
see what comes out.

    >>> learner.stop.min_instances = 5.0
    >>> tree = learner(data)
    >>> print tree.dump()
    tear_rate=reduced: none (100.00%)
    tear_rate=normal
    |    astigmatic=no
    |    |    age=pre-presbyopic: soft (100.00%)
    |    |    age=presbyopic: none (50.00%)
    |    |    age=young: soft (100.00%)
    |    astigmatic=yes
    |    |    prescription=hypermetrope: none (66.67%)
    |    |    prescription=myope: hard (100.00%)

OK, that's better. If we want an even smaller tree, we can also limit
the maximal proportion of majority class.

    >>> learner.stop.max_majority = 0.5
    >>> tree = learner(data)
    >>> print tree.dump()
    none (62.50%)


=================================
Learner and Classifier Components
=================================

Split constructors
=====================

Split constructor find a suitable criteria for dividing the learning (and
later testing) instances. Those that cannot handle a particular feature
type (discrete, continuous) quitely skip them. Therefore use a correct
split constructor for your dataset, or :obj:`SplitConstructor_Combined`
that delegates features to specialized split constructors.

The same split constructors can be both for classification and regression
trees, if the 'measure' attribute for the :obj:`SplitConstructor_Score`
class (and derived classes) is set accordingly.

.. class:: SplitConstructor

    Finds a suitable criteria for dividing the learning (and later
    testing) instances. 
    
    The :obj:`SplitConstructor` should use the domain contingency when
    possible, both because it's faster and because the contingency
    matrices are not necessarily constructed by simply counting the
    instances. There are, however, cases when domain contingency does not
    suffice; for example if ReliefF is used to score features.

    :obj:`SplitConstructor` returns a classifier to be used as
    :obj:`Node`'s :obj:`~Node.branch_selector`, a list of branch descriptions
    a list with the number of instances that go into each branch
    (if empty, the :obj:`TreeLearner` will find the number itself after
    splitting the instances into subsets), a split quality (a number without
    any fixed meaning except that higher numbers mean better splits).

    If the constructed splitting criterion uses a feature in such
    a way that the feature will be useless in the future and should not be
    considered as a split criterion in any of the subtrees (the typical
    case of this are discrete features that are used as-they-are,
    without any binarization or subsetting), then it should report
    the index of this feature. Some splits do not spend any features;
    this is indicated by returning a negative index.

    A :obj:`SplitConstructor` can veto the further tree induction
    by returning no classifier. This can happen for many reasons.
    A general one is related to number of instances in the branches.
    :obj:`SplitConstructor` has a field :obj:`min_subset`, which sets
    the minimal number of instances in a branch; null nodes
    are allowed. If there is no split where this condition is met,
    :obj:`SplitConstructor` stops the induction.

    .. attribute:: min_subset

        The minimal number of (weighted) in non-null leaves.

    .. method:: __call__(instances, [ weightID, contingency, apriori_distribution, candidates, clsfr]) 

        :param instances:  Examples can be given in any acceptable form
            (an :obj:`ExampleGenerator`, such as :obj:`ExampleTable`, or a
            list of instances).
        :param weightID: Optional; the default of 0 means that all
            instances have a weight of 1.0. 
        :param contingency: a domain contingency
        :param apriori_distribution: apriori class probabilities.
        :type apriori_distribution: :obj:`Orange.statistics.distribution.Distribution`
        :param candidates: The split constructor should consider only 
            the features in the candidate list (one boolean for each
            feature).
        :param clsfr: a node classifier (if it was constructed, that is, 
            if :obj:`store_node_classifier` is True) 

        Construct a split. Return a tuple (:obj:`branch_selector`,
        :obj:`branch_descriptions`, :obj:`subset_sizes`, :obj:`quality`,
        :obj:`spent_feature`). :obj:`spent_feature` is -1 if no
        feature is completely spent by the split criterion. If no
        split is constructed, the :obj:`selector`, :obj:`branch_descriptions`
        and :obj:`subset_sizes` are None, while :obj:`quality` is 0.0 and
        :obj:`spent_feature` is -1. 

.. class:: SplitConstructor_Score

    Bases: :class:`SplitConstructor`

    An abstract base class for split constructors that compare splits
    with a :class:`Orange.feature.scoring.Score`.  All split
    constructors except for :obj:`SplitConstructor_Combined` are derived
    from this class.

    .. attribute:: measure

        A :class:`Orange.feature.scoring.Score` for split evaluation. It
        has to handle the class type - for example, you cannot use
        :class:`~Orange.feature.scoring.GainRatio` for regression or
        :class:`~Orange.feature.scoring.MSE` for classification.

    .. attribute:: worst_acceptable

        The lowest allowed split quality.  The value strongly depends
        on chosen :obj:`measure` component. Default is 0.0.

.. class:: SplitConstructor_Feature

    Bases: :class:`SplitConstructor_Score`

    Each value of a discrete feature corresponds to a branch.  The feature
    with the highest score (:obj:`~Measure.measure`) is selected. When
    tied, a random feature is selected.

    The constructed :obj:`branch_selector` is an instance of
    :obj:`orange.ClassifierFromVarFD` that returns a value of the selected
    feature. :obj:`branch_description` contains the feature's
    values. The feature is marked as spent (it cannot reappear in the
    node's subtrees).

.. class:: SplitConstructor_ExhaustiveBinary

    Bases: :class:`SplitConstructor_Score`

    For each discrete feature it determines which binarization gives
    the the highest score. In case of ties, a random feature is selected.

    The constructed :obj:`branch_selector` is an instance
    :obj:`orange.ClassifierFromVarFD` that returns a value of the selected
    feature. Its :obj:`transformer` contains a :obj:`MapIntValue`
    that maps values of the feature into a binary feature. Branch
    descriptions are of form ``[<val1>, <val2>, ...<valn>]`` for branches
    with more than one feature value. Branches with a single feature
    value are described with that value. If the feature was binary,
    it is spent and cannot be used in the node's subtrees. Otherwise
    it is not spent.


.. class:: SplitConstructor_Threshold

    Bases: :class:`SplitConstructor_Score`

    The only split constructor for continuous features.  It divides the
    range of feature values with a threshold that maximizes the split's
    quality. In case of ties, a random feature is selected.  The feature
    that yields the best binary split is returned.

    The constructed :obj:`branch_selector` is an instance of
    :obj:`orange.ClassifierFromVarFD` with an attached :obj:`transformer`,
    of type :obj:`Orange.feature.discretization.ThresholdDiscretizer`. The
    branch descriptions are "<threshold" and ">=threshold". The feature
    is not spent.

.. class:: SplitConstructor_OneAgainstOthers
    
    Bases: :class:`SplitConstructor_Score`

    Undocumented.

.. class:: SplitConstructor_Combined

    Bases: :class:`SplitConstructor`

    This split constructor uses different split constructors for
    discrete and continuous features. Each split constructor is called
    with features of appropriate type only. Both construct a candidate
    for a split; the better of them is selected.

    There is a problem when multiple candidates have the same score. Let
    there be nine discrete features with the highest score; the split
    constructor for discrete features will select one of them. Now,
    if there is a single continuous feature with the same score,
    :obj:`SplitConstructor_Combined` would randomly select between the
    proposed discrete feature and the continuous feature. It is not aware
    of that the discrete has already competed with eight other discrete
    features. So, the probability for selecting (each) discrete feature
    would be 1/18 instead of 1/10. Although incorrect, we doubt that
    this would affect the tree's performance.

    The :obj:`branch_selector`, :obj:`branch_descriptions` and whether
    the feature is spent is decided by the winning split constructor.

    .. attribute: discrete_split_constructor

        Split constructor for discrete features; 
        for instance, :obj:`SplitConstructor_Feature` or
        :obj:`SplitConstructor_ExhaustiveBinary`.

    .. attribute: continuous_split_constructor

        Split constructor for continuous features; it 
        can be either :obj:`SplitConstructor_Threshold` or a 
        split constructor you programmed in Python.


StopCriteria and StopCriteria_common
============================================

:obj:`StopCriteria` determines when to stop the induction of subtrees. 

.. class:: StopCriteria

    Provides the basic stopping criteria: the tree induction stops
    when there is at most one instance left (the actual, not weighted,
    number). The induction also stops when all instances are in the
    same class (for discrete problems) or have the same outcome value
    (for regression problems).

    .. method:: __call__(instances[, weightID, domain contingencies])

        Return True (stop) of False (continue the induction).
        If contingencies are given, they are used for checking whether
        classes but not for counting. Derived classes should use the
        contingencies whenever possible.

.. class:: StopCriteria_common

    Additional criteria for pre-pruning: the proportion of majority
    class and the number of weighted instances.

    .. attribute:: max_majority

        Maximal proportion of majority class. When exceeded,
        induction stops.

    .. attribute:: min_instances

        Minimal number of instances in internal leaves. Subsets with less
        than :obj:`min_instances` instances are not split further.
        The sample count is weighed.


Splitters
=================

Splitters sort learning instances info brances (the branches are selected
with a :obj:`SplitConstructor`, while a :obj:`Descender` decides the
branch for an instance during classification.

Most splitters simply call :obj:`Node.branch_selector` and assign
instances to correspondingly. When the value is unknown they choose a
particular branch or simply skip the instance.


Some enhanced splitters can split instances. An instance (actually,
a pointer to it) is copied to more than one subset. To facilitate
real splitting, weights are needed. Each branch has a weight ID (each
would usually have its own ID) and all instances in that branch (either
completely or partially) should have this meta attribute. If an instance
hasn't been split, it has only one additional attribute - with weight
ID corresponding to the subset to which it went. Instance that is split
between, say, three subsets, has three new meta attributes, one for each
subset. ID's of weight meta attributes returned by the :obj:`Splitter`
are used for the induction of the corresponding subtrees.

The weights are used only when needed. When no splitting occured -
because the splitter is was unable to do it or because there was no need
for splitting - no weight ID's are returned.


.. class:: Splitter

    An abstract base class for objects that split sets of instances
    into subsets. The derived classes treat instances which cannot be
    unambiguously placed into a single branch (usually due to unknown
    value of the crucial attribute) differently.

    .. method:: __call__(node, instances[, weightID])

        :param node: a node.
        :type node: :obj:`Node`
        :param instances: a set of instances
        :param weightID: weight ID. 
        
        Use the information in :obj:`node` (particularly the
        :obj:`branch_selector`) to split the given set of instances into
        subsets.  Return a tuple with a list of instance generators and
        a list of weights.  The list of weights is either an ordinary
        python list of integers or a None when no splitting of instances
        occurs and thus no weights are needed.

        Return a list of subsets of instances and, optionally, a list
        of new weight ID's.

.. class:: Splitter_IgnoreUnknowns

    Bases: :class:`Splitter`

    Ignores the instances for which no single branch can be determined.

.. class:: Splitter_UnknownsToCommon

    Bases: :class:`Splitter`

    Places all ambiguous instances to a branch with the highest number of
    instances. If there is more than one such branch, one is selected at
    random and then used for all instances.

.. class:: Splitter_UnknownsToAll

    Bases: :class:`Splitter`

    Places instances with an unknown value of the feature into all branches.

.. class:: Splitter_UnknownsToRandom

    Bases: :class:`Splitter`

    Selects a random branch for ambiguous instances.

.. class:: Splitter_UnknownsToBranch

    Bases: :class:`Splitter`

    Constructs an additional branch to contain all ambiguous instances. 
    The branch's description is "unknown".

.. class:: Splitter_UnknownsAsBranchSizes

    Bases: :class:`Splitter`

    Splits instances with unknown value of the feature according to
    proportions of instances in each branch.

.. class:: Splitter_UnknownsAsSelector

    Bases: :class:`Splitter`

    Splits instances with unknown value of the feature according to
    distribution proposed by selector (usually the same as proportions
    of instances in branches).

Descenders
=============================


Descenders decide the where should the instances that cannot be
unambiguously put in a branch be sorted to (the branches are selected
with a :obj:`SplitConstructor`, while a :obj:`Splitter` sorts instances
during learning).

.. class:: Descender

    An abstract base object for tree descenders. It descends a
    given instance as far deep as possible, according to the values
    of instance's features. The :obj:`Descender`: calls the node's
    :obj:`~Node.branch_selector` to get the branch index. If it's a
    simple index, the corresponding branch is followed. If not, it's up
    to descender to decide what to do. A descender can choose a single
    branch (for instance, the one that is the most recommended by the
    :obj:`~Node.branch_selector`) or it can let the branches vote.

    Three are possible outcomes of a descent:

    #. The descender reaches a leaf. This happens when
       there were no unknown or out-of-range values, or when the
       descender selected a single branch and continued the descend
       despite them. The descender returns the reached :obj:`Node`.
    #. Node's :obj:`~Node.branch_selector` returned a distribution and the
       :obj:`Descender` decided to stop the descend at this (internal)
       node. It returns the current :obj:`Node`.
    #. Node's :obj:`~Node.branch_selector` returned a distribution and the
       :obj:`Node` wants to split the instance (i.e., to decide the class
       by voting). It returns a :obj:`Node` and the vote-weights for the
       branches.  The weights can correspond to the distribution returned
       by node's :obj:`~Node.branch_selector`, to the number of learning
       instances that were assigned to each branch, or to something else.

    .. method:: __call__(node, instance)

        Descends down the tree until it reaches a leaf or a node in
        which a vote of subtrees is required. In both cases, a tuple
        of two elements is returned; in the former, the tuple contains
        the reached node and None, in the latter in contains a node and
        weights of votes for subtrees (a list of floats).

        Descenders that never split instances always descend to a
        leaf. They differ in the treatment of instances with unknown
        values (or, in general, instances for which a branch cannot be
        determined at some node the tree). Descenders that
        do split instances differ in returned vote weights.

.. class:: Descender_UnknownsToNode

    Bases: :obj:`Descender`

    When instance cannot be classified into a single branch, the current
    node is returned. Thus, the node's :obj:`~Node.node_classifier`
    will be used to make a decision. In such case the internal nodes
    need to have their :obj:`Node.node_classifier` (i.e., don't disable
    creating node classifier or manually remove them after the induction).

.. class:: Descender_UnknownsToBranch

    Bases: :obj:`Descender`

    Classifies instances with unknown value to a special branch. This
    makes sense only if the tree itself was constructed with
    :obj:`Splitter_UnknownsToBranch`.

.. class:: Descender_UnknownsToCommonBranch

    Bases: :obj:`Descender`

    Classifies instances with unknown values to the branch with the
    highest number of instances. If there is more than one such branch,
    random branch is chosen for each instance that is to be classified.

.. class:: Descender_UnknownsToCommonSelector

    Bases: :obj:`Descender`

    Classifies instances with unknown values to the branch which received
    the highest recommendation by the selector.

.. class:: Descender_MergeAsBranchSizes

    Bases: :obj:`Descender`

    The subtrees vote for the instance's class; the vote is weighted
    according to the sizes of the branches.

.. class:: Descender_MergeAsSelector

    Bases: :obj:`Descender`

    The subtrees vote for the instance's class; the vote is weighted
    according to the selectors proposal.

Pruning
=======

.. index::
    pair: classification trees; pruning

The pruners construct a shallow copy of a tree.  The pruned tree's
:obj:`Node` contain references to the same contingency matrices,
node classifiers, branch selectors, ...  as the original tree. Thus,
you may modify a pruned tree structure (manually cut it, add new
nodes, replace components) but modifying, for instance, some node's
:obj:`~Node.node_classifier` (a :obj:`~Node.node_classifier` itself, not
a reference to it!) would modify the node's :obj:`~Node.node_classifier`
in the corresponding node of the original tree.

Pruners cannot construct a :obj:`~Node.node_classifier` nor merge
:obj:`~Node.node_classifier` of the pruned subtrees into classifiers for new
leaves. Thus, if you want to build a prunable tree, internal nodes
must have their :obj:`~Node.node_classifier` defined. Fortunately, this is
the default.

.. class:: Pruner

    An abstract base class for a tree pruner which defines nothing useful, 
    only a pure virtual call operator.

    .. method:: __call__(tree)

        :param tree: either
            a :obj:`Node` (presumably, but not necessarily a root) or a
            :obj:`_TreeClassifier` (the C++ version of the classifier,
            saved in :obj:`TreeClassfier.base_classifier`).

        Prunes a tree. The argument can be either a tree classifier or
        a tree node; the result is of the same type as the argument.
        The original tree remains intact.

.. class:: Pruner_SameMajority

    Bases: :class:`Pruner`

    In Orange, a tree can have a non-trivial subtrees (i.e. subtrees with
    more than one leaf) in which all the leaves have the same majority
    class. This is allowed because those leaves can still have different
    distributions of classes and thus predict different probabilities.
    However, this can be undesired when we're only interested
    in the class prediction or a simple tree interpretation. The
    :obj:`Pruner_SameMajority` prunes the tree so that there is no
    subtree in which all the nodes would have the same majority class.

    This pruner will only prune the nodes in which the node classifier
    is a :obj:`~Orange.classification.majority.ConstantClassifier`
    (or a derived class).

    The leaves with more than one majority class require some special
    handling. The pruning goes backwards, from leaves to the root.
    When siblings are compared, the algorithm checks whether they have
    (at least one) common majority class. If so, they can be pruned.

.. class:: Pruner_m

    Bases: :class:`Pruner`

    Prunes a tree by comparing m-estimates of static and dynamic 
    error as defined in (Bratko, 2002).

    .. attribute:: m

        Parameter m for m-estimation.

Printing the tree
=================

The included printing functions can print out practically anything you'd
like to know, from the number of instances, proportion of instances of
majority class in nodes and similar, to more complex statistics like the
proportion of instances in a particular class divided by the proportion
of examples of this class in a parent node. And even more, you can define
your own callback functions to be used for printing.

Before we go on: you can read all about the function and use it to its
full extent, or you can just call it, giving it the tree as the sole
argument and it will print out the usual textual representation of the
tree. If you're satisfied with that, you can stop here.

The magic is in the format string. It is a string which is printed
out at every leaf or internal node with the certain format specifiers
replaced by data from the tree node. Specifiers are generally of form
**%[^]<precision><quantity><divisor>**.

**^** at the start tells that the number should be multiplied by 100.
It's useful for printing proportions like percentages.

**<precision>** is in the same format as in Python (or C) string
formatting. For instance, :samp:`%N` denotes the number of examples in
the node, hence :samp:`%6.2N` would mean output to two decimal digits
and six places altogether. If left out, a default format :samp:`5.3` is
used, unless you multiply the numbers by 100, in which case the default
is :samp:`.0` (no decimals, the number is rounded to the nearest integer).

**<divisor>** tells what to divide the quantity in that node with.
:samp:`bP` means division by the same quantity in the parent node; for instance,
:samp:`%NbP` will tell give the number of examples in the node divided by the
number of examples in parent node. You can add use precision formatting,
e.g. :samp:`%6.2NbP.` bA is division by the same quantity over the entire
data set, so :samp:`%NbA` will tell you the proportion of examples (out
of the entire training data set) that fell into that node. If division is
impossible since the parent node does not exist or some data is missing,
a dot is printed out instead of the quantity.

**<quantity>** is the only required element. It defines what to print.
For instance, :samp:`%N` would print out the number of examples in the node.
Possible quantities are

:samp:`V`
    The value predicted at that node. You cannot define the precision 
    or divisor here.

:samp:`N`
    The number of examples in the node.

:samp:`M`
    The number of examples in the majority class (that is, the class 
    predicted by the node).

:samp:`m`
    The proportion of examples in the majority class.

:samp:`A`
    The average class for examples the node; this is available only for 
    regression trees.

:samp:`E`
    Standard error for class of examples in the node; available for
    regression trees.

:samp:`I`
    Print out the confidence interval. The modifier is used as 
    :samp:`%I(95)` of (more complicated) :samp:`%5.3I(95)bP`.

:samp:`C`
    The number of examples in the given class. For classification trees, 
    this modifier is used as, for instance in, :samp:`%5.3C="Iris-virginica"bP` 
    - this will tell the number of examples of Iris-virginica by the 
    number of examples this class in the parent node. If you are 
    interested in examples that are *not* Iris-virginica, say
    :samp:`%5.3CbP!="Iris-virginica"`

    For regression trees, you can use operators =, !=, <, <=, >, and >=, 
    as in :samp:`%C<22` - add the precision and divisor if you will. You
    can also check the number of examples in a certain interval:
    :samp:`%C[20, 22]` will give you the number of examples between 20
    and 22 (inclusive) and :samp:`%C(20, 22)` will give the number of
    such examples excluding the boundaries. You can of course mix the
    parentheses, e.g. :samp:`%C(20, 22]`.  If you would like the examples
    outside the interval, add a :samp:`!`, like :samp:`%C!(20, 22]`.

:samp:`c`
    Same as above, except that it computes the proportion of the class
    instead of the number of examples.

:samp:`D`
    Prints out the number of examples in each class. You can use both,
    precision (it is applied to each number in the distribution) or the
    divisor. This quantity cannot be computed for regression trees.

:samp:`d`
    Same as above, except that it shows proportions of examples. This
    again doesn't work with regression trees.

<user defined formats>
    You can add more, if you will. Instructions and examples are given at
    the end of this section.

.. rubric:: Examples

We shall build a small tree from the iris data set - we shall limit the
depth to three levels (part of `orngTree1.py`_, uses `iris.tab`_):

.. literalinclude:: code/orngTree1.py
   :lines: 1-4

.. _orngTree1.py: code/orngTree1.py

The easiest way to call the function is to pass the tree as the only 
argument::

    >>> print tree.dump()
    petal width<0.800: Iris-setosa (100.00%)
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: Iris-versicolor (94.23%)
    |    |    petal length>=5.350: Iris-virginica (100.00%)
    |    petal width>=1.750
    |    |    petal length<4.850: Iris-virginica (66.67%)
    |    |    petal length>=4.850: Iris-virginica (100.00%)

Let's now print out the predicted class at each node, the number
of examples in the majority class with the total number of examples in
the node::

    >>> print tree.dump(leaf_str="%V (%M out of %N)")
    petal width<0.800: Iris-setosa (50.000 out of 50.000)
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: Iris-versicolor (49.000 out of 52.000)
    |    |    petal length>=5.350: Iris-virginica (2.000 out of 2.000)
    |    petal width>=1.750
    |    |    petal length<4.850: Iris-virginica (2.000 out of 3.000)
    |    |    petal length>=4.850: Iris-virginica (43.000 out of 43.000)

Would you like to know how the number of examples declines as
compared to the entire data set and to the parent node? We find it
with this::

    >>> print tree.dump(leaf_str="%V (%^MbA%, %^MbP%)")
    petal width<0.800: Iris-setosa (100%, 100%)
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: Iris-versicolor (98%, 100%)
    |    |    petal length>=5.350: Iris-virginica (4%, 40%)
    |    petal width>=1.750
    |    |    petal length<4.850: Iris-virginica (4%, 4%)
    |    |    petal length>=4.850: Iris-virginica (86%, 96%)

Let us first read the format string. :samp:`%M` is the number of 
examples in the majority class. We want it divided by the number of
all examples from this class on the entire data set, hence :samp:`%MbA`.
To have it multipied by 100, we say :samp:`%^MbA`. The percent sign
*after* that is just printed out literally, just as the comma and
parentheses (see the output). The string for showing the proportion
of this class in the parent is the same except that we have :samp:`bP`
instead of :samp:`bA`.

And now for the output: all examples of setosa for into the first node.
For versicolor, we have 98% in one node; the rest is certainly
not in the neighbouring node (petal length>=5.350) since all versicolors
from the node petal width<1.750 went to petal length<5.350 (we know
this from the 100% in that line). Virginica is the majority class in
the three nodes that together contain 94% of this class (4+4+86). The
rest must had gone to the same node as versicolor.

If you find this guesswork annoying - so do I. Let us print out the
number of versicolors in each node, together with the proportion of
versicolors among the examples in this particular node and among all
versicolors. So,

::

    '%C="Iris-versicolor" (%^c="Iris-versicolor"% of node, %^CbA="Iris-versicolor"% of versicolors)

gives the following output::

    petal width<0.800: 0.000 (0% of node, 0% of versicolors)
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: 49.000 (94% of node, 98% of versicolors)
    |    |    petal length>=5.350: 0.000 (0% of node, 0% of versicolors)
    |    petal width>=1.750
    |    |    petal length<4.850: 1.000 (33% of node, 2% of versicolors)
    |    |    petal length>=4.850: 0.000 (0% of node, 0% of versicolors)

Finally, we may want to print out the distributions, using a simple 
string :samp:`%D`::

    petal width<0.800: [50.000, 0.000, 0.000]
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: [0.000, 49.000, 3.000]
    |    |    petal length>=5.350: [0.000, 0.000, 2.000]
    |    petal width>=1.750
    |    |    petal length<4.850: [0.000, 1.000, 2.000]
    |    |    petal length>=4.850: [0.000, 0.000, 43.000]

What is the order of numbers here? If you check 
:samp:`data.domain.class_var.values` , you'll learn that the order is setosa, 
versicolor, virginica; so in the node at peta length<5.350 we have 49
versicolors and 3 virginicae. To print out the proportions, we can
:samp:`%.2d` - this gives us proportions within node, rounded on two
decimals::

    petal width<0.800: [1.00, 0.00, 0.00]
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: [0.00, 0.94, 0.06]
    |    |    petal length>=5.350: [0.00, 0.00, 1.00]
    |    petal width>=1.750
    |    |    petal length<4.850: [0.00, 0.33, 0.67]
    |    |    petal length>=4.850: [0.00, 0.00, 1.00]

We haven't tried printing out any information for internal nodes.
To start with the most trivial case, we shall print the prediction at
each node.

::

    tree.dump(leaf_str="%V", node_str=".")
    
says that the node_str should be the same as leaf_str (not very useful 
here, since leaf_str is trivial anyway).

:: 

    root: Iris-setosa
    |    petal width<0.800: Iris-setosa
    |    petal width>=0.800: Iris-versicolor
    |    |    petal width<1.750: Iris-versicolor
    |    |    |    petal length<5.350: Iris-versicolor
    |    |    |    petal length>=5.350: Iris-virginica
    |    |    petal width>=1.750: Iris-virginica
    |    |    |    petal length<4.850: Iris-virginica
    |    |    |    petal length>=4.850: Iris-virginica

Note that the output is somewhat different now: there appeared another
node called *root* and the tree looks one level deeper. This is needed
to print out the data for that node to.

Now for something more complicated: let us observe how the number
of virginicas decreases down the tree::

    print tree.dump(leaf_str='%^.1CbA="Iris-virginica"% (%^.1CbP="Iris-virginica"%)', node_str='.')

Let's first interpret the format string: :samp:`CbA="Iris-virginica"` is 
the number of examples from class virginica, divided by the total number
of examples in this class. Add :samp:`^.1` and the result will be
multiplied and printed with one decimal. The trailing :samp:`%` is printed
out. In parentheses we print the same thing except that we divide by
the examples in the parent node. Note the use of single quotes, so we
can use the double quotes inside the string, when we specify the class.

::

    root: 100.0% (.%)
    |    petal width<0.800: 0.0% (0.0%)
    |    petal width>=0.800: 100.0% (100.0%)
    |    |    petal width<1.750: 10.0% (10.0%)
    |    |    |    petal length<5.350: 6.0% (60.0%)
    |    |    |    petal length>=5.350: 4.0% (40.0%)
    |    |    petal width>=1.750: 90.0% (90.0%)
    |    |    |    petal length<4.850: 4.0% (4.4%)
    |    |    |    petal length>=4.850: 86.0% (95.6%)

See what's in the parentheses in the root node? If :meth:`~TreeClassifier.dump`
cannot compute something (in this case it's because the root has no parent),
it prints out a dot. You can also eplace :samp:`=` by :samp:`!=` and it
will count all classes *except* virginica.

For one final example with classification trees, we shall print the
distributions in that nodes, the distribution compared to the parent
and the proportions compared to the parent (the latter things are not
the same - think why). In the leaves we shall also add the predicted
class. So now we'll have to call the function like this.

::

    >>> print tree.dump(leaf_str='"%V   %D %.2DbP %.2dbP"', node_str='"%D %.2DbP %.2dbP"')
    root: [50.000, 50.000, 50.000] . .
    |    petal width<0.800: [50.000, 0.000, 0.000] [1.00, 0.00, 0.00] [3.00, 0.00, 0.00]:
    |        Iris-setosa   [50.000, 0.000, 0.000] [1.00, 0.00, 0.00] [3.00, 0.00, 0.00]
    |    petal width>=0.800: [0.000, 50.000, 50.000] [0.00, 1.00, 1.00] [0.00, 1.50, 1.50]
    |    |    petal width<1.750: [0.000, 49.000, 5.000] [0.00, 0.98, 0.10] [0.00, 1.81, 0.19]
    |    |    |    petal length<5.350: [0.000, 49.000, 3.000] [0.00, 1.00, 0.60] [0.00, 1.04, 0.62]:
    |    |    |        Iris-versicolor   [0.000, 49.000, 3.000] [0.00, 1.00, 0.60] [0.00, 1.04, 0.62]
    |    |    |    petal length>=5.350: [0.000, 0.000, 2.000] [0.00, 0.00, 0.40] [0.00, 0.00, 10.80]:
    |    |    |        Iris-virginica   [0.000, 0.000, 2.000] [0.00, 0.00, 0.40] [0.00, 0.00, 10.80]
    |    |    petal width>=1.750: [0.000, 1.000, 45.000] [0.00, 0.02, 0.90] [0.00, 0.04, 1.96]
    |    |    |    petal length<4.850: [0.000, 1.000, 2.000] [0.00, 1.00, 0.04] [0.00, 15.33, 0.68]:
    |    |    |        Iris-virginica   [0.000, 1.000, 2.000] [0.00, 1.00, 0.04] [0.00, 15.33, 0.68]
    |    |    |    petal length>=4.850: [0.000, 0.000, 43.000] [0.00, 0.00, 0.96] [0.00, 0.00, 1.02]:
    |    |    |        Iris-virginica   [0.000, 0.000, 43.000] [0.00, 0.00, 0.96] [0.00, 0.00, 1.02]

To explore the possibilities when printing regression trees, we are going 
to induce a tree from the housing data set. Called with the tree as the
only argument, :meth:`TreeClassifier.dump` prints the tree like this::

    RM<6.941
    |    LSTAT<14.400
    |    |    DIS<1.385: 45.6
    |    |    DIS>=1.385: 22.9
    |    LSTAT>=14.400
    |    |    CRIM<6.992: 17.1
    |    |    CRIM>=6.992: 12.0
    RM>=6.941
    |    RM<7.437
    |    |    CRIM<7.393: 33.3
    |    |    CRIM>=7.393: 14.4
    |    RM>=7.437
    |    |    TAX<534.500: 45.9
    |    |    TAX>=534.500: 21.9

Let us add the standard error in both internal nodes and leaves, and
the 90% confidence intervals in the leaves::

    >>> print tree.dump(leaf_str="[SE: %E]\t %V %I(90)", node_str="[SE: %E]")
    root: [SE: 0.409]
    |    RM<6.941: [SE: 0.306]
    |    |    LSTAT<14.400: [SE: 0.320]
    |    |    |    DIS<1.385: [SE: 4.420]:
    |    |    |        [SE: 4.420]   45.6 [38.331-52.829]
    |    |    |    DIS>=1.385: [SE: 0.244]:
    |    |    |        [SE: 0.244]   22.9 [22.504-23.306]
    |    |    LSTAT>=14.400: [SE: 0.333]
    |    |    |    CRIM<6.992: [SE: 0.338]:
    |    |    |        [SE: 0.338]   17.1 [16.584-17.691]
    |    |    |    CRIM>=6.992: [SE: 0.448]:
    |    |    |        [SE: 0.448]   12.0 [11.243-12.714]
    |    RM>=6.941: [SE: 1.031]
    |    |    RM<7.437: [SE: 0.958]
    |    |    |    CRIM<7.393: [SE: 0.692]:
    |    |    |        [SE: 0.692]   33.3 [32.214-34.484]
    |    |    |    CRIM>=7.393: [SE: 2.157]:
    |    |    |        [SE: 2.157]   14.4 [10.862-17.938]
    |    |    RM>=7.437: [SE: 1.124]
    |    |    |    TAX<534.500: [SE: 0.817]:
    |    |    |        [SE: 0.817]   45.9 [44.556-47.237]
    |    |    |    TAX>=534.500: [SE: 0.000]:
    |    |    |        [SE: 0.000]   21.9 [21.900-21.900]

What's the difference between :samp:`%V`, the predicted value and 
:samp:`%A` the average? Doesn't a regression tree always predict the
leaf average anyway? Not necessarily, the tree predict whatever the
:obj:`~Node.node_classifier` in a leaf returns. 
As :samp:`%V` uses the :obj:`Orange.data.variable.Continuous`' function
for printing out the value, therefore the printed number has the same
number of decimals as in the data file.

Regression trees cannot print the distributions in the same way
as classification trees. They instead offer a set of operators for
observing the number of examples within a certain range. For instance,
let us check the number of examples with values below 22, and compare
this number with values in the parent nodes::

    >>> print tree.dump(leaf_str="%C<22 (%cbP<22)", node_str=".")
    root: 277.000 (.)
    |    RM<6.941: 273.000 (1.160)
    |    |    LSTAT<14.400: 107.000 (0.661)
    |    |    |    DIS<1.385: 0.000 (0.000)
    |    |    |    DIS>=1.385: 107.000 (1.020)
    |    |    LSTAT>=14.400: 166.000 (1.494)
    |    |    |    CRIM<6.992: 93.000 (0.971)
    |    |    |    CRIM>=6.992: 73.000 (1.040)
    |    RM>=6.941: 4.000 (0.096)
    |    |    RM<7.437: 3.000 (1.239)
    |    |    |    CRIM<7.393: 0.000 (0.000)
    |    |    |    CRIM>=7.393: 3.000 (15.333)
    |    |    RM>=7.437: 1.000 (0.633)
    |    |    |    TAX<534.500: 0.000 (0.000)
    |    |    |    TAX>=534.500: 1.000 (30.000)</xmp>

The last line, for instance, says the the number of examples with the
class below 22 is among those with tax above 534 is 30 times higher than
the number of such examples in its parent node.

For another exercise, let's count the same for all examples *outside*
interval [20, 22] (given like this, the interval includes the bounds).
And let us print out the proportions as percents.

::

    >>> print tree.dump(leaf_str="%C![20,22] (%^cbP![20,22]%)", node_str=".")

OK, let's observe the format string for one last time. :samp:`%c![20,
22]` would be the proportion of examples (within the node) whose values
are below 20 or above 22. By :samp:`%cbP![20, 22]` we derive this by
the same statistics computed on the parent. Add a :samp:`^` and you have
the percentages.

::

    root: 439.000 (.%)
    |    RM<6.941: 364.000 (98%)
    |    |    LSTAT<14.400: 200.000 (93%)
    |    |    |    DIS<1.385: 5.000 (127%)
    |    |    |    DIS>=1.385: 195.000 (99%)
    |    |    LSTAT>=14.400: 164.000 (111%)
    |    |    |    CRIM<6.992: 91.000 (96%)
    |    |    |    CRIM>=6.992: 73.000 (105%)
    |    RM>=6.941: 75.000 (114%)
    |    |    RM<7.437: 46.000 (101%)
    |    |    |    CRIM<7.393: 43.000 (100%)
    |    |    |    CRIM>=7.393: 3.000 (100%)
    |    |    RM>=7.437: 29.000 (98%)
    |    |    |    TAX<534.500: 29.000 (103%)
    |    |    |    TAX>=534.500: 0.000 (0%)


Defining Your Own Printout functions
------------------------------------

:meth:`TreeClassifier.dump`'s argument :obj:`user_formats` can be used to print out
some other information in the leaves or nodes. If provided,
:obj:`user_formats` should contain a list of tuples with a regular
expression and a callback function to be called when that expression
is found in the format string. Expressions from :obj:`user_formats`
are checked before the built-in expressions discussed above, so you can
override the built-ins if you want to.

The regular expression should describe a string like those we used above,
for instance the string :samp:`%.2DbP`. When a leaf or internal node
is printed out, the format string (:obj:`leaf_str` or :obj:`node_str`)
is checked for these regular expressions and when the match is found,
the corresponding callback function is called.

The callback function will get five arguments: the format string 
(:obj:`leaf_str` or :obj:`node_str`), the match object, the node which is
being printed, its parent (can be None) and the tree classifier.
The function should return the format string in which the part described
by the match object (that is, the part that is matched by the regular
expression) is replaced by whatever information your callback function
is supposed to give.

The function can use several utility function provided in the module.

.. autofunction:: insert_str

.. autofunction:: insert_dot

.. autofunction:: insert_num

.. autofunction:: by_whom


There are also a few pieces of regular expression that you may want to reuse. 
The two you are likely to use are:

.. autodata:: fs

.. autodata:: by

For a trivial example, :samp:`%V` is implemented like this. There is the
following tuple in the list of built-in formats::

    (re.compile("%V"), replaceV)

:obj:`replaceV` is a function defined by::

    def replaceV(strg, mo, node, parent, tree):
        return insert_str(strg, mo, str(node.node_classifier.default_value))

It therefore takes the value predicted at the node
(:samp:`node.node_classifier.default_value` ), converts it to a string
and passes it to *insert_str* to do the replacement.

A more complex regular expression is the one for the proportion of
majority class, defined as :samp:`"%"+fs+"M"+by`. It uses the two partial
expressions defined above.

Let's say with like to print the classification margin for each node,
that is, the difference between the proportion of the largest and the
second largest class in the node (part of `orngTree2.py`_):

.. _orngTree2.py: code/orngTree2.py

.. literalinclude:: code/orngTree2.py
   :lines: 7-31

``get_margin`` gets the distribution and computes the margin. The callback
replaces, ``replaceB``, computes the margin for the node.  If :data:`by`
group is present, we call :func:`by_whom` to get the node with whose
margin this node's margin is to be divided. If this node (usually the
parent) does not exist of if its margin is zero, :func:`insert_dot`
inserts dot, otherwise :func:`insert_num` is called which insert the
number in the user-specified format.  ``my_format`` contains the regular
expression and the callback function.

We can now print out the iris tree:

.. literalinclude:: code/orngTree2.py
    :lines: 33

And we get::

    petal width<0.800: Iris-setosa 100% (100.00%)
    petal width>=0.800
    |    petal width<1.750
    |    |    petal length<5.350: Iris-versicolor 88% (108.57%)
    |    |    petal length>=5.350: Iris-virginica 100% (122.73%)
    |    petal width>=1.750
    |    |    petal length<4.850: Iris-virginica 33% (34.85%)
    |    |    petal length>=4.850: Iris-virginica 100% (104.55%)

Plotting the Tree using Dot
---------------------------

Suppose you saved the tree in a file "tree5.dot". You can then
print it out as a gif if you execute the following command line

::
    
    dot -Tgif tree5.dot -otree5.gif

GraphViz's dot has quite a few other output formats, check 
its documentation to learn which.



===========================
C4.5 Classifier and Learner
===========================

As C4.5 is a standard benchmark in machine learning, 
it is incorporated in Orange, although Orange has its own
implementation of decision trees.

The implementation uses the original Quinlan's code for learning so the
tree you get is exactly like the one that would be build by standalone
C4.5. Upon return, however, the original tree is copied to Orange
components that contain exactly the same information plus what is needed
to make them visible from Python. To be sure that the algorithm behaves
just as the original, we use a dedicated class :class:`C45Node`
instead of reusing the components used by Orange's tree inducer
(ie, :class:`Node`). This, however, could be done and probably
will be done in the future; we shall still retain :class:`C45Node` 
but offer transformation to :class:`Node` so that routines
that work on Orange trees will also be usable for C45 trees.

:class:`C45Learner` and :class:`C45Classifier` behave
like any other Orange learner and classifier. Unlike most of Orange 
learning algorithms, C4.5 does not accepts weighted examples.

Building the C4.5 plug-in
=========================

C4.5 is not distributed with Orange, but it can be incorporated as a
plug-in. A C compiler is need for the procedure: on Windows MS Visual C
(CL.EXE and LINK.EXE must be on the PATH), on Linux and OS X gcc (OS X
users can download it from Apple).

Orange must be installed prior to building C4.5.

#. Download 
   `C4.5 (Release 8) sources <http://www.rulequest.com/Personal/c4.5r8.tar.gz>`_
   from the `Rule Quest's site <http://www.rulequest.com/>`_ and extract
   them. The files will be modified in the
   further process.
#. Download
   `buildC45.zip <http://orange.biolab.si/orange/download/buildC45.zip>`_
   and unzip its contents into the directory R8/Src of the C4.5 sources
   (this directory contains, for instance, the file average.c).
#. Run buildC45.py, which will build the plug-in and put it next to 
   orange.pyd (or orange.so on Linux/Mac).
#. Run python, type :samp:`import Orange` and
   create :samp:`Orange.classification.tree.C45Learner()`. This should
   succeed.
#. Finally, you can remove C4.5 sources.

The buildC45.py creates .h files that wrap Quinlan's .i files and
ensure that they are not included twice. It modifies C4.5 sources to
include .h's instead of .i's (this step can hardly fail). Then it compiles
ensemble.c into c45.dll or c45.so and puts it next to Orange. In the end
it checks if the built C4.5 gives the same results as the original.

.. autoclass:: C45Learner
    :members:

.. autoclass:: C45Classifier
    :members:

.. class:: C45Node

    This class is a reimplementation of the corresponding *struct* from
    Quinlan's C4.5 code.

    .. attribute:: node_type

        Type of the node:  :obj:`C45Node.Leaf` (0), 
        :obj:`C45Node.Branch` (1), :obj:`C45Node.Cut` (2),
        :obj:`C45Node.Subset` (3). "Leaves" are leaves, "branches"
        split examples based on values of a discrete attribute,
        "cuts" cut them according to a threshold value of a continuous
        attributes and "subsets" use discrete attributes but with subsetting
        so that several values can go into the same branch.

    .. attribute:: leaf

        Value returned by that leaf. The field is defined for internal 
        nodes as well.

    .. attribute:: items

        Number of (learning) examples in the node.

    .. attribute:: class_dist

        Class distribution for the node (of type 
        :obj:`Orange.statistics.distribution.Discrete`).

    .. attribute:: tested
        
        The attribute used in the node's test. If node is a leaf,
        obj:`tested` is None, if node is of type :obj:`Branch` or :obj:`Cut`
        :obj:`tested` is a discrete attribute, and if node is of type
        :obj:`Cut` then :obj:`tested` is a continuous attribute.

    .. attribute:: cut

        A threshold for continuous attributes, if node is of type :obj:`Cut`.
        Undefined otherwise.

    .. attribute:: mapping

        Mapping for nodes of type :obj:`Subset`. Element :samp:`mapping[i]`
        gives the index for an example whose value of :obj:`tested` is *i*. 
        Here, *i* denotes an index of value, not a :class:`Orange.data.Value`.

    .. attribute:: branch
        
        A list of branches stemming from this node.

Examples
========

.. _tree_c45.py: code/tree_c45.py
.. _iris.tab: code/iris.tab

The simplest way to use :class:`C45Learner` is to call it. This
script constructs the same learner as you would get by calling
the usual C4.5 (`tree_c45.py`_, uses `iris.tab`_):

.. literalinclude:: code/tree_c45.py
   :lines: 7-14

Arguments can be set by the usual mechanism (the below to lines do the
same, except that one uses command-line symbols and the other internal
variable names)

::

    tree = Orange.classification.tree.C45Learner(data, m=100)
    tree = Orange.classification.tree.C45Learner(data, minObjs=100)

The way that could be prefered by veteran C4.5 user might be through
method `:obj:C45Learner.commandline`.

::

    lrn = Orange.classification.tree.C45Learner()
    lrn.commandline("-m 1 -s")
    tree = lrn(data)

There's nothing special about using :obj:`C45Classifier` - it's 
just like any other. To demonstrate what the structure of 
:class:`C45Node`'s looks like, will show a script that prints 
it out in the same format as C4.5 does.

.. literalinclude:: code/tree_c45_printtree.py

Leaves are the simplest. We just print out the value contained
in :samp:`node.leaf`. Since this is not a qualified value (ie., 
:obj:`C45Node` does not know to which attribute it belongs), we need to
convert it to a string through :obj:`class_var`, which is passed as an
extra argument to the recursive part of printTree.

For discrete splits without subsetting, we print out all attribute values
and recursively call the function for all branches. Continuous splits are
equally easy to handle.

For discrete splits with subsetting, we iterate through branches, retrieve
the corresponding values that go into each branch to inset, turn
the values into strings and print them out, separately treating the
case when only a single value goes into the branch.

=================
SimpleTreeLearner
=================

:obj:`SimpleTreeLearner` is an implementation of regression and classification
trees. It is faster than :obj:`TreeLearner` at the expense of flexibility.
It uses gain ratio for classification and mse for regression.

:obj:`SimpleTreeLearner` was developed for speeding up the construction
of random forests, but can also be used as a standalone tree.

.. class:: SimpleTreeLearner

    .. attribute:: max_majority

        Maximal proportion of majority class. When this is exceeded,
        induction stops.

    .. attribute:: min_instances

        Minimal number of instances in leaves. Instance count is weighed.

    .. attribute:: max_depth

        Maximal depth of tree.

    .. attribute:: skip_prob
        
        At every split an attribute will be skipped with probability ``skip_prob``.
        Useful for building random forests.
        
Examples
========

:obj:`SimpleTreeLearner` is used in much the same way as :obj:`TreeLearner`.
A typical example of using :obj:`SimpleTreeLearner` would be to build a random
forest (uses `iris.tab`_):

.. literalinclude:: code/simple_tree_random_forest.py


References
==========

Bratko, I. (2002). `Prolog Programming for Artificial Intelligence`, Addison 
Wesley, 2002.

E Koutsofios, SC North. Drawing Graphs with dot. AT&T Bell Laboratories,
Murray Hill NJ, U.S.A., October 1993.

`Graphviz - open source graph drawing software <http://www.research.att.com/sw/tools/graphviz/>`_
A home page of AT&T's dot and similar software packages.

"""

"""
TODO C++ aliases

SplitConstructor.discrete/continuous_split_constructor -> SplitConstructor.discrete 
Node.examples -> Node.instances
"""

from Orange.core import \
     TreeLearner as _TreeLearner, \
         TreeClassifier as _TreeClassifier, \
         SimpleTreeLearner, \
         SimpleTreeClassifier, \
         C45Learner as _C45Learner, \
         C45Classifier as _C45Classifier, \
         C45TreeNode as C45Node, \
         C45TreeNodeList as C45NodeList, \
         TreeDescender as Descender, \
              TreeDescender_UnknownMergeAsBranchSizes as Descender_UnknownMergeAsBranchSizes, \
              TreeDescender_UnknownMergeAsSelector as Descender_UnknownMergeAsSelector, \
              TreeDescender_UnknownToBranch as Descender_UnknownToBranch, \
              TreeDescender_UnknownToCommonBranch as Descender_UnknownToCommonBranch, \
              TreeDescender_UnknownToCommonSelector as Descender_UnknownToCommonSelector, \
         TreeExampleSplitter as Splitter, \
              TreeExampleSplitter_IgnoreUnknowns as Splitter_IgnoreUnknowns, \
              TreeExampleSplitter_UnknownsAsBranchSizes as Splitter_UnknownsAsBranchSizes, \
              TreeExampleSplitter_UnknownsAsSelector as Splitter_UnknownsAsSelector, \
              TreeExampleSplitter_UnknownsToAll as Splitter_UnknownsToAll, \
              TreeExampleSplitter_UnknownsToBranch as Splitter_UnknownsToBranch, \
              TreeExampleSplitter_UnknownsToCommon as Splitter_UnknownsToCommon, \
              TreeExampleSplitter_UnknownsToRandom as Splitter_UnknownsToRandom, \
         TreeNode as Node, \
         TreeNodeList as NodeList, \
         TreePruner as Pruner, \
              TreePruner_SameMajority as Pruner_SameMajority, \
              TreePruner_m as Pruner_m, \
         TreeSplitConstructor as SplitConstructor, \
              TreeSplitConstructor_Combined as SplitConstructor_Combined, \
              TreeSplitConstructor_Measure as SplitConstructor_Score, \
                   TreeSplitConstructor_Attribute as SplitConstructor_Feature, \
                   TreeSplitConstructor_ExhaustiveBinary as SplitConstructor_ExhaustiveBinary, \
                   TreeSplitConstructor_OneAgainstOthers as SplitConstructor_OneAgainstOthers, \
                   TreeSplitConstructor_Threshold as SplitConstructor_Threshold, \
         TreeStopCriteria as StopCriteria, \
              TreeStopCriteria_Python as StopCriteria_Python, \
              TreeStopCriteria_common as StopCriteria_common

import Orange.core
import operator
import base64
import re
import Orange.data
import Orange.feature.scoring
import warnings

class C45Learner(Orange.classification.Learner):
    """
    :class:`C45Learner`'s attributes have double names - those that
    you know from C4.5 command lines and the corresponding names of C4.5's
    internal variables. All defaults are set as in C4.5; if you change
    nothing, you are running C4.5.

    .. attribute:: gainRatio (g)
        
        Determines whether to use information gain (false, default)
        or gain ratio for selection of attributes (true).

    .. attribute:: batch (b)

        Turn on batch mode (no windows, no iterations); this option is
        not documented in C4.5 manuals. It conflicts with "window",
        "increment" and "trials".

    .. attribute:: subset (s)
        
        Enables subsetting (default: false, no subsetting),
 
    .. attribute:: probThresh (p)

        Probabilistic threshold for continuous attributes (default: false).

    .. attribute:: minObjs (m)
        
        Minimal number of objects (examples) in leaves (default: 2).

    .. attribute:: window (w)

        Initial windows size (default: maximum of 20% and twice the
        square root of the number of data objects).

    .. attribute:: increment (i)

        The maximum number of objects that can be added to the window
        at each iteration (default: 20% of the initial window size).

    .. attribute:: cf (c)

        Prunning confidence level (default: 25%).

    .. attribute:: trials (t)

        Set the number of trials in iterative (i.e. non-batch) mode (default: 10).

    .. attribute:: prune
        
        Return pruned tree (not an original C4.5 option) (default: true)
    """

    def __new__(cls, instances = None, weightID = 0, **argkw):
        self = Orange.classification.Learner.__new__(cls, **argkw)
        if instances:
            self.__init__(**argkw)
            return self.__call__(instances, weightID)
        else:
            return self
        
    def __init__(self, **kwargs):
        self.base = _C45Learner(**kwargs)

    def __setattr__(self, name, value):
        if name != "base" and name in self.base.__dict__:
            self.base.__dict__[name] = value
        else:
            self.__dict__["base"] = value

    def __getattr(self, name):
        if name != "base":
            return self.base.__dict__[name]
        else:
            return self.base

    def __call__(self, *args, **kwargs):
        return C45Classifier(self.base(*args, **kwargs))

    def commandline(self, ln):
        """
        Set the arguments with a C4.5 command line.
        """
        self.base.commandline(ln)
    
 
class C45Classifier(Orange.classification.Classifier):
    """
    A faithful reimplementation of Quinlan's function from C4.5, but
    uses a tree composed of :class:`C45Node` instead of C4.5's original
    tree structure.

    .. attribute:: tree

        C4.5 tree stored as :obj:`C45Node`.
    """

    def __init__(self, base_classifier):
        self.nativeClassifier = base_classifier
        for k, v in self.nativeClassifier.__dict__.items():
            self.__dict__[k] = v
  
    def __call__(self, instance, result_type=Orange.classification.Classifier.GetValue,
                 *args, **kwdargs):
        """Classify a new instance.
        
        :param instance: instance to be classified.
        :type instance: :class:`Orange.data.Instance`
        :param result_type: 
              :class:`Orange.classification.Classifier.GetValue` or \
              :class:`Orange.classification.Classifier.GetProbabilities` or
              :class:`Orange.classification.Classifier.GetBoth`
        
        :rtype: :class:`Orange.data.Value`, 
              :class:`Orange.statistics.Distribution` or a tuple with both
        """
        return self.nativeClassifier(instance, result_type, *args, **kwdargs)

    def __setattr__(self, name, value):
        if name == "nativeClassifier":
            self.__dict__[name] = value
            return
        if name in self.nativeClassifier.__dict__:
            self.nativeClassifier.__dict__[name] = value
        self.__dict__[name] = value

    def __str__(self):
        return self.dump()
   
    def dump(self):  
        """
        Print the tree in the same form as Ross Quinlan's 
        C4.5 program.

        ::

            import Orange

            data = Orange.data.Table("voting")
            c45 = Orange.classification.tree.C45Learner(data)
            print c45.dump()

        prints

        ::

            physician-fee-freeze = n: democrat (253.4)
            physician-fee-freeze = y:
            |   synfuels-corporation-cutback = n: republican (145.7)
            |   synfuels-corporation-cutback = y:
            |   |   mx-missile = y: democrat (6.0)
            |   |   mx-missile = n:
            |   |   |   adoption-of-the-budget-resolution = n: republican (22.6)
            |   |   |   adoption-of-the-budget-resolution = y:
            |   |   |   |   anti-satellite-test-ban = n: democrat (5.0)
            |   |   |   |   anti-satellite-test-ban = y: republican (2.2)


        The standalone C4.5 would, on the same data, print::

            physician-fee-freeze = n: democrat (253.4/5.9)
            physician-fee-freeze = y:
            |   synfuels-corporation-cutback = n: republican (145.7/6.2)
            |   synfuels-corporation-cutback = y:
            |   |   mx-missile = y: democrat (6.0/2.4)
            |   |   mx-missile = n:
            |   |   |   adoption-of-the-budget-resolution = n: republican (22.6/5.2)
            |   |   |   adoption-of-the-budget-resolution = y:
            |   |   |   |   anti-satellite-test-ban = n: democrat (5.0/1.2)
            |   |   |   |   anti-satellite-test-ban = y: republican (2.2/1.0)

        4.5 also prints out the number of errors on learning data in
        each node.
        """
        return  _c45_printTree0(self.tree, self.class_var, 0)

def _c45_showBranch(node, classvar, lev, i):
    var = node.tested
    str_ = ""
    if node.node_type == 1:
        str_ += "\n"+"|   "*lev + "%s = %s:" % (var.name, var.values[i])
        str_ += _c45_printTree0(node.branch[i], classvar, lev+1)
    elif node.node_type == 2:
        str_ += "\n"+"|   "*lev + "%s %s %.1f:" % (var.name, ["<=", ">"][i], node.cut)
        str_ += _c45_printTree0(node.branch[i], classvar, lev+1)
    else:
        inset = filter(lambda a:a[1]==i, enumerate(node.mapping))
        inset = [var.values[j[0]] for j in inset]
        if len(inset)==1:
            str_ += "\n"+"|   "*lev + "%s = %s:" % (var.name, inset[0])
        else:
            str_ +=  "\n"+"|   "*lev + "%s in {%s}:" % (var.name, ", ".join(inset))
        str_ += _c45_printTree0(node.branch[i], classvar, lev+1)
    return str_
        
        
def _c45_printTree0(node, classvar, lev):
    var = node.tested
    str_ = ""
    if node.node_type == 0:
        str_ += "%s (%.1f)" % (classvar.values[int(node.leaf)], node.items) 
    else:
        for i, branch in enumerate(node.branch):
            if not branch.node_type:
                str_ += _c45_showBranch(node, classvar, lev, i)
        for i, branch in enumerate(node.branch):
            if branch.node_type:
                str_ += _c45_showBranch(node, classvar, lev, i)
    return str_

def _printTreeC45(tree):
    print _c45_printTree0(tree.tree, tree.class_var, 0)


import Orange.feature.scoring as fscoring

class TreeLearner(Orange.core.Learner):
    """
    A classification or regression tree learner.  If upon
    initialization :class:`TreeLearner` is given a set of instances,
    then an :class:`TreeClassifier` object is built and returned
    instead. Attributes can be also be set on initialization.

    **The tree building process**

    #. The learning instances are stored in a table,
       because the algorithm works with pointers to instances. If instances
       are in a file or are fed through a filter, they are copied to a
       table. Even if they are already in a table, they are copied if
       :obj:`store_instances` is `True`.
    #. Apriori class probabilities are computed. If the sum
       of instance weights is zero, there are no instances so the process
       stops. A list of candidate attributes for the split is compiled;
       in the beginning, all attributes are candidates.
    #. The recursive part. Its
       arguments are a set of instances, a weight meta-attribute ID
       (it can be always the same as the original or can change to
       accomodate splitting of instances among branches), apriori class
       distribution and a list of candidates (represented as a vector
       of Boolean values).
    #. The contingency matrix is computed.  
    #. A :obj:`stop` is called
       to see whether it is worth to continue. If not, a
       :obj:`~Node.node_classifier` is built and the :obj:`Node` is
       returned. Otherwise, a :obj:`~Node.node_classifier` is only built if
       :obj:`store_node_classifier` is `True`.  The :obj:`~Node.node_classifier`
       is build by calling :obj:`node_learner`'s :obj:`smart_learn`
       function with the given instances, weight ID and the just computed
       matrix. If the learner can use the matrix (and the default,
       :obj:`~Orange.classification.majority.MajorityLearner`, can), it
       won't touch the instances. Therefore a :obj:`contingency_computer`
       will, in many cases, affect the :obj:`~Node.node_classifier`. The
       :obj:`node_learner` can return no classifier; if so and
       if the classifier would be needed for classification, the
       :obj:`TreeClassifier`'s function returns DK or an empty
       distribution.
    #. If the induction is to continue, a :obj:`split` is called.
       If it fails to return a branch selector, induction stops and the
       :obj:`Node` is returned.
    #. Instances are divided (into child nodes) with :obj:`splitter`.
    #. The contingency gets removed if :obj:`store_contingencies` is
       `False`.  Thus, :obj:`split`, :obj:`stop` and :obj:`splitter`
       can use the contingency matrices.
    #. The object recursively calls itself (see step 3) for each of
       the non-empty subsets. If the splitter returnes a list of weights,
       a corresponding weight is used for each branch. The attribute spent
       by the splitter (if any) is removed from the list of candidates
       for the subtree.
    #. A subset of instances is stored in its corresponding tree node,
       if :obj:`store_instances` is `True`. If not, the new weight
       attributes are removed (if any were created).

    **Attributes**

    .. attribute:: node_learner

        Induces a classifier from instances in a node, both
        used for internal nodes and leaves. The default is
        :obj:`Orange.classification.majority.MajorityLearner`.

    .. attribute:: descender

        Descending component that the induces :obj:`TreeClassifier` will
        use. Default descender is :obj:`Descender_UnknownMergeAsSelector`
        which votes using the :obj:`branch_selector`'s distribution for
        vote weights.

    **Split construction**

    .. attribute:: split
        
        A :obj:`SplitConstructor` or a function with the same signature as
        :obj:`SplitConstructor.__call__`. It is useful for prototyping
        new tree induction algorithms. When defined, other parameters
        that affect  the split construction are ignored. These include
        :obj:`binarization`, :obj:`measure`, :obj:`worst_acceptable` and
        :obj:`min_subset`. Default: :class:`SplitConstructor_Combined`
        with separate constructors for discrete and continuous
        attributes.  Discrete attributes are used as they are, while
        continuous attributes are binarized.  Gain ratio is used to select
        attributes.  A minimum of two instances in a leaf is required for
        discrete and five instances in a leaf for continuous attributes.

    .. attribute:: binarization

        If 1, :class:`SplitConstructor_ExhaustiveBinary` is used.
        If 2, use :class:`SplitConstructor_OneAgainstOthers`. If
        0, do not use binarization (use :class:`SplitConstructor_Feature`).
        Default: 0.

    .. attribute:: measure
    
        Measure for scoring of the attributes when deciding which of the
        attributes will be used for splitting of the instances in a node.
        A subclass of :class:`Orange.feature.scoring.Score` (perhaps
        :class:`~Orange.feature.scoring.InfoGain`, 
        :class:`~Orange.feature.scoring.GainRatio`, 
        :class:`~Orange.feature.scoring.Gini`,
        :class:`~Orange.feature.scoring.Relief`, or
        :class:`~Orange.feature.scoring.MSE`). Default: :class:`Orange.feature.scoring.GainRatio`.

    .. attribute:: relief_m, relief_k

        Set `m` and `k` for Relief, if chosen.

    .. attribute:: splitter

        :class:`Splitter`  or a function with the same
        signature as :obj:`Splitter.__call__`. The default is
        :class:`Splitter_UnknownsAsSelector` that splits the
        learning instances according to distributions given by the
        selector.

    .. attribute:: contingency_computer
    
        Used to change the way the contingency matrices (used
        by :class:`SplitConstructor` and :class:`StopCriteria`) are
        computed, for example, to change the treatment of unknown values.
        By default ordinary contingency matrices are computed for
        instances at each node.

    **Pruning**

    .. attribute:: worst_acceptable

        Used in pre-pruning, sets the lowest required attribute
        score. If the score of the best attribute is below this margin, the
        tree at that node is not grown further (default: 0).

        So, to allow splitting only when gain ratio (the default measure)
        is greater than 0.6, set :samp:`worst_acceptable=0.6`.

    .. attribute:: min_subset

        The smalles number of instances in non-null leaves (default: 0).

    .. attribute:: min_instances

        Data subsets with less than :obj:`min_instances`
        instances are not split any further, that is, all leaves in the tree
        will contain at least that many instances (default: 0).

    .. attribute:: max_depth

        Gives maximal tree depth;  0 means that only root is generated. 
        The default is 100. 

    .. attribute:: max_majority

        Induction stops when the proportion of majority class in the
        node exceeds the value set by this parameter (default: 1.0). 
  
    .. attribute:: stop

        :class:`StopCriteria` or a function with the same signature as
        :obj:`StopCriteria.__call__`. Useful for prototyping new tree
        induction algorithms.  When used, parameters  :obj:`max_majority`
        and :obj:`min_instances` will not be  considered.  The default
        stopping criterion stops induction when all instances in a node
        belong to the same class.

    .. attribute:: m_pruning

        If non-zero, invokes an error-based bottom-up post-pruning,
        where m-estimate is used to estimate class probabilities 
        (default: 0).

    .. attribute:: same_majority_pruning

        If true, invokes a bottom-up post-pruning by removing the
        subtrees of which all leaves classify to the same class
        (default: False).

    **Record keeping**

    .. attribute:: store_distributions 
    
    .. attribute:: store_contingencies
    
    .. attribute:: store_instances
    
    .. attribute:: store_node_classifier

        Determines whether to store class distributions, contingencies and
        examples in :class:`Node`, and whether the :obj:`Node.node_classifier`
        should be build for internal nodes.  No memory will be saved 
        by not storing distributions but storing contingencies, since
        distributions actually points to the same distribution that is
        stored in :obj:`contingency.classes`.  By default everything
        except :obj:`store_instances` is enabled. 

    """
    def __new__(cls, examples = None, weightID = 0, **argkw):
        self = Orange.core.Learner.__new__(cls, **argkw)
        if examples:
            self.__init__(**argkw)
            return self.__call__(examples, weightID)
        else:
            return self
    
    def __init__(self, **kw):

        #name, buildfunction, parameters
        #buildfunctions are not saved as function references
        #because that would make problems with object copies
        for n,(fn,_) in self._built_fn.items():
            self.__dict__["_handset_" + n] = False

        #measure has to be before split
        self.measure = None
        self.split = None
        self.stop = None
        self.splitter = None
        
        for n,(fn,_) in self._built_fn.items():
            self.__dict__[n] = fn(self)

        for k,v in kw.items():
            self.__setattr__(k,v)
      
    def __call__(self, instances, weight=0):
        """
        Return a classifier from the given instances.
        """
        bl = self._base_learner()

        #set the scoring criteria for regression if it was not
        #set by the user
        if not self._handset_split and not self.measure:
            measure = fscoring.GainRatio() \
                if instances.domain.class_var.var_type == Orange.data.Type.Discrete \
                else fscoring.MSE()
            bl.split.continuous_split_constructor.measure = measure
            bl.split.discrete_split_constructor.measure = measure
         
        if self.splitter != None:
            bl.example_splitter = self.splitter

        #post pruning
        tree = bl(instances, weight)
        if getattr(self, "same_majority_pruning", 0):
            tree = Pruner_SameMajority(tree)
        if getattr(self, "m_pruning", 0):
            tree = Pruner_m(tree, m=self.m_pruning)

        return TreeClassifier(base_classifier=tree) 

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        for n,(fn,v) in self._built_fn.items():
            if name in v:
                if not self.__dict__["_handset_" + n]:
                    self.__dict__[n] = fn(self)
                else:
                    warnings.warn("Changing \"" + name + "\" does not have any effect as \"" + n + "\" was already set", UserWarning, 2)
            elif n == name:
                if value == None:
                    self.__dict__[n] = fn(self)
                    self.__dict__["_handset_" + n] = False
                    #print n, "was now disabled by hand"
                else:
                    self.__dict__["_handset_" + n] = True
                    #print n, "is now handset"
        #print self.__dict__

    def __delattr__(self, name):
        self.__setattr__(name, None) #use the __setattr__
        del self.__dict__[name]

    def instance(self):
        """
        DEPRECATED. Return a base learner - an object 
        of :class:`_TreeLearner`. 
        This method is left for backwards compatibility.
        """
        return self._base_learner()

    def _build_split(self):
        """
        Return the split constructor built according to object attributes.
        """
        split = SplitConstructor_Combined()
        split.continuous_split_constructor = \
            SplitConstructor_Threshold()
        binarization = getattr(self, "binarization", 0)
        if binarization == 1:
            split.discrete_split_constructor = \
                SplitConstructor_ExhaustiveBinary()
        elif binarization == 2:
            split.discrete_split_constructor = \
                SplitConstructor_OneAgainstOthers()
        else:
            split.discrete_split_constructor = \
                SplitConstructor_Feature()

        measures = {"infoGain": fscoring.InfoGain,
            "gainRatio": fscoring.GainRatio,
            "gini": fscoring.Gini,
            "relief": fscoring.Relief,
            "retis": fscoring.MSE
            }

        measure = self.measure
        if isinstance(measure, str):
            measure = measures[measure]()
        if not measure:
            measure = fscoring.GainRatio()

        measureIsRelief = isinstance(measure, fscoring.Relief)
        relM = getattr(self, "relief_m", None)
        if relM and measureIsRelief:
            measure.m = relM
        
        relK = getattr(self, "relief_k", None)
        if relK and measureIsRelief:
            measure.k = relK

        split.continuous_split_constructor.measure = measure
        split.discrete_split_constructor.measure = measure

        wa = getattr(self, "worst_acceptable", 0)
        if wa:
            split.continuous_split_constructor.worst_acceptable = wa
            split.discrete_split_constructor.worst_acceptable = wa

        ms = getattr(self, "min_subset", 0)
        if ms:
            split.continuous_split_constructor.min_subset = ms
            split.discrete_split_constructor.min_subset = ms

        return split

    def _build_stop(self):
        """
        Return the stop criteria built according to object's attributes.
        """
        stop = Orange.classification.tree.StopCriteria_common()
        mm = getattr(self, "max_majority", 1.0)
        if mm < 1.0:
            stop.max_majority = self.max_majority
        me = getattr(self, "min_instances", 0)
        if me:
            stop.min_examples = self.min_instances
        return stop

    def _base_learner(self):
        learner = _TreeLearner()

        learner.split = self.split
        learner.stop = self.stop

        for a in ["store_distributions", "store_contingencies",
            "store_node_classifier", "node_learner", "max_depth", "contingency_computer", "descender" ]:
            if hasattr(self, a):
                setattr(learner, a, getattr(self, a))

        if hasattr(self, "store_instances"):
            learner.store_examples = self.store_instances

        return learner

    _built_fn = { 
            "split": [ _build_split, [ "binarization", "measure", "relief_m", "relief_k", "worst_acceptable", "min_subset" ] ], \
            "stop": [ _build_stop, ["max_majority", "min_instances" ] ] 
        }



TreeLearner = Orange.misc.deprecated_members({
          "mForPruning": "m_pruning",
          "sameMajorityPruning": "same_majority_pruning",
          "reliefM": "relief_m",
          "reliefK": "relief_k",
          "storeDistributions": "store_distributions",
          "storeContingencies": "store_contingencies",
          "storeExamples": "store_instances",
          "store_examples": "store_instances",
          "storeNodeClassifier": "store_node_classifier",
          "worstAcceptable": "worst_acceptable",
          "minSubset": "min_subset",
          "maxMajority": "max_majority",
          "minExamples": "min_instances",
          "maxDepth": "max_depth",
          "nodeLearner": "node_learner",
          "min_examples": "min_instances"
}, wrap_methods=[])(TreeLearner)

#
# the following is for the output
#

fs = r"(?P<m100>\^?)(?P<fs>(\d*\.?\d*)?)"
""" Defines the multiplier by 100 (:samp:`^`) and the format
for the number of decimals (e.g. :samp:`5.3`). The corresponding 
groups are named :samp:`m100` and :samp:`fs`. """

by = r"(?P<by>(b(P|A)))?"
""" Defines bP or bA or nothing; the result is in groups by. """

bysub = r"((?P<bysub>b|s)(?P<by>P|A))?"
opc = r"(?P<op>=|<|>|(<=)|(>=)|(!=))(?P<num>\d*\.?\d+)"
opd = r'(?P<op>=|(!=))"(?P<cls>[^"]*)"'
intrvl = r'((\((?P<intp>\d+)%?\))|(\(0?\.(?P<intv>\d+)\))|)'
fromto = r"(?P<out>!?)(?P<lowin>\(|\[)(?P<lower>\d*\.?\d+)\s*,\s*(?P<upper>\d*\.?\d+)(?P<upin>\]|\))"
re_V = re.compile("%V")
re_N = re.compile("%"+fs+"N"+by)
re_M = re.compile("%"+fs+"M"+by)
re_m = re.compile("%"+fs+"m"+by)
re_Ccont = re.compile("%"+fs+"C"+by+opc)
re_Cdisc = re.compile("%"+fs+"C"+by+opd)
re_ccont = re.compile("%"+fs+"c"+by+opc)
re_cdisc = re.compile("%"+fs+"c"+by+opd)
re_Cconti = re.compile("%"+fs+"C"+by+fromto)
re_cconti = re.compile("%"+fs+"c"+by+fromto)
re_D = re.compile("%"+fs+"D"+by)
re_d = re.compile("%"+fs+"d"+by)
re_AE = re.compile("%"+fs+"(?P<AorE>A|E)"+bysub)
re_I = re.compile("%"+fs+"I"+intrvl)

def insert_str(s, mo, sub):
    """ Replace the part of s which is covered by mo 
    with the string sub. """
    return s[:mo.start()] + sub + s[mo.end():]

def insert_dot(s, mo):
    """ Replace the part of s which is covered by mo 
    with a dot.  You should use this when the 
    function cannot compute the desired quantity; it is called, for instance, 
    when it needs to divide by something in the parent, but the parent 
    doesn't exist.
    """
    return s[:mo.start()] + "." + s[mo.end():]

def insert_num(s, mo, n):
    """ Replace the part of s matched by mo with the number n, 
    formatted as specified by the user, that is, it multiplies 
    it by 100, if needed, and prints with the right number of 
    places and decimals. It does so by checking the mo
    for a group named m100 (representing the :samp:`^` in the format string) 
    and a group named fs representing the part giving the number o
    f decimals (e.g. :samp:`5.3`).
    """
    grps = mo.groupdict()
    m100 = grps.get("m100", None)
    if m100:
        n *= 100
    fs = grps.get("fs") or (m100 and ".0" or "5.3")
    return s[:mo.start()] + ("%%%sf" % fs % n) + s[mo.end():]

def by_whom(by, parent, tree):
    """ If by equals bp, return parent, else return
    :samp:`tree.tree`. This is used to find what to divide the quantity 
    with, when division is required.
    """
    if by=="bP":
        return parent
    else:
        return tree.tree

def replaceV(strg, mo, node, parent, tree):
    return insert_str(strg, mo, str(node.node_classifier.default_value))

def replaceN(strg, mo, node, parent, tree):
    by = mo.group("by")
    N = node.distribution.abs
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            if whom.distribution.abs > 1e-30:
                N /= whom.distribution.abs
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, N)
        

def replaceM(strg, mo, node, parent, tree):
    by = mo.group("by")
    maj = int(node.node_classifier.default_value)
    N = node.distribution[maj]
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            if whom.distribution[maj] > 1e-30:
                N /= whom.distribution[maj]
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, N)
        

def replacem(strg, mo, node, parent, tree):
    by = mo.group("by")
    maj = int(node.node_classifier.default_value)
    if node.distribution.abs > 1e-30:
        N = node.distribution[maj] / node.distribution.abs
        if by:
            if whom and whom.distribution:
                byN = whom.distribution[maj] / whom.distribution.abs
                if byN > 1e-30:
                    N /= byN
            else:
                return insert_dot(strg, mo)
    else:
        N = 0.
    return insert_num(strg, mo, N)


def replaceCdisc(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Discrete:
        return insert_dot(strg, mo)
    
    by, op, cls = mo.group("by", "op", "cls")
    N = node.distribution[cls]
    if op == "!=":
        N = node.distribution.abs - N
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            if whom.distribution[cls] > 1e-30:
                N /= whom.distribution[cls]
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, N)

    
def replacecdisc(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Discrete:
        return insert_dot(strg, mo)
    
    op, by, cls = mo.group("op", "by", "cls")
    N = node.distribution[cls]
    if node.distribution.abs > 1e-30:
        N /= node.distribution.abs
        if op == "!=":
            N = 1 - N
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            if whom.distribution[cls] > 1e-30:
                N /= whom.distribution[cls] / whom.distribution.abs
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, N)


__opdict = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "=": operator.eq, "!=": operator.ne}

def replaceCcont(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)
    
    by, op, num = mo.group("by", "op", "num")
    op = __opdict[op]
    num = float(num)
    N = sum([x[1] for x in node.distribution.items() if op(x[0], num)], 0.)
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            byN = sum([x[1] for x in whom.distribution.items() if op(x[0], num)], 0.)
            if byN > 1e-30:
                N /= byN
        else:
            return insert_dot(strg, mo)

    return insert_num(strg, mo, N)
    
    
def replaceccont(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)
    
    by, op, num = mo.group("by", "op", "num")
    op = __opdict[op]
    num = float(num)
    N = sum([x[1] for x in node.distribution.items() if op(x[0], num)], 0.)
    if node.distribution.abs > 1e-30:
        N /= node.distribution.abs
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            byN = sum([x[1] for x in whom.distribution.items() if op(x[0], num)], 0.)
            if byN > 1e-30:
                N /= byN/whom.distribution.abs # abs > byN, so byN>1e-30 => abs>1e-30
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, N)


def extractInterval(mo, dist):
    out, lowin, lower, upper, upin = mo.group("out", "lowin", "lower", "upper", "upin")
    lower, upper = float(lower), float(upper)
    if out:
        lop = lowin == "(" and operator.le or operator.lt
        hop = upin == ")" and operator.ge or operator.ge
        return filter(lambda x:lop(x[0], lower) or hop(x[0], upper), dist.items())
    else:
        lop = lowin == "(" and operator.gt or operator.ge
        hop = upin == ")" and operator.lt or operator.le
        return filter(lambda x:lop(x[0], lower) and hop(x[0], upper), dist.items())

    
def replaceCconti(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)

    by = mo.group("by")
    N = sum([x[1] for x in extractInterval(mo, node.distribution)])
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            byN = sum([x[1] for x in extractInterval(mo, whom.distribution)])
            if byN > 1e-30:
                N /= byN
        else:
            return insert_dot(strg, mo)
        
    return insert_num(strg, mo, N)

            
def replacecconti(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)

    N = sum([x[1] for x in extractInterval(mo, node.distribution)])
    ab = node.distribution.abs
    if ab > 1e-30:
        N /= ab

    by = mo.group("by")
    if by:
        whom = by_whom(by, parent, tree)
        if whom and whom.distribution:
            byN = sum([x[1] for x in extractInterval(mo, whom.distribution)])
            if byN > 1e-30:
                N /= byN/whom.distribution.abs
        else:
            return insert_dot(strg, mo)
        
    return insert_num(strg, mo, N)

    
def replaceD(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Discrete:
        return insert_dot(strg, mo)

    fs, by, m100 = mo.group("fs", "by", "m100")
    dist = list(node.distribution)
    if by:
        whom = by_whom(by, parent, tree)
        if whom:
            for i, d in enumerate(whom.distribution):
                if d > 1e-30:
                    dist[i] /= d
        else:
            return insert_dot(strg, mo)
    mul = m100 and 100 or 1
    fs = fs or (m100 and ".0" or "5.3")
    return insert_str(strg, mo, "["+", ".join(["%%%sf" % fs % (N*mul) for N in dist])+"]")


def replaced(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Discrete:
        return insert_dot(strg, mo)

    fs, by, m100 = mo.group("fs", "by", "m100")
    dist = list(node.distribution)
    ab = node.distribution.abs
    if ab > 1e-30:
        dist = [d/ab for d in dist]
    if by:
        whom = by_whom(by, parent, tree)
        if whom:
            for i, d in enumerate(whom.distribution):
                if d > 1e-30:
                    dist[i] /= d/whom.distribution.abs # abs > d => d>1e-30 => abs>1e-30
        else:
            return insert_dot(strg, mo)
    mul = m100 and 100 or 1
    fs = fs or (m100 and ".0" or "5.3")
    return insert_str(strg, mo, "["+", ".join(["%%%sf" % fs % (N*mul) for N in dist])+"]")


def replaceAE(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)

    AorE, bysub, by = mo.group("AorE", "bysub", "by")
    
    if AorE == "A":
        A = node.distribution.average()
    else:
        A = node.distribution.error()
    if by:
        whom = by_whom("b"+by, parent, tree)
        if whom:
            if AorE == "A":
                avg = whom.distribution.average()
            else:
                avg = whom.distribution.error()
            if bysub == "b":
                if avg > 1e-30:
                    A /= avg
            else:
                A -= avg
        else:
            return insert_dot(strg, mo)
    return insert_num(strg, mo, A)


Z = { 0.75:1.15, 0.80:1.28, 0.85:1.44, 0.90:1.64, 0.95:1.96, 0.99:2.58 }

def replaceI(strg, mo, node, parent, tree):
    if tree.class_var.var_type != Orange.data.Type.Continuous:
        return insert_dot(strg, mo)

    fs = mo.group("fs") or "5.3"
    intrvl = float(mo.group("intp") or mo.group("intv") or "95")/100.
    mul = mo.group("m100") and 100 or 1

    if not Z.has_key(intrvl):
        raise SystemError, "Cannot compute %5.3f% confidence intervals" % intrvl

    av = node.distribution.average()    
    il = node.distribution.error() * Z[intrvl]
    return insert_str(strg, mo, "[%%%sf-%%%sf]" % (fs, fs) % ((av-il)*mul, (av+il)*mul))


# This class is more a collection of function, merged into a class so 
# that they don't need to transfer too many arguments. It will be 
# constructed, used and discarded, it is not meant to store any information.
class _TreeDumper:
    defaultStringFormats = [(re_V, replaceV), (re_N, replaceN),
         (re_M, replaceM), (re_m, replacem), 
         (re_Cdisc, replaceCdisc), (re_cdisc, replacecdisc),
         (re_Ccont, replaceCcont), (re_ccont, replaceccont),
         (re_Cconti, replaceCconti), (re_cconti, replacecconti),
         (re_D, replaceD), (re_d, replaced), (re_AE, replaceAE), 
         (re_I, replaceI) ]

    def node(self):
        return self.tree.tree if "tree" in self.tree.__dict__ else self.tree

    def __init__(self, leafStr, nodeStr, stringFormats, minExamples, 
        maxDepth, simpleFirst, tree, **kw):
        self.stringFormats = stringFormats
        self.minExamples = minExamples
        self.maxDepth = maxDepth
        self.simpleFirst = simpleFirst
        self.tree = tree
        self.__dict__.update(kw)

        if leafStr:
            self.leafStr = leafStr
        else:
            if self.node().node_classifier.class_var.var_type == \
                    Orange.data.Type.Discrete:
                self.leafStr = "%V (%^.2m%)"
            else:
                self.leafStr = "%V"

        if nodeStr == ".":
            self.nodeStr = self.leafStr
        else:
            self.nodeStr = nodeStr
        

    def formatString(self, strg, node, parent):
        if hasattr(strg, "__call__"):
            return strg(node, parent, self.tree)
        
        if not node:
            return "<null node>"
        
        for rgx, replacer in self.stringFormats:
            if not node.distribution:
                strg = rgx.sub(".", strg)
            else:
                strt = 0
                while True:
                    mo = rgx.search(strg, strt)
                    if not mo:
                        break
                    strg = replacer(strg, mo, node, parent, self.tree)
                    strt = mo.start()+1
                        
        return strg
        

    def showBranch(self, node, parent, lev, i):
        bdes = node.branch_descriptions[i]
        bdes = node.branch_selector.class_var.name + \
            (bdes[0] not in "<=>" and "=" or "") + bdes
        if node.branches[i]:
            nodedes = self.nodeStr and ": " + \
                self.formatString(self.nodeStr, node.branches[i], node) or ""
        else:
            nodedes = "<null node>"
        return "|    "*lev + bdes + nodedes
        
        
    def dumpTree0(self, node, parent, lev):
        if node.branches:
            if node.distribution.abs < self.minExamples or \
                lev > self.maxDepth:
                return "|    "*lev + ". . .\n"
            
            res = ""
            if self.leafStr and self.nodeStr and self.leafStr != self.nodeStr:
                leafsep = "\n"+("|    "*lev)+"    "
            else:
                leafsep = ""
            if self.simpleFirst:
                for i, branch in enumerate(node.branches):
                    if not branch or not branch.branches:
                        if self.leafStr == self.nodeStr:
                            res += "%s\n" % \
                                self.showBranch(node, parent, lev, i)
                        else:
                            res += "%s: %s\n" % \
                                (self.showBranch(node, parent, lev, i),
                                 leafsep + 
                                 self.formatString(self.leafStr, branch, node))
            for i, branch in enumerate(node.branches):
                if branch and branch.branches:
                    res += "%s\n%s" % (self.showBranch(node, parent, lev, i),
                                       self.dumpTree0(branch, node, lev+1))
                elif not self.simpleFirst:
                    if self.leafStr == self.nodeStr:
                        res += "%s\n" % self.showBranch(node, parent, lev, i)
                    else:
                        res += "%s: %s\n" % \
                            (self.showBranch(node, parent, lev, i),
                             leafsep + 
                             self.formatString(self.leafStr, branch, node))
            return res
        else:
            return self.formatString(self.leafStr, node, parent)


    def dumpTree(self):
        node = self.node()
        if self.nodeStr:
            lev, res = 1, "root: %s\n" % \
                self.formatString(self.nodeStr, node, None)
            self.maxDepth += 1
        else:
            lev, res = 0, ""
        return res + self.dumpTree0(node, None, lev)
        

    def dotTree0(self, node, parent, internalName):
        if node.branches:
            if node.distribution.abs < self.minExamples or \
                len(internalName)-1 > self.maxDepth:
                self.fle.write('%s [ shape="plaintext" label="..." ]\n' % \
                    _quoteName(internalName))
                return
                
            label = node.branch_selector.class_var.name
            if self.nodeStr:
                label += "\\n" + self.formatString(self.nodeStr, node, parent)
            self.fle.write('%s [ shape=%s label="%s"]\n' % \
                (_quoteName(internalName), self.nodeShape, label))
            
            for i, branch in enumerate(node.branches):
                if branch:
                    internalBranchName = "%s-%d" % (internalName,i)
                    self.fle.write('%s -> %s [ label="%s" ]\n' % \
                        (_quoteName(internalName), 
                         _quoteName(internalBranchName), 
                         node.branch_descriptions[i]))
                    self.dotTree0(branch, node, internalBranchName)
                    
        else:
            self.fle.write('%s [ shape=%s label="%s"]\n' % \
                (_quoteName(internalName), self.leafShape, 
                self.formatString(self.leafStr, node, parent)))


    def dotTree(self, internalName="n"):
        self.fle.write("digraph G {\n")
        self.dotTree0(self.node(), None, internalName)
        self.fle.write("}\n")

def _quoteName(x):
    return '"%s"' % (base64.b64encode(x))

class TreeClassifier(Orange.classification.Classifier):
    """

    Classifies instances according to the tree stored in :obj:`tree`.

    **The classification process**

    :obj:`TreeClassifier` uses the :obj:`descender` to descend from
    the root.  If it returns only a :obj:`Node` and no distribution,
    the descend should stop; it does not matter whether it's a leaf
    (the first case above) or an internal node (the second case). The
    node's :obj:`~Node.node_classifier` is used to decide the class.

    If the descender returns a :obj:`Node` and a distribution,
    the :obj:`TreeClassifier` recursively calls itself for each of
    the subtrees and the predictions are weighted as requested by
    the descender. From now on, ``vote`` and ``class_distribution``
    (private methods) interweave down the tree.

    ``vote`` returns a normalized distribution  of predictions: for each
    node, it calls the  :obj:`class_distribution` and then multiplies
    and sums the distribution.  ``class_distribution`` gets an additional 
    parameter, a default
    tree root.  If :obj:`descender` reaches a leaf, it calls
    :obj:`~Node.node_classifier`, otherwise it calls ``vote``. Thus,
    ``vote`` and ``class_distribution`` form a double recursion. The
    recursive calls only happen at nodes where a vote is needed (that is,
    at nodes where the descender halts).

    **Attributes**

    .. attribute:: tree

        The root of the tree, represented as a :class:`Node`.

    .. attribute:: descender

        A :obj:`Descender`. It is used to descend an instance from the
        root of the tree (:obj:`tree`) as deeply as possible according
        to the instance's feature values.


    """
    
    def __init__(self, base_classifier=None):
        if not base_classifier: base_classifier = _TreeClassifier()
        self.nativeClassifier = base_classifier
        for k, v in self.nativeClassifier.__dict__.items():
            self.__dict__[k] = v
  
    def __call__(self, instance, result_type=Orange.classification.Classifier.GetValue,
                 *args, **kwdargs):
        """Classify a new instance.

      
        :param instance: instance to be classified.
        :type instance: :class:`Orange.data.Instance`
        :param result_type: 
              :class:`Orange.classification.Classifier.GetValue` or \
              :class:`Orange.classification.Classifier.GetProbabilities` or
              :class:`Orange.classification.Classifier.GetBoth`
        
        :rtype: :class:`Orange.data.Value`, 
              :class:`Orange.statistics.Distribution` or a tuple with both
        """
        return self.nativeClassifier(instance, result_type, *args, **kwdargs)

    def __setattr__(self, name, value):
        if name == "nativeClassifier":
            self.__dict__[name] = value
            return
        if name in self.nativeClassifier.__dict__:
            self.nativeClassifier.__dict__[name] = value
        self.__dict__[name] = value
    
    def __str__(self):
        return self.dump()

    @Orange.misc.deprecated_keywords({"fileName": "file_name", \
        "leafStr": "leaf_str", "nodeStr": "node_str", \
        "userFormats": "user_formats", "minExamples": "min_examples", \
        "maxDepth": "max_depth", "simpleFirst": "simple_first"})
    def dump(self, leaf_str = "", node_str = "", \
            user_formats=[], min_examples=0, max_depth=1e10, \
            simple_first=True):
        """
        Return a string representation of a tree.

        :arg leaf_str: The format string for the tree leaves. If 
          left empty, "%V (%^.2m%)" will be used for classification trees
          and "%V" for regression trees.
        :type leaf_str: string
        :arg node_str: The format string for the internal nodes.
          If left empty (as it is by default), no data is printed out for
          internal nodes. If set to :samp:`"."`, the same string is
          used as for leaves.
        :type node_str: string
        :arg max_depth: If set, it limits the depth to which the tree is
          printed out.
        :type max_depth: integer
        :arg min_examples: If set, the subtrees with less than the given 
          number of examples are not printed.
        :type min_examples: integer
        :arg simple_first: If True (default), the branches with a single 
          node are printed before the branches with larger subtrees. 
          If False, the branches are printed in order of
          appearance.
        :type simple_first: boolean
        :arg user_formats: A list of regular expressions and callback 
          function through which the user can print out other specific 
          information in the nodes.
        """
        return _TreeDumper(leaf_str, node_str, user_formats + 
            _TreeDumper.defaultStringFormats, min_examples, 
            max_depth, simple_first, self).dumpTree()

    @Orange.misc.deprecated_keywords({"fileName": "file_name", \
        "leafStr": "leaf_str", "nodeStr": "node_str", \
        "leafShape": "leaf_shape", "nodeShape": "node_shape", \
        "userFormats": "user_formats", "minExamples": "min_examples", \
        "maxDepth": "max_depth", "simpleFirst": "simple_first"})
    def dot(self, fileName, leaf_str = "", node_str = "", \
            leaf_shape="plaintext", node_shape="plaintext", \
            user_formats=[], min_examples=0, max_depth=1e10, \
            simple_first=True):
        """ Print the tree to a file in a format used by `GraphViz
        <http://www.research.att.com/sw/tools/graphviz>`_.  Uses the
        same parameters as :meth:`dump` plus two which define the shape
        of internal nodes and leaves of the tree:

        :param leaf_shape: Shape of the outline around leaves of the tree. 
            If "plaintext", no outline is used (default: "plaintext").
        :type leaf_shape: string
        :param node_shape: Shape of the outline around internal nodes 
            of the tree. If "plaintext", no outline is used (default: "plaintext")
        :type node_shape: string

        Check `Polygon-based Nodes <http://www.graphviz.org/doc/info/shapes.html>`_ 
        for various outlines supported by GraphViz.
        """
        fle = type(fileName) == str and open(fileName, "wt") or fileName

        _TreeDumper(leaf_str, node_str, user_formats + 
            _TreeDumper.defaultStringFormats, min_examples, 
            max_depth, simple_first, self,
            leafShape=leaf_shape, nodeShape=node_shape, fle=fle).dotTree()

    def count_nodes(self):
        """
        Return the number of nodes.
        """
        return _countNodes(self.tree)

    def count_leaves(self):
        """
        Return the number of leaves.
        """
        return _countLeaves(self.tree)

def _countNodes(node):
    count = 0
    if node:
        count += 1
        if node.branches:
            for node in node.branches:
                count += _countNodes(node)
    return count

def _countLeaves(node):
    count = 0
    if node:
        if node.branches: # internal node
            for node in node.branches:
                count += _countLeaves(node)
        else:
            count += 1
    return count

