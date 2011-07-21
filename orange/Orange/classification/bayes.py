import Orange
from Orange.core import BayesClassifier as _BayesClassifier
from Orange.core import BayesLearner as _BayesLearner


class NaiveLearner(Orange.classification.Learner):
    """
    Probabilistic classifier based on applying Bayes' theorem (from Bayesian
    statistics) with strong (naive) independence assumptions.
    If data instances are provided to the constructor, the learning algorithm
    is called and the resulting classifier is returned instead of the learner.
    
    ..
        :param adjust_threshold: sets the corresponding attribute
        :type adjust_threshold: boolean
        :param m: sets the :obj:`estimatorConstructor` to
            :class:`orange.ProbabilityEstimatorConstructor_m` with specified m
        :type m: integer
        :param estimator_constructor: sets the corresponding attribute
        :type estimator_constructor: orange.ProbabilityEstimatorConstructor
        :param conditional_estimator_constructor: sets the corresponding attribute
        :type conditional_estimator_constructor:
                :class:`orange.ConditionalProbabilityEstimatorConstructor`
        :param conditional_estimator_constructor_continuous: sets the corresponding
                attribute
        :type conditional_estimator_constructor_continuous: 
                :class:`orange.ConditionalProbabilityEstimatorConstructor`
                
    :rtype: :class:`Orange.classification.bayes.NaiveLearner` or
            :class:`Orange.classification.bayes.NaiveClassifier`
            
    Constructor parameters set the corresponding attributes.
    
    .. attribute:: adjust_threshold
    
        If set and the class is binary, the classifier's
        threshold will be set as to optimize the classification accuracy.
        The threshold is tuned by observing the probabilities predicted on
        learning data. Setting it to True can increase the
        accuracy considerably
        
    .. attribute:: m
    
        m for m-estimate. If set, m-estimation of probabilities
        will be used using :class:`orange.ProbabilityEstimatorConstructor_m`.
        This attribute is ignored if you also set estimatorConstructor.
        
    .. attribute:: estimator_constructor
    
        Probability estimator constructor for
        prior class probabilities. Defaults to
        :class:`orange.ProbabilityEstimatorConstructor_relative`.
        Setting this attribute disables the above described attribute m.
        
    .. attribute:: conditional_estimator_constructor
    
        Probability estimator constructor
        for conditional probabilities for discrete features. If omitted,
        the estimator for prior probabilities will be used.
        
    .. attribute:: conditional_estimator_constructor_continuous
    
        Probability estimator constructor for conditional probabilities for
        continuous features. Defaults to 
        :class:`orange.ConditionalProbabilityEstimatorConstructor_loess`.
    """
    
    def __new__(cls, instances = None, weight_id = 0, **argkw):
        self = Orange.classification.Learner.__new__(cls, **argkw)
        if instances:
            self.__init__(**argkw)
            return self.__call__(instances, weight_id)
        else:
            return self
        
    def __init__(self, adjust_threshold=False, m=0, estimator_constructor=None,
                 conditional_estimator_constructor=None,
                 conditional_estimator_constructor_continuous=None,**argkw):
        self.adjust_threshold = adjust_threshold
        self.m = m
        self.estimator_constructor = estimator_constructor
        self.conditional_estimator_constructor = conditional_estimator_constructor
        self.conditional_estimator_constructor_continuous = conditional_estimator_constructor_continuous
        self.__dict__.update(argkw)

    def __call__(self, instances, weight=0):
        """Learn from the given table of data instances.
        
        :param instances: Data instances to learn from.
        :type instances: Orange.data.Table
        :param weight: Id of meta attribute with weights of instances
        :type weight: integer
        :rtype: :class:`Orange.classification.bayes.NaiveBayesClassifier`
        """
        bayes = _BayesLearner()
        if self.estimator_constructor:
            bayes.estimator_constructor = self.estimator_constructor
            if self.m:
                if not hasattr(bayes.estimator_constructor, "m"):
                    raise AttributeError, "invalid combination of attributes: 'estimator_constructor' does not expect 'm'"
                else:
                    self.estimator_constructor.m = self.m
        elif self.m:
            bayes.estimator_constructor = Orange.core.ProbabilityEstimatorConstructor_m(m = self.m)
        if self.conditional_estimator_constructor:
            bayes.conditional_estimator_constructor = self.conditional_estimator_constructor
        elif bayes.estimator_constructor:
            bayes.conditional_estimator_constructor = Orange.core.ConditionalProbabilityEstimatorConstructor_ByRows()
            bayes.conditional_estimator_constructor.estimator_constructor=bayes.estimator_constructor
        if self.conditional_estimator_constructor_continuous:
            bayes.conditional_estimator_constructor_continuous = self.conditional_estimator_constructor_continuous
        if self.adjust_threshold:
            bayes.adjust_threshold = self.adjust_threshold
        return NaiveClassifier(bayes(instances, weight))
NaiveLearner = Orange.misc.deprecated_members(
{     "adjustThreshold": "adjust_threshold",
      "estimatorConstructor": "estimator_constructor",
      "conditionalEstimatorConstructor": "conditional_estimator_constructor",
      "conditionalEstimatorConstructorContinuous":"conditional_estimator_constructor_continuous",
      "weightID": "weight_id"
}, in_place=True)(NaiveLearner)


class NaiveClassifier(Orange.classification.Classifier):
    """
    Predictor based on calculated probabilities. It wraps an
    :class:`Orange.core.BayesClassifier` that does the actual classification.
    
    :param base_classifier: an :class:`Orange.core.BayesLearner` to wrap. If
            not set, a new :class:`Orange.core.BayesLearner` is created.
    :type base_classifier: :class:`Orange.core.BayesLearner`
    
    .. attribute:: distribution
    
        Stores probabilities of classes, i.e. p(C) for each class C.
        
    .. attribute:: estimator
    
        An object that returns a probability of class p(C) for a given class C.
        
    .. attribute:: conditional_distributions
    
        A list of conditional probabilities.
        
    .. attribute:: conditional_estimators
    
        A list of estimators for conditional probabilities.
        
    .. attribute:: adjust_threshold
    
        For binary classes, this tells the learner to
        determine the optimal threshold probability according to 0-1
        loss on the training set. For multiple class problems, it has
        no effect.
    """
    
    def __init__(self, base_classifier=None):
        if not base_classifier: base_classifier = _BayesClassifier()
        self.native_bayes_classifier = base_classifier
        for k, v in self.native_bayes_classifier.__dict__.items():
            self.__dict__[k] = v
  
    def __call__(self, instance, result_type=Orange.classification.Classifier.GetValue,
                 *args, **kwdargs):
        """Classify a new instance.
        
        :param instance: instance to be classified.
        :type instance: :class:`Orange.data.Instance`
        :param result_type: :class:`Orange.classification.Classifier.GetValue` or \
              :class:`Orange.classification.Classifier.GetProbabilities` or
              :class:`Orange.classification.Classifier.GetBoth`
        
        :rtype: :class:`Orange.data.Value`, 
              :class:`Orange.statistics.Distribution` or a tuple with both
        """
        return self.native_bayes_classifier(instance, result_type, *args, **kwdargs)

    def __setattr__(self, name, value):
        if name == "native_bayes_classifier":
            self.__dict__[name] = value
            return
        if name in self.native_bayes_classifier.__dict__:
            self.native_bayes_classifier.__dict__[name] = value
        self.__dict__[name] = value
    
    def p(self, class_, instance):
        """
        Return probability of a single class.
        Probability is not normalized and can be different from probability
        returned from __call__.
        
        :param class_: class variable for which the probability should be
                output.
        :type class_: :class:`Orange.data.Variable`
        :param instance: instance to be classified.
        :type instance: :class:`Orange.data.Instance`
        
        """
        return self.native_bayes_classifier.p(class_, instance)
    
    def __str__(self):
        """Return classifier in human friendly format."""
        nvalues=len(self.class_var.values)
        frmtStr=' %10.3f'*nvalues
        classes=" "*20+ ((' %10s'*nvalues) % tuple([i[:10] for i in self.class_var.values]))
        
        return "\n".join([
            classes,
            "class probabilities "+(frmtStr % tuple(self.distribution)),
            "",
            "\n".join(["\n".join([
                "Attribute " + i.variable.name,
                classes,
                "\n".join(
                    ("%20s" % i.variable.values[v][:20]) + (frmtStr % tuple(i[v]))
                    for v in xrange(len(i.variable.values)))]
                ) for i in self.conditional_distributions
                        if i.variable.var_type == Orange.data.variable.Discrete])])
            

def printModel(model):
    print NaiveClassifier(model)
