/*
    This file is part of Orange.

    Orange is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Orange is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Orange; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Authors: Janez Demsar, Blaz Zupan, 1996--2002
    Contact: miha.stajdohar@fri.uni-lj.si
*/

#include "ppp/network.ppp"

TNetwork::TNetwork(TGraphAsList *graph)
: TGraphAsList(graph->nVertices, graph->nEdgeTypes, graph->directed)
{
  optimize.clear();
  vector<int> vertices;
  vector<int> neighbours;
	for(int v1 = 0; v1 < graph->nVertices; v1++) {
		graph->getNeighboursFrom_Single(v1, neighbours);

		ITERATE(vector<int>, ni, neighbours) {
      double *w = getOrCreateEdge(v1, *ni);
			*w = *graph->getOrCreateEdge(v1, *ni);
		}

    vertices.push_back(v1);
    optimize.insert(v1);
	}

  hierarchy.setTop(vertices);
}

TNetwork::TNetwork(const int &nVert, const int &nEdge, const bool dir)
: TGraphAsList(nVert, nEdge, dir)
{
  optimize.clear();
  vector<int> vertices;
  int i;
  for (i = 0; i < nVert; i++)
  {
    vertices.push_back(i);
    optimize.insert(i);
  }

  hierarchy.setTop(vertices);
}

TNetwork::~TNetwork()
{

}

void TNetwork::hideVertices(vector<int> vertices)
{
  for (vector<int>::iterator it = vertices.begin(); it != vertices.end(); ++it) 
	{
    optimize.erase(*it);
  }
}

void TNetwork::showVertices(vector<int> vertices)
{
  for (vector<int>::iterator it = vertices.begin(); it != vertices.end(); ++it) 
	{
    optimize.insert(*it);
  }
}

void TNetwork::showAll()
{
  optimize.clear();
  int i;
  for (i = 0; i < nVertices; i++)
  {
    optimize.insert(i);
  }
}

void TNetwork::printHierarchy()
{
  hierarchy.printChilds(hierarchy.top);
  cout << endl;
}

TNetworkHierarchyNode::TNetworkHierarchyNode()
{
	parent = NULL;
  vertex = INT_MIN;
}

TNetworkHierarchyNode::~TNetworkHierarchyNode()
{
  int i;
  for (i = 0; i < childs.size(); i++)
  {
    if (childs[i])
    {
      delete childs[i]; 
    }
  }
}

int TNetworkHierarchyNode::getLevel()
{
  int level = 0;
  TNetworkHierarchyNode *next_parent = parent;
  
  while (next_parent != NULL)
  {
    if (next_parent->parent == NULL)
      next_parent = NULL;
    else
      next_parent = next_parent->parent;
    level++;
  }
  
  return level;
}

TNetworkHierarchy::TNetworkHierarchy()
{
	top = new TNetworkHierarchyNode();
  meta_index = 0;
  top->vertex = getNextMetaIndex();
  top->parent = NULL;
}

TNetworkHierarchy::TNetworkHierarchy(vector<int> &topVertices)
{
	top = new TNetworkHierarchyNode();
  meta_index = 0;
  top->vertex = getNextMetaIndex();
  top->parent = NULL;
	setTop(topVertices);
}

TNetworkHierarchy::~TNetworkHierarchy()
{
	if (top)
	{
		delete top;
	}
}

int TNetworkHierarchy::getNextMetaIndex()
{
  meta_index--;
  return meta_index;
}

int TNetworkHierarchy::getMetaChildsCount(TNetworkHierarchyNode *node)
{
  int rv = 0;
  int i;
  
  for (i = 0; i < node->childs.size(); i++)
  {
    if (node->childs[i]->vertex < 0)
      rv++;

    rv += getMetaChildsCount(node->childs[i]);
  }

  return rv;
}

int TNetworkHierarchy::getMetasCount()
{
  return getMetaChildsCount(top);
}

void TNetworkHierarchy::printChilds(TNetworkHierarchyNode *node)
{
  if (node->childs.size() > 0)
  {
    cout << node->vertex << " | ";
    int i;
    for (i = 0; i < node->childs.size(); i++)
    {
      cout << node->childs[i]->vertex << " ";
    }

    cout << endl;

    for (i = 0; i < node->childs.size(); i++)
    {
      printChilds(node->childs[i]);
    }
  }
}

void TNetworkHierarchy::setTop(vector<int> &vertices)
{
	top->childs.clear();
  top->parent = NULL;

	for (vector<int>::iterator it = vertices.begin(); it != vertices.end(); ++it) 
	{
    TNetworkHierarchyNode *child = new TNetworkHierarchyNode();
    
    child->vertex = *it;
    child->parent = top;

    top->childs.push_back(child);
	}
}

void TNetworkHierarchy::addToNewMeta(vector<int> &vertices)
{
  vector<TNetworkHierarchyNode *> nodes;
  int i;
  TNetworkHierarchyNode *highest_parent = NULL;
  for (i = 0; i < vertices.size(); i++)
  {
    TNetworkHierarchyNode *node = getNodeByVertex(vertices[i]);
    nodes.push_back(node);
    if (highest_parent)
    {
      if (node->parent && highest_parent->getLevel() > node->parent->getLevel())
      {
        highest_parent = node->parent;
      }
    }
    else
    {
      highest_parent = node->parent;
    }
  }
  
  TNetworkHierarchyNode *meta = new TNetworkHierarchyNode();
  meta->parent = highest_parent;
  meta->vertex = getNextMetaIndex();
  highest_parent->childs.push_back(meta);

  for (i = 0; i < nodes.size(); i++)
  {
    for (vector<TNetworkHierarchyNode *>::iterator it = nodes[i]->parent->childs.begin(); it != nodes[i]->parent->childs.end(); ++it) 
	  {
      if ((*it)->vertex == nodes[i]->vertex)
      {
        nodes[i]->parent->childs.erase(it);

        // TODO: erase meta-nodes with 1 or 0 childs
      }
    }

    nodes[i]->parent = meta;
    meta->childs.push_back(nodes[i]);
  }
}

void TNetworkHierarchy::expandMeta(int meta)
{
  TNetworkHierarchyNode *metaNode = getNodeByVertex(meta);

  int i;
  for (i = 0; i < metaNode->childs.size(); i++)
  {
    TNetworkHierarchyNode *node = node->childs[i];

    node->parent = metaNode->parent;
    metaNode->parent->childs.push_back(node);
  }

  // erase meta from parent
  for (vector<TNetworkHierarchyNode *>::iterator it = metaNode->parent->childs.begin(); it != metaNode->parent->childs.end(); ++it) 
  {
    if ((*it)->vertex == metaNode->vertex)
    {
      metaNode->parent->childs.erase(it);
      break;
    }
  }

  metaNode->childs.clear();
  metaNode->parent = NULL;
}

TNetworkHierarchyNode *TNetworkHierarchy::getNodeByVertex(int vertex, TNetworkHierarchyNode &start)
{
  int i;
  for (i = 0; i < start.childs.size(); i++)
  {
    if (start.childs[i]->vertex == vertex)
    {
      return start.childs[i];
    }
    else
    {
      TNetworkHierarchyNode *child = getNodeByVertex(vertex, *start.childs[i]);

      if (child)
      {
        return child;
      }
    }
  }

  return NULL;
}

TNetworkHierarchyNode *TNetworkHierarchy::getNodeByVertex(int vertex)
{
  return getNodeByVertex(vertex, *top);
}

#include "externs.px"
#include "orange_api.hpp"
WRAPPER(GraphAsList);
PyObject *Network_new(PyTypeObject *type, PyObject *args, PyObject *kwds) BASED_ON (GraphAsList, "(nVertices, directed[, nEdgeTypes])")
{
	PyTRY
		int nVertices, directed, nEdgeTypes = 1;
    PyObject *pygraph;
    
    if (PyArg_ParseTuple(args, "O:Network", &pygraph))
    {
      if (!PyOrGraphAsList_Check(pygraph))
      {
        PyErr_Format(PyExc_TypeError, "Network.__new__: an instance of GraphAsList expected got '%s'", pygraph->ob_type->tp_name);
        return PYNULL;
      }

      TGraphAsList *graph = PyOrange_AsGraphAsList(pygraph).getUnwrappedPtr();

      TNetwork *network = mlnew TNetwork(graph);

      // set graphs attribut items of type ExampleTable to subgraph
      PyObject *strItems = PyString_FromString("items");

		  if (PyObject_HasAttr(pygraph, strItems) == 1)
		  {
			  PyObject* items = PyObject_GetAttr(pygraph, strItems);
        network->items = &dynamic_cast<TExampleTable &>(PyOrange_AsOrange(items).getReference());
      }

	  Py_DECREF(strItems);

      return WrapNewOrange(network, type);
    }
    
    PyErr_Clear();
    
    if (PyArg_ParseTuple(args, "ii|i:Network", &nVertices, &directed, &nEdgeTypes))
    {
		  return WrapNewOrange(mlnew TNetwork(nVertices, nEdgeTypes, directed != 0), type);
    }

    PYERROR(PyExc_TypeError, "Network.__new__: number of vertices directedness and optionaly, number of edge types expected", PYNULL);
	
	PyCATCH
}

PyObject *Network_printHierarchy(PyObject *self, PyObject *) PYARGS(METH_NOARGS, "None -> None")
{
  PyTRY
    CAST_TO(TNetwork, network);
    network->printHierarchy();
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_printNodeByVertex(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(vertex) -> None")
{
  PyTRY
    int vertexNdx;

    if (!PyArg_ParseTuple(args, "i:Network.printNodeByVertex", &vertexNdx))
		  return PYNULL;

    CAST_TO(TNetwork, network);
    TNetworkHierarchyNode* vertex = network->hierarchy.getNodeByVertex(vertexNdx);
    cout << "vertex: " << vertex->vertex << endl;
    cout << "n of childs: " << vertex->childs.size() << endl;
    cout << "level: " << vertex->getLevel() << endl;
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_groupVerticesInHierarchy(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(List of vertices) -> None")
{
  PyTRY
    PyObject *pyVertices;

    if (!PyArg_ParseTuple(args, "O:Network.groupVerticesInHierarchy", &pyVertices))
		  return PYNULL;

    int size = PyList_Size(pyVertices);
    int i;
		vector<int> vertices;
		for (i = 0; i < size; i++)
		{
      int vertex = PyInt_AsLong(PyList_GetItem(pyVertices, i));
      vertices.push_back(vertex);
    }

    CAST_TO(TNetwork, network);
    network->hierarchy.addToNewMeta(vertices);
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_expandMeta(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(index) -> None")
{
  PyTRY
    int meta;

    if (!PyArg_ParseTuple(args, "u:Network.groupVerticesInHierarchy", &meta))
		  return PYNULL;

    CAST_TO(TNetwork, network);
    network->hierarchy.expandMeta(meta);
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_hideVertices(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(List of vertices) -> None")
{
  PyTRY
    PyObject *pyVertices;

    if (!PyArg_ParseTuple(args, "O:Network.hideVertices", &pyVertices))
		  return PYNULL;

    int size = PyList_Size(pyVertices);
    int i;
		vector<int> vertices;
		for (i = 0; i < size; i++)
		{
      int vertex = PyInt_AsLong(PyList_GetItem(pyVertices, i));
      vertices.push_back(vertex);
    }

    CAST_TO(TNetwork, network);
    network->hideVertices(vertices);
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_showVertices(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(List of vertices) -> None")
{
  PyTRY
    PyObject *pyVertices;

    if (!PyArg_ParseTuple(args, "O:Network.showVertices", &pyVertices))
		  return PYNULL;

    int size = PyList_Size(pyVertices);
    int i;
		vector<int> vertices;
		for (i = 0; i < size; i++)
		{
      int vertex = PyInt_AsLong(PyList_GetItem(pyVertices, i));
      vertices.push_back(vertex);
    }

    CAST_TO(TNetwork, network);
    network->showVertices(vertices);
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_showAll(PyObject *self, PyObject *) PYARGS(METH_NOARGS, "None -> None")
{
  PyTRY
    CAST_TO(TNetwork, network);
    network->showAll();
    RETURN_NONE
  PyCATCH;
}

PyObject *Network_getVisible(PyObject *self, PyObject *) PYARGS(METH_NOARGS, "None -> None")
{
  PyTRY
    CAST_TO(TNetwork, network);

    PyObject *pyVisible = PyList_New(0);

    for (set<int>::iterator it = network->optimize.begin(); it != network->optimize.end(); ++it) 
	  {
      PyObject *nel = Py_BuildValue("i", *it);
			PyList_Append(pyVisible, nel);
			Py_DECREF(nel);
    }

	  return pyVisible;
  PyCATCH;
}

#include "network.px"