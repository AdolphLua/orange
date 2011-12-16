.. py:currentmodule:: Orange.data

================================
Symmetric matrix (``SymMatrix``)
================================

:obj:`SymMatrix` implements symmetric matrices of size fixed at 
construction time (and stored in :obj:`SymMatrix.dim`).

.. class:: SymMatrix

    .. attribute:: dim
	
        Matrix dimension.
            
    .. attribute:: matrix_type 

        Can be ``SymMatrix.Lower`` (0), ``SymMatrix.Upper`` (1), 
        ``SymMatrix.Symmetric`` (2, default), ``SymMatrix.Lower_Filled`` (3) or
        ``SymMatrix.Upper_Filled`` (4). 

        If the matrix type is ``Lower`` or ``Upper``, indexing 
        above or below the diagonal, respectively, will fail. 
        With ``Lower_Filled`` and ``Upper_Filled``,
        the elements upper or lower, respectively, still 
        exist and are set to zero, but they cannot be modified. The 
        default matrix type is ``Symmetric``, but can be changed 
        at any time.

        If matrix type is ``Upper``, it is printed as:

        >>> m.matrix_type = m.Upper
        >>> print m
        (( 1.000,  2.000,  3.000,  4.000),
         (         4.000,  6.000,  8.000),
         (                 9.000, 12.000),
         (                        16.000))

        Changing the type to ``Lower_Filled`` changes the printout to

        >>> m.matrix_type = m.Lower_Filled
        >>> print m
        (( 1.000,  0.000,  0.000,  0.000),
         ( 2.000,  4.000,  0.000,  0.000),
         ( 3.000,  6.000,  9.000,  0.000),
         ( 4.000,  8.000, 12.000, 16.000))
	
    .. method:: __init__(dim[, default_value])

        Construct a symmetric matrix of the given dimension.

        :param dim: matrix dimension
        :type dim: int

        :param default_value: default value (0 by default)
        :type default_value: double
        
        
    .. method:: __init__(instances)

        Construct a new symmetric matrix containing the given data instances. 
        These can be given as Python list containing lists or tuples.

        :param instances: data instances
        :type instances: list of lists
        
        The following example fills a matrix created above with
        data in a list::

            import Orange
            m = [[],
                 [ 3],
                 [ 2, 4],
                 [17, 5, 4],
                 [ 2, 8, 3, 8],
                 [ 7, 5, 10, 11, 2],
                 [ 8, 4, 1, 5, 11, 13],
                 [ 4, 7, 12, 8, 10, 1, 5],
                 [13, 9, 14, 15, 7, 8, 4, 6],
                 [12, 10, 11, 15, 2, 5, 7, 3, 1]]
                    
            matrix = Orange.data.SymMatrix(m)

        SymMatrix also stores diagonal elements. They are set
        to zero, if they are not specified. The missing elements
        (shorter lists) are set to zero as well. If a list
        spreads over the diagonal, the constructor checks
        for asymmetries. For instance, the matrix

        ::

            m = [[],
                 [ 3,  0, f],
                 [ 2,  4]]
    
        is only OK if f equals 2. Finally, no row can be longer 
        than matrix size.  

    .. method:: get_values()
    
        Return all matrix values in a Python list.

    .. method:: get_KNN(i, k)
    
        Return k columns with the lowest value in the i-th row. 
        
        :param i: i-th row
        :type i: int
        
        :param k: number of neighbors
        :type k: int
        
    .. method:: avg_linkage(clusters)
    
        Return a symmetric matrix with average distances between given clusters.  
      
        :param clusters: list of clusters
        :type clusters: list of lists
        
    .. method:: invert(type)
    
        Invert values in the symmetric matrix.
        
        :param type: 0 (-X), 1 (1 - X), 2 (max - X), 3 (1 / X)
        :type type: int

    .. method:: normalize(type)
    
        Normalize values in the symmetric matrix.
        
        :param type: 0 (normalize to [0, 1] interval), 1 (Sigmoid)
        :type type: int
        
        
-------------------
Indexing
-------------------

For symmetric matrices the order of indices is not important: 
if ``m`` is a SymMatrix, then ``m[2, 4]`` addresses the same element as ``m[4, 2]``.

.. literalinclude:: code/symmatrix.py
    :lines: 1-6

Although only the lower left half of the matrix was set explicitely, 
the whole matrix is constructed.

>>> print m
(( 1.000,  2.000,  3.000,  4.000),
 ( 2.000,  4.000,  6.000,  8.000),
 ( 3.000,  6.000,  9.000, 12.000),
 ( 4.000,  8.000, 12.000, 16.000))
 
Entire rows are indexed with a single index. They can be iterated
over in a for loop or sliced (with, for example, ``m[:3]``):

>>> print m[1]
(3.0, 6.0, 9.0, 0.0)
>>> m.matrix_type = m.Lower
>>> for row in m:
...     print row
(1.0,)
(2.0, 4.0)
(3.0, 6.0, 9.0)
(4.0, 8.0, 12.0, 16.0)

