""" 
.. index:: MultikNN Learner
   
.. index:: 
   single: multilabel;  MultikNN Learner

***************************************
MultikNN Learner
***************************************

MultikNN Classification is the base class of kNN method based multi-label
classification. 
It is an adaptation of the kNN lazy learning algorithm for multi-label data. 
For more information, see Zhang, M. and Zhou, Z. 2007. `ML-KNN: A lazy learning
approach to multi-label learning <http://dx.doi.org/10.1016/j.patcog.2006.12.019>`_. 
Pattern Recogn. 40, 7 (Jul. 2007), 2038-2048.  

.. index:: MultikNN Learner
.. autoclass:: Orange.multilabel.MultikNNLearner
   :members:
   :show-inheritance:
 
   .. method:: __new__(instances, **argkw) 
   MLkNNLearner Constructor
   
   :param instances: a table of instances.
   :type instances: :class:`Orange.data.Table`

.. index:: MLkNN Classifier
.. autoclass:: Orange.multilabel.MLkNNClassifier
   :members:
   :show-inheritance:

   .. method:: __call__(self, example, result_type)
   :rtype: a list of :class:`Orange.data.Value`, 
              :class:`Orange.statistics.Distribution` or a tuple with both 
   
Examples
========

The following example demonstrates a straightforward invocation of
this algorithm (`mlc-classify.py`_, uses `multidata.tab`_):

.. literalinclude:: code/mlc-classify.py
   :lines: 1-3, 24-27

.. _mlc-classify.py: code/mlc-example.py
.. _multidata.tab: code/multidata.tab

"""
import random

import Orange
import multibase as _multibase

class MultikNNLearner(_multibase.MultiLabelLearner):
    """
    Class implementing the MultikNN (Multi-Label k Nearest Neighbours) algorithm. 
    
    .. attribute:: k
    
        Number of neighbors. The default value is 1 
    
    .. attribute:: num_labels
    
        Number of labels
    
    .. attribute:: label_indices
    
        The indices of labels in the domain 
    
    .. attribute:: knn
        
        :class:`Orange.classification.knn.FindNearest` for nearest neighbor search
    
    """
    def __new__(cls, k=1, **argkw):
        """
        Constructor of MultikNNLearner
                
        :param k: number of nearest neighbors used in classification
        :type k: int
        
        :rtype: :class:`MultikNNLearner`
        """
        
        self = _multibase.MultiLabelLearner.__new__(cls, **argkw)
        self.k = k
        return self
    
    def _build_knn(self, instances):
        nnc = Orange.classification.knn.FindNearestConstructor()
        nnc.distanceConstructor = Orange.core.ExamplesDistanceConstructor_Euclidean()
        
        weight_id = Orange.core.newmetaid()
        self.knn = nnc(instances, 0, weight_id)
        self.weight_id = weight_id

class MultikNNClassifier(_multibase.MultiLabelClassifier):   
    pass
        