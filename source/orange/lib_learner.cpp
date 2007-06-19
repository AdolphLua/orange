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
    Contact: janez.demsar@fri.uni-lj.si
*/


#ifdef _MSC_VER
  #pragma warning (disable : 4786 4114 4018 4267 4244)
#endif

#include "vars.hpp"
#include "domain.hpp"
#include "examples.hpp"
#include "examplegen.hpp"
#include "nearest.hpp"
#include "estimateprob.hpp"
#include "induce.hpp"
#include "cost.hpp"
#include "measures.hpp"
#include "distance.hpp"
#include "contingency.hpp"

#include "callback.hpp"

#include "cls_orange.hpp"
#include "cls_value.hpp"
#include "cls_example.hpp"
#include "lib_kernel.hpp"

#include "converts.hpp"

#include "vectortemplates.hpp"
#include "slist.hpp"

#include "externs.px"

/* ************ MAJORITY AND COST ************ */

#include "majority.hpp" 
C_CALL(MajorityLearner, Learner, "([examples] [, weight=, estimate=]) -/-> Classifier")
C_CALL(CostLearner, Learner, "([examples] [, weight=, estimate=, costs=]) -/-> Classifier")

//#include "linreg.hpp"
PYXTRACT_IGNORE C_CALL(LinRegLearner, Learner, "([examples] [, weight=]) -/-> Classifier")
PYXTRACT_IGNORE C_NAMED(LinRegClassifier, ClassifierFD, "([classifier=, costs=])")

PYCLASSCONSTANT_INT(LinRegLearner, All, 0)
PYCLASSCONSTANT_INT(LinRegLearner, Forward, 1)
PYCLASSCONSTANT_INT(LinRegLearner, Backward, 2)
PYCLASSCONSTANT_INT(LinRegLearner, Stepwise, 3)

#include "costwrapper.hpp"
C_CALL(CostWrapperLearner, Learner, "([examples] [, weight=, costs=]) -/-> Classifier")
C_NAMED(CostWrapperClassifier, Classifier, "([classifier=, costs=])")


/************* ASSOCIATION RULES ************/

#include "assoc.hpp"
C_CALL(AssociationLearner, Learner, "([examples] [, weight=, conf=, supp=, voteWeight=]) -/-> Classifier")
C_NAMED(AssociationClassifier, ClassifierFD, "([rules=, voteWeight=])")
C_CALL3(AssociationRulesInducer, AssociationRulesInducer, Orange, "([examples[, weightID]], confidence=, support=]) -/-> AssociationRules")
C_CALL3(AssociationRulesSparseInducer, AssociationRulesSparseInducer, Orange, "([examples[, weightID]], confidence=, support=]) -/-> AssociationRules")


bool operator < (const TAssociationRule &, const TAssociationRule &) { return false; }
bool operator > (const TAssociationRule &, const TAssociationRule &) { return false; }

PyObject *AssociationRulesInducer_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(examples[, weightID]) -> AssociationRules")
{
  PyTRY
    NO_KEYWORDS

    int weightID;
    PExampleGenerator egen = exampleGenFromArgs(args, weightID);
    if (!egen)
      return PYNULL;

    return WrapOrange(SELF_AS(TAssociationRulesInducer)(egen, weightID));
  PyCATCH
}


PyObject *AssociationRulesSparseInducer_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(examples[, weightID]) -> AssociationRules")
{
  PyTRY
    NO_KEYWORDS

    int weightID = 0;
    PExampleGenerator egen =  exampleGenFromArgs(args, weightID);
    if (!egen)
      return PYNULL;

    return WrapOrange(SELF_AS(TAssociationRulesSparseInducer)(egen, weightID));
  PyCATCH
}


bool convertFromPython(PyObject *, PAssociationRule &);

PyObject *AssociationRule_new(PyTypeObject *type, PyObject *args, PyObject *) BASED_ON(Orange, "(left, right, support, confidence)")
{ PyTRY
    PAssociationRule rule;
    return  convertFromPython(args, rule) ? WrapOrange(rule) : PYNULL;
  PyCATCH
}

PyObject *AssociationRule__reduce__(PyObject *self)
{
  PyTRY
    CAST_TO(TAssociationRule, arule);
    return Py_BuildValue("O(NN)N", self->ob_type,
                                   Example_FromWrappedExample(arule->left),
                                   Example_FromWrappedExample(arule->right),
                                   packOrangeDictionary(self));
  PyCATCH                          
}


PyObject *AssociationRule_appliesLeft(PyObject *self, PyObject *arg, PyObject *) PYARGS(METH_O, "(example) -> bool")
{ PyTRY
    if (!PyOrExample_Check(arg))
      PYERROR(PyExc_TypeError, "attribute error (example expected)", PYNULL);
    
    CAST_TO(TAssociationRule, rule)
    return PyInt_FromLong(rule->appliesLeft(PyExample_AS_ExampleReference(arg)) ? 1 : 0);
  PyCATCH
}


PyObject *AssociationRule_appliesRight(PyObject *self, PyObject *arg, PyObject *) PYARGS(METH_O, "(example) -> bool")
{ PyTRY
    if (!PyOrExample_Check(arg))
      PYERROR(PyExc_TypeError, "attribute error (example expected)", PYNULL);
    
    CAST_TO(TAssociationRule, rule)
    return PyInt_FromLong(rule->appliesRight(PyExample_AS_ExampleReference(arg)) ? 1 : 0);
  PyCATCH
}


PyObject *AssociationRule_appliesBoth(PyObject *self, PyObject *arg, PyObject *) PYARGS(METH_O, "(example) -> bool")
{ PyTRY
    if (!PyOrExample_Check(arg))
      PYERROR(PyExc_TypeError, "attribute error (example expected)", PYNULL);
    
    CAST_TO(TAssociationRule, rule)
    return PyInt_FromLong(rule->appliesBoth(PyExample_AS_ExampleReference(arg)) ? 1 : 0);
  PyCATCH
}


PyObject *AssociationRule_native(PyObject *self)
{ PyTRY
    CAST_TO(TAssociationRule, rule)
    return Py_BuildValue("NNff", Example_FromWrappedExample(rule->left), Example_FromWrappedExample(rule->right), rule->support, rule->confidence);
  PyCATCH
}

bool convertFromPython(PyObject *obj, PAssociationRule &rule)
{ if (PyOrOrange_Check(obj))
    if (!PyOrange_AS_Orange(obj)) {
      rule = PAssociationRule();
      return true;
    }
    else if (PyOrAssociationRule_Check(obj)) {
      rule = PyOrange_AsAssociationRule(obj);
      return true;
    }

  TExample *le, *re;

  switch (PyTuple_Size(obj)) {
    case 6:
      float nAppliesLeft, nAppliesRight, nAppliesBoth, nExamples;
      if (PyArg_ParseTuple(obj, "O&O&ffff:convertFromPython(AssociationRule)", ptr_Example, &le, ptr_Example, &re, &nAppliesLeft, &nAppliesRight, &nAppliesBoth, &nExamples)) {
        PExample nle = mlnew TExample(*le);
        PExample nre = mlnew TExample(*re);
        rule = mlnew TAssociationRule(nle, nre, nAppliesLeft, nAppliesRight, nAppliesBoth, nExamples);
        return true;
      }
      else
        break;

    case 2:
    case 3:
    case 4: {
      float support = -1, confidence = -1;
      if (PyArg_ParseTuple(obj, "O&O&|ff:convertFromPython(AssociationRule)", ptr_Example, &le, ptr_Example, &re, &support, &confidence)) {
        PExample nle = mlnew TExample(*le);
        PExample nre = mlnew TExample(*re);
        rule = mlnew TAssociationRule(nle, nre);
        rule->support = support;
        rule->confidence = confidence;
        return true;
      }
      else
        break;
    }

    case 1: 
      if (PyArg_ParseTuple(obj, "O&:convertFromPython(AssociationRule)", cc_AssociationRule, &rule))
        return true;
      else
        break;
  }
    
  PYERROR(PyExc_TypeError, "invalid arguments", false);
}


string side2string(PExample ex)
{ string res;

  if (ex->domain->variables->empty())
    ITERATE(TMetaValues, mi, ex->meta) {
      if (res.length())
        res += " ";
      res += ex->domain->getMetaVar((*mi).first)->name;
    }

  else {
    string val;

    TVarList::const_iterator vi(ex->domain->variables->begin());
    for(TExample::const_iterator ei(ex->begin()), ee(ex->end()); ei!=ee; ei++, vi++)
      if (!(*ei).isSpecial()) {
        if (res.length())
          res += " ";
        (*vi)->val2str(*ei, val);
        res += (*vi)->name + "=" + val;
      }
  }

  return res;
}

PyObject *AssociationRule_str(TPyOrange *self)
{ 
  PyObject *result = callbackOutput((PyObject *)self, NULL, NULL, "str", "repr");
  if (result)
    return result;

  CAST_TO(TAssociationRule, rule);
  return PyString_FromFormat("%s -> %s", side2string(rule->left).c_str(), side2string(rule->right).c_str());
}


PyObject *AssociationRule_repr(TPyOrange *self)
{ 
  PyObject *result = callbackOutput((PyObject *)self, NULL, NULL, "repr", "str");
  if (result)
    return result;

  CAST_TO(TAssociationRule, rule);
  return PyString_FromFormat("%s -> %s", side2string(rule->left).c_str(), side2string(rule->right).c_str());
}


PAssociationRules PAssociationRules_FromArguments(PyObject *arg) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::P_FromArguments(arg); }
PyObject *AssociationRules_FromArguments(PyTypeObject *type, PyObject *arg) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_FromArguments(type, arg); }
PyObject *AssociationRules_new(PyTypeObject *type, PyObject *arg, PyObject *kwds) BASED_ON(Orange, "(<list of AssociationRule>)")  ALLOWS_EMPTY { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_new(type, arg, kwds); }
PyObject *AssociationRules_getitem_sq(TPyOrange *self, int index) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_getitem(self, index); }
int       AssociationRules_setitem_sq(TPyOrange *self, int index, PyObject *item) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_setitem(self, index, item); }
PyObject *AssociationRules_getslice(TPyOrange *self, int start, int stop) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_getslice(self, start, stop); }
int       AssociationRules_setslice(TPyOrange *self, int start, int stop, PyObject *item) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_setslice(self, start, stop, item); }
int       AssociationRules_len_sq(TPyOrange *self) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_len(self); }
PyObject *AssociationRules_richcmp(TPyOrange *self, PyObject *object, int op) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_richcmp(self, object, op); }
PyObject *AssociationRules_concat(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_concat(self, obj); }
PyObject *AssociationRules_repeat(TPyOrange *self, int times) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_repeat(self, times); }
PyObject *AssociationRules_str(TPyOrange *self) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_str(self); }
PyObject *AssociationRules_repr(TPyOrange *self) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_str(self); }
int       AssociationRules_contains(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_contains(self, obj); }
PyObject *AssociationRules_append(TPyOrange *self, PyObject *item) PYARGS(METH_O, "(AssociationRule) -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_append(self, item); }
PyObject *AssociationRules_extend(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(sequence) -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_extend(self, obj); }
PyObject *AssociationRules_count(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(AssociationRule) -> int") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_count(self, obj); }
PyObject *AssociationRules_filter(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([filter-function]) -> AssociationRules") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_filter(self, args); }
PyObject *AssociationRules_index(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(AssociationRule) -> int") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_index(self, obj); }
PyObject *AssociationRules_insert(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "(index, item) -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_insert(self, args); }
PyObject *AssociationRules_native(TPyOrange *self) PYARGS(METH_NOARGS, "() -> list") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_native(self); }
PyObject *AssociationRules_pop(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "() -> AssociationRule") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_pop(self, args); }
PyObject *AssociationRules_remove(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(AssociationRule) -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_remove(self, obj); }
PyObject *AssociationRules_reverse(TPyOrange *self) PYARGS(METH_NOARGS, "() -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_reverse(self); }
PyObject *AssociationRules_sort(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([cmp-func]) -> None") { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_sort(self, args); }
PyObject *AssociationRules__reduce__(TPyOrange *self, PyObject *) { return ListOfWrappedMethods<PAssociationRules, TAssociationRules, PAssociationRule, &PyOrAssociationRule_Type>::_reduce(self); }

/************* CLASSIFICATION TREES ************/

#include "tdidt.hpp"
#include "tdidt_split.hpp"
#include "tdidt_stop.hpp"
#include "callback.hpp"

C_CALL(TreeLearner, Learner, "([examples] [, weight=, split=, stop=, nodeLearner=, lookDownOnUnknown=]) -/-> Classifier")

C_NAMED(TreeNode, Orange, "([lookDownOnUnknown=, branchSelector=, nodeClassifier=, branches=, contingency=])")
C_NAMED(TreeClassifier, ClassifierFD, "([domain=, tree=, descender=])")

C_NAMED(TreeStopCriteria_common, TreeStopCriteria, "([maxMajority=, minExamples=])")
HIDDEN(TreeStopCriteria_Python, TreeStopCriteria)
NO_PICKLE(TreeStopCriteria_Python)

C_CALL(TreeSplitConstructor_Combined, TreeSplitConstructor, "([examples, [weight, domainContingency, apriorClass, candidates] [discreteTreeSplitConstructor=, continuousTreeSplitConstructor=]) -/-> (Classifier, descriptions, sizes, quality)")

ABSTRACT(TreeSplitConstructor_Measure, TreeSplitConstructor)
C_CALL(TreeSplitConstructor_Attribute, TreeSplitConstructor_Measure, "([measure=, worstAcceptable=, minSubset=])")
C_CALL(TreeSplitConstructor_ExhaustiveBinary, TreeSplitConstructor_Measure, "([measure=, worstAcceptable=, minSubset=])")
C_CALL(TreeSplitConstructor_Threshold, TreeSplitConstructor_Measure, "([measure=, worstAcceptable=, minSubset=])")
PYXTRACT_IGNORE C_CALL(TreeSplitConstructor_LR, TreeSplitConstructor, "([minSubset=])")

BASED_ON(TreeExampleSplitter, Orange)

C_CALL(TreeExampleSplitter_IgnoreUnknowns, TreeExampleSplitter, "([node, examples[, weight]]) -/-> (ExampleGeneratorList, [list of weight ID's])")
C_CALL(TreeExampleSplitter_UnknownsToCommon, TreeExampleSplitter, "([node, examples[, weight]]) -/-> (ExampleGeneratorList, [list of weight ID's])")
C_CALL(TreeExampleSplitter_UnknownsToAll, TreeExampleSplitter, "([node, examples[, weight]]) -/-> (ExampleGeneratorList, [list of weight ID's])")
C_CALL(TreeExampleSplitter_UnknownsToRandom, TreeExampleSplitter, "([node, examples[, weight]]) -/-> (ExampleGeneratorList, [list of weight ID's])")
C_CALL(TreeExampleSplitter_UnknownsToBranch, TreeExampleSplitter, "([node, examples[, weight]]) -/-> (ExampleGeneratorList, [list of weight ID's])")

C_CALL(TreeExampleSplitter_UnknownsAsBranchSizes, TreeExampleSplitter, "([branchIndex, node, examples[, weight]]) -/-> (ExampleGenerator, [list of weight ID's])")
C_CALL(TreeExampleSplitter_UnknownsAsSelector, TreeExampleSplitter, "([branchIndex, node, examples[, weight]]) -/-> (ExampleGenerator, [list of weight ID's])")

C_CALL(TreeDescender_UnknownToBranch, TreeDescender, "(node, example) -/-> (node, {distribution | None})")
C_CALL(TreeDescender_UnknownToCommonBranch, TreeDescender, "(node, example) -/-> (node, {distribution | None})")
C_CALL(TreeDescender_UnknownToCommonSelector, TreeDescender, "(node, example) -/-> (node, {distribution | None})")
C_CALL(TreeDescender_UnknownMergeAsBranchSizes, TreeDescender, "(node, example) -/-> (node, {distribution | None})")
C_CALL(TreeDescender_UnknownMergeAsSelector, TreeDescender, "(node, example) -/-> (node, {distribution | None})")

ABSTRACT(TreePruner, Orange)
C_CALL (TreePruner_SameMajority, TreePruner, "([tree]) -/-> tree")
C_CALL (TreePruner_m, TreePruner, "([tree]) -/-> tree")


PyObject *TreeNode_treesize(PyObject *self, PyObject *, PyObject *) PYARGS(METH_NOARGS, "() -> int")
{ PyTRY
    return PyInt_FromLong(PyOrange_AsTreeNode(self)->treeSize());
  PyCATCH
}


PyObject *TreeNode_removestoredinfo(PyObject *self, PyObject *, PyObject *) PYARGS(METH_NOARGS, "() -> None")
{ PyTRY
    PyOrange_AsTreeNode(self)->removeStoredInfo();
    RETURN_NONE;
  PyCATCH
}


PyObject *TreeStopCriteria_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "()")
{ if (type == (PyTypeObject *)&PyOrTreeStopCriteria_Type) {
      PyObject *name=NULL;
      if (args && !PyArg_ParseTuple(args, "|O", &name))
        PYERROR(PyExc_TypeError, "TreeStopCriteria: invalid arguments - name or callback function expected", PYNULL);

      if (!args || !name || name && PyString_Check(name)) {
          PyObject *self = WrapNewOrange(mlnew TTreeStopCriteria(), type);
          if (name)
            PyObject_SetAttrString(self, "name", name);
          return self;
      }
      // (args && name && !PyStringString_Check(name)

      return setCallbackFunction(WrapNewOrange(mlnew TTreeStopCriteria_Python(), type), args);
  }

  return WrapNewOrange(mlnew TTreeStopCriteria_Python(), type);
}


/* This is all twisted: Python classes are derived from TreeStopCriteria;
   although the underlying C++ structure is TreeStopCriteria_Python,
   the Python base is always TreeStopCritera. We must therefore define
   TreeStopCriteria__reduce__ to handle both C++ objects, and need not
   define TreeStopCriteria_Python__reduce__
*/

PyObject *TreeStopCriteria__reduce__(PyObject *self)
{
  POrange orself = PyOrange_AS_Orange(self);

  if (orself.is_derived_from(TTreeStopCriteria_Python) && PyObject_HasAttrString(self, "__callback")) {
    PyObject *packed = packOrangeDictionary(self);
    PyObject *callback = PyDict_GetItemString(packed, "__callback");
    PyDict_DelItemString(packed, "__callback");
    return Py_BuildValue("O(O)N", self->ob_type, callback, packed);
  }

  /* This works for ordinary (not overloaded) TreeStopCriteria
     and for Python classes derived from TreeStopCriteria. 
     The latter have different self->ob_type, so TreeStopCriteria_new will construct
     an instance of TreeStopCriteria_Python */
  return Py_BuildValue("O()N", self->ob_type, packOrangeDictionary(self));
}


PyObject *TreeStopCriteria_lowcall(PyObject *self, PyObject *args, PyObject *keywords, bool allowPython)
{ 
  static TTreeStopCriteria _cbdefaultStop;
  PyTRY
    NO_KEYWORDS

    CAST_TO(TTreeStopCriteria, stop);
    if (!stop)
      PYERROR(PyExc_SystemError, "attribute error", PYNULL);

    PExampleGenerator egen;
    PDomainContingency dcont;
    int weight = 0;
    if (!PyArg_ParseTuple(args, "O&|O&O&:TreeStopCriteria.__call__", pt_ExampleGenerator, &egen, pt_weightByGen(egen), &weight, ptn_DomainContingency, &dcont))
      return PYNULL;

    bool res;

    if (allowPython || (stop->classDescription() != &TTreeStopCriteria_Python::st_classDescription))
      res = (*stop)(egen, weight, dcont);
    else
      res = _cbdefaultStop(egen, weight, dcont);

    return PyInt_FromLong(res ? 1 : 0);
  PyCATCH
}


PyObject *TreeStopCriteria_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("([examples, [weight, domainContingency]) -> bool")
{  return TreeStopCriteria_lowcall(self, args, keywords, false); }


PyObject *TreeStopCriteria_Python_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("([examples, [weight, domainContingency, apriorClass, candidates]) -/-> (Classifier, descriptions, sizes, quality)")
{ return TreeStopCriteria_lowcall(self, args, keywords, false); }



PyObject *TreeSplitConstructor_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrTreeSplitConstructor_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TTreeSplitConstructor_Python(), type), args);
  else
    return WrapNewOrange(mlnew TTreeSplitConstructor_Python(), type);
}


PyObject *TreeSplitConstructor__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrTreeSplitConstructor_Type);
}


PyObject *TreeSplitConstructor_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(examples[, weight, contingency, apriori class distribution, candidates, nodeClassifier]) -> (Classifier, descriptions, sizes, quality)")
{ PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrTreeSplitConstructor_Type) {
      PyErr_Format(PyExc_SystemError, "TreeSplitConstructor.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PExampleGenerator gen;
    int weightID = 0;
    PDomainContingency dcont;
    PDistribution apriori;
    PyObject *pycandidates = PYNULL;
    PClassifier nodeClassifier;

    if (!PyArg_ParseTuple(args, "O&|O&O&O&OO&:TreeSplitConstructor.call", pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, ccn_DomainContingency, &dcont, ccn_Distribution, &apriori, &pycandidates, ccn_Classifier, &nodeClassifier))
      return PYNULL;

    vector<bool> candidates;
    if (pycandidates) {
      PyObject *iterator = PyObject_GetIter(pycandidates);
      if (!iterator)
        PYERROR(PyExc_SystemError, "TreeSplitConstructor.call: cannot iterate through candidates; a list exected", PYNULL);
      for(PyObject *item = PyIter_Next(iterator); item; item = PyIter_Next(iterator)) {
        candidates.push_back(PyObject_IsTrue(item) != 0);
        Py_DECREF(item);
      }
      
      Py_DECREF(iterator);
      if (PyErr_Occurred())
        return PYNULL;
    }
    
    PClassifier branchSelector;
    PStringList descriptions;
    PDiscDistribution subsetSizes;
    float quality;
    int spentAttribute;

    branchSelector = SELF_AS(TTreeSplitConstructor)(descriptions, subsetSizes, quality, spentAttribute,
                                                    gen, weightID, dcont, apriori, candidates, nodeClassifier);

    return Py_BuildValue("NNNfi", WrapOrange(branchSelector), WrapOrange(descriptions), WrapOrange(subsetSizes), quality, spentAttribute);
  PyCATCH
}


PyObject *TreeExampleSplitter_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrTreeExampleSplitter_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TTreeExampleSplitter_Python(), type), args);
  else
    return WrapNewOrange(mlnew TTreeExampleSplitter_Python(), type);
}


PyObject *TreeExampleSplitter__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrTreeExampleSplitter_Type);
}


PyObject *TreeExampleSplitter_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(node, examples[, weight]) -/-> (ExampleGeneratorList, list of weight ID's")
{ PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrTreeExampleSplitter_Type) {
      PyErr_Format(PyExc_SystemError, "TreeExampleSplitter.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PTreeNode node;
    PExampleGenerator gen;
    int weightID = 0;

    if (!PyArg_ParseTuple(args, "O&O&|O&:TreeExampleSplitter.call", cc_TreeNode, &node, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID))
      return PYNULL;

    vector<int> newWeights;
    PExampleGeneratorList egl = SELF_AS(TTreeExampleSplitter)(node, gen, weightID, newWeights);

    if (newWeights.size()) {
      PyObject *pyweights = PyList_New(newWeights.size());
      int i = 0;
      ITERATE(vector<int>, li, newWeights)
        PyList_SetItem(pyweights, i++, PyInt_FromLong(*li));

      return Py_BuildValue("NN", WrapOrange(egl), pyweights);
    }

    else {
      return Py_BuildValue("NO", WrapOrange(egl), Py_None);
    }

  PyCATCH 
}



PyObject *TreeDescender_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrTreeDescender_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TMeasureAttribute_Python(), type), args);
  else
    return WrapNewOrange(mlnew TTreeDescender_Python(), type);
}


PyObject *TreeDescender__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrTreeDescender_Type);
}


PyObject *TreeDescender_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(node, example) -/-> (node, {distribution | None})")
{ PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrTreeDescender_Type) {
      PyErr_Format(PyExc_SystemError, "TreeDescender.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PTreeNode onode;
    TExample *example;
    if (!PyArg_ParseTuple(args, "O&O&", cc_TreeNode, &onode, ptr_Example, &example))
      PYERROR(PyExc_TypeError, "invalid parameters", PYNULL);

    PDiscDistribution distr;
    PTreeNode node = SELF_AS(TTreeDescender)(onode, *example, distr);
    return Py_BuildValue("NN", WrapOrange(node), WrapOrange(distr));
  PyCATCH
}


PyObject *TreePruner_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(tree) -> tree")
{ 
  PyTRY
    NO_KEYWORDS

    PyObject *obj;
    PTreeNode node;
    PTreeClassifier classifier;
    if (PyArg_ParseTuple(args, "O", &obj))
      if (PyOrTreeClassifier_Check(obj)) {
        classifier = PyOrange_AsClassifier(obj);
        node = classifier->tree;
      }
      else if (PyOrTreeNode_Check(obj))
        node = PyOrange_AsTreeNode(obj);

    if (!node)
      PYERROR(PyExc_TypeError, "invalid arguments (a classifier expected)", PYNULL);

    PTreeNode newRoot = SELF_AS(TTreePruner)(node);

    if (classifier) {
      PTreeClassifier newClassifier = CLONE(TTreeClassifier, classifier);
      newClassifier->tree = newRoot;
      return WrapOrange(newClassifier);
    }
    else
      return WrapOrange(newRoot);
  PyCATCH
}


PyObject *TreeClassifier_treesize(PyObject *self, PyObject *, PyObject *) PYARGS(METH_NOARGS, "() -> size")
{ PyTRY
    CAST_TO(TTreeClassifier, me);
    if (!me->tree)
      PYERROR(PyExc_SystemError, "TreeClassifier: 'tree' not defined", PYNULL);

    return PyInt_FromLong(long(me->tree->treeSize()));
  PyCATCH
}


PTreeNodeList PTreeNodeList_FromArguments(PyObject *arg) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::P_FromArguments(arg); }
PyObject *TreeNodeList_FromArguments(PyTypeObject *type, PyObject *arg) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_FromArguments(type, arg); }
PyObject *TreeNodeList_new(PyTypeObject *type, PyObject *arg, PyObject *kwds) BASED_ON(Orange, "(<list of TreeNode>)")  ALLOWS_EMPTY { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_new(type, arg, kwds); }
PyObject *TreeNodeList_getitem_sq(TPyOrange *self, int index) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_getitem(self, index); }
int       TreeNodeList_setitem_sq(TPyOrange *self, int index, PyObject *item) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_setitem(self, index, item); }
PyObject *TreeNodeList_getslice(TPyOrange *self, int start, int stop) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_getslice(self, start, stop); }
int       TreeNodeList_setslice(TPyOrange *self, int start, int stop, PyObject *item) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_setslice(self, start, stop, item); }
int       TreeNodeList_len_sq(TPyOrange *self) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_len(self); }
PyObject *TreeNodeList_richcmp(TPyOrange *self, PyObject *object, int op) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_richcmp(self, object, op); }
PyObject *TreeNodeList_concat(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_concat(self, obj); }
PyObject *TreeNodeList_repeat(TPyOrange *self, int times) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_repeat(self, times); }
PyObject *TreeNodeList_str(TPyOrange *self) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_str(self); }
PyObject *TreeNodeList_repr(TPyOrange *self) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_str(self); }
int       TreeNodeList_contains(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_contains(self, obj); }
PyObject *TreeNodeList_append(TPyOrange *self, PyObject *item) PYARGS(METH_O, "(TreeNode) -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_append(self, item); }
PyObject *TreeNodeList_extend(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(sequence) -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_extend(self, obj); }
PyObject *TreeNodeList_count(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(TreeNode) -> int") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_count(self, obj); }
PyObject *TreeNodeList_filter(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([filter-function]) -> TreeNodeList") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_filter(self, args); }
PyObject *TreeNodeList_index(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(TreeNode) -> int") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_index(self, obj); }
PyObject *TreeNodeList_insert(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "(index, item) -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_insert(self, args); }
PyObject *TreeNodeList_native(TPyOrange *self) PYARGS(METH_NOARGS, "() -> list") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_native(self); }
PyObject *TreeNodeList_pop(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "() -> TreeNode") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_pop(self, args); }
PyObject *TreeNodeList_remove(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(TreeNode) -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_remove(self, obj); }
PyObject *TreeNodeList_reverse(TPyOrange *self) PYARGS(METH_NOARGS, "() -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_reverse(self); }
PyObject *TreeNodeList_sort(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([cmp-func]) -> None") { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_sort(self, args); }
PyObject *TreeNodeList__reduce__(TPyOrange *self, PyObject *) { return ListOfWrappedMethods<PTreeNodeList, TTreeNodeList, PTreeNode, &PyOrTreeNode_Type>::_reduce(self); }

 
/************* C45 ************/

#include "c4.5.hpp"

C_CALL(C45Learner, Learner, "([examples] [, weight=, gainRatio=, subset=, batch=, probThresh=, minObjs=, window=, increment=, cf=, trials=]) -/-> Classifier")
C_NAMED(C45Classifier, Classifier, "()")

PyObject *C45Learner_commandline(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(line) -> None")
{ PyTRY
    char *line;
    if (!PyArg_ParseTuple(args, "s", &line))
      PYERROR(PyExc_TypeError, "C45Learner.commandline: string argument expected", NULL);

    SELF_AS(TC45Learner).parseCommandLine(string(line));
    RETURN_NONE;
  PyCATCH
}

C_NAMED(C45TreeNode, Orange, "")

PYCLASSCONSTANT_INT(C45TreeNode, Leaf, TC45TreeNode::Leaf)
PYCLASSCONSTANT_INT(C45TreeNode, Branch, TC45TreeNode::Branch)
PYCLASSCONSTANT_INT(C45TreeNode, Cut, TC45TreeNode::Cut)
PYCLASSCONSTANT_INT(C45TreeNode, Subset, TC45TreeNode::Subset)


PC45TreeNodeList PC45TreeNodeList_FromArguments(PyObject *arg) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::P_FromArguments(arg); }
PyObject *C45TreeNodeList_FromArguments(PyTypeObject *type, PyObject *arg) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_FromArguments(type, arg); }
PyObject *C45TreeNodeList_new(PyTypeObject *type, PyObject *arg, PyObject *kwds) BASED_ON(Orange, "(<list of C45TreeNode>)") ALLOWS_EMPTY { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_new(type, arg, kwds); }
PyObject *C45TreeNodeList_getitem_sq(TPyOrange *self, int index) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_getitem(self, index); }
int       C45TreeNodeList_setitem_sq(TPyOrange *self, int index, PyObject *item) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_setitem(self, index, item); }
PyObject *C45TreeNodeList_getslice(TPyOrange *self, int start, int stop) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_getslice(self, start, stop); }
int       C45TreeNodeList_setslice(TPyOrange *self, int start, int stop, PyObject *item) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_setslice(self, start, stop, item); }
int       C45TreeNodeList_len_sq(TPyOrange *self) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_len(self); }
PyObject *C45TreeNodeList_richcmp(TPyOrange *self, PyObject *object, int op) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_richcmp(self, object, op); }
PyObject *C45TreeNodeList_concat(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_concat(self, obj); }
PyObject *C45TreeNodeList_repeat(TPyOrange *self, int times) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_repeat(self, times); }
PyObject *C45TreeNodeList_str(TPyOrange *self) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_str(self); }
PyObject *C45TreeNodeList_repr(TPyOrange *self) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_str(self); }
int       C45TreeNodeList_contains(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_contains(self, obj); }
PyObject *C45TreeNodeList_append(TPyOrange *self, PyObject *item) PYARGS(METH_O, "(C45TreeNode) -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_append(self, item); }
PyObject *C45TreeNodeList_extend(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(sequence) -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_extend(self, obj); }
PyObject *C45TreeNodeList_count(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(C45TreeNode) -> int") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_count(self, obj); }
PyObject *C45TreeNodeList_filter(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([filter-function]) -> C45TreeNodeList") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_filter(self, args); }
PyObject *C45TreeNodeList_index(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(C45TreeNode) -> int") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_index(self, obj); }
PyObject *C45TreeNodeList_insert(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "(index, item) -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_insert(self, args); }
PyObject *C45TreeNodeList_native(TPyOrange *self) PYARGS(METH_NOARGS, "() -> list") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_native(self); }
PyObject *C45TreeNodeList_pop(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "() -> C45TreeNode") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_pop(self, args); }
PyObject *C45TreeNodeList_remove(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(C45TreeNode) -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_remove(self, obj); }
PyObject *C45TreeNodeList_reverse(TPyOrange *self) PYARGS(METH_NOARGS, "() -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_reverse(self); }
PyObject *C45TreeNodeList_sort(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([cmp-func]) -> None") { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_sort(self, args); }
PyObject *C45TreeNodeList__reduce__(TPyOrange *self, PyObject *) { return ListOfWrappedMethods<PC45TreeNodeList, TC45TreeNodeList, PC45TreeNode, &PyOrC45TreeNode_Type>::_reduce(self); }


/************* kNN ************/

#include "knn.hpp"
C_CALL(kNNLearner, Learner, "([examples] [, weight=, k=] -/-> Classifier")
C_NAMED(kNNClassifier, ClassifierFD, "([k=, weightID=, findNearest=])")


/************* PNN ************/

#include "numeric_interface.hpp"

#include "pnn.hpp"

PyObject *P2NN_new(PyTypeObject *type, PyObject *args, PyObject *keywords) BASED_ON(ClassifierFD, "(examples, anchors[, domain]) -> PNN")
{
  PyTRY
    PDomain domain;
    PExampleGenerator examples;
    PyObject *pybases;
    int normalizeExamples = 1;
    if (PyArg_ParseTuple(args, "O&O|iO&:P2NN", pt_ExampleGenerator, &examples, &pybases, &normalizeExamples, cc_Domain, &domain)) {
      if (!domain)
        domain = examples->domain;

      if (!PyList_Check(pybases))
        PYERROR(PyExc_AttributeError, "the anchors should be given as a list", PYNULL);

      const int nAnchors = PyList_Size(pybases);
      if (nAnchors != domain->attributes->size())
        PYERROR(PyExc_AttributeError, "the number of attributes does not match the number of anchors", PYNULL);

      TFloatList *basesX = mlnew TFloatList(nAnchors);
      TFloatList *basesY = mlnew TFloatList(nAnchors);
      PFloatList wbasesX = basesX, wbasesY = basesY;
   
      TFloatList::iterator xi(basesX->begin());
      TFloatList::iterator yi(basesY->begin());
      PyObject *foo;

      for(int i = 0; i < nAnchors; i++)
        if (!PyArg_ParseTuple(PyList_GetItem(pybases, i), "ff|O", &*xi++, &*yi++, &foo)) {
          PyErr_Format(PyExc_TypeError, "anchor #%i is not a tuple of (at least) two elements", i);
          return PYNULL;
        }

      return WrapNewOrange(mlnew TP2NN(domain, examples, wbasesX, wbasesY, -1.0, normalizeExamples != 0), type);
    }

      PyErr_Clear();
      PyObject *matrix;
      PyObject *pyoffsets, *pynormalizers, *pyaverages;
      if (PyArg_ParseTuple(args, "O&OOOOO|i", cc_Domain, &domain, &matrix, &pybases, &pyoffsets, &pynormalizers, &pyaverages, &normalizeExamples)) {
        prepareNumeric();
  //      if (!PyArray_Check(matrix))
  //        PYERROR(PyExc_AttributeError, "the second argument (projection matrix) must a Numeric.array", PYNULL);

        const int nAttrs = domain->attributes->size();

        PyArrayObject *array = (PyArrayObject *)(matrix);
        if (array->nd != 2)
          PYERROR(PyExc_AttributeError, "two-dimensional array expected for matrix of projections", PYNULL);
        if (array->dimensions[1] != 3)
          PYERROR(PyExc_AttributeError, "the matrix of projections must have three columns", PYNULL);
          
        const char arrayType = getArrayType(array);
        if ((arrayType != 'f') && (arrayType != 'd'))
          PYERROR(PyExc_AttributeError, "elements of matrix of projections must be doubles or floats", PYNULL);

        const int nExamples = array->dimensions[0];

        double *projections = new double[3*nExamples];

        char *rowPtr = array->data;
        double *pi = projections;
        const int &strideRow = array->strides[0];
        const int &strideCol = array->strides[1];

        if (arrayType == 'f') {
          for(int row = 0, rowe = nExamples; row < rowe; row++, rowPtr += strideRow) {
            *pi++ = double(*(float *)(rowPtr));
            *pi++ = double(*(float *)(rowPtr+strideCol));
            *pi++ = double(*(float *)(rowPtr+2*strideCol));
          }
        }
        else {
          for(int row = 0, rowe = nExamples; row < rowe; row++, rowPtr += strideRow) {
            *pi++ = *(double *)(rowPtr);
            *pi++ = *(double *)(rowPtr+strideCol);
            *pi++ = *(double *)(rowPtr+2*strideCol);
          }
        }


        double *bases = NULL;
        PFloatList offsets, normalizers, averages;

        if (pybases == Py_None) {
          if ((pyoffsets != Py_None) || (pynormalizers != Py_None) || (pyaverages != Py_None))
            PYERROR(PyExc_AttributeError, "anchors, offsets, normalizers and averages must be either all given or all None", PYNULL);
        }

        else {
          if (!PyList_Check(pybases) || ((pybases != Py_None) && (PyList_Size(pybases) != nAttrs)))
            PYERROR(PyExc_AttributeError, "the third argument must be a list of anchors with length equal the number of attributes", PYNULL);


          #define LOADLIST(x) \
          x = ListOfUnwrappedMethods<PAttributedFloatList, TAttributedFloatList, float>::P_FromArguments(py##x); \
          if (!x) return PYNULL; \
          if (x->size() != nAttrs) PYERROR(PyExc_TypeError, "invalid size of "#x" list", PYNULL);

          LOADLIST(offsets)
          LOADLIST(normalizers)
          LOADLIST(averages)
          #undef LOADLIST

          bases = new double[2*nAttrs];
          double *bi = bases;
          PyObject *foo;

          for(int i = 0; i < nAttrs; i++, bi+=2)
            if (!PyArg_ParseTuple(PyList_GetItem(pybases, i), "dd|O", bi, bi+1, &foo)) {
              PyErr_Format(PyExc_TypeError, "anchor #%i is not a tuple of (at least) two elements", i);
              delete bases;
              return PYNULL;
            }
        }

        return WrapNewOrange(mlnew TP2NN(domain, projections, nExamples, bases, offsets, normalizers, averages, TP2NN::InverseSquare, normalizeExamples != 0), type);
      }

    PyErr_Clear();
    PYERROR(PyExc_TypeError, "P2NN.invalid arguments", PYNULL);

  PyCATCH;
}


PyObject *P2NN__reduce__(PyObject *self)
{
  PyTRY
    CAST_TO(TP2NN, p2nn);

    if (!p2nn->offsets)
      PYERROR(PyExc_SystemError, "cannot pickle an invalid instance of P2NN (no offsets)", NULL);

    const int nAttrs = p2nn->offsets->size();
    const int nExamples = p2nn->nExamples;

    TCharBuffer buf(3 + 2 * sizeof(int) + (4 * nAttrs + 3 * nExamples + 2) * sizeof(double));

    buf.writeInt(nAttrs);
    buf.writeInt(nExamples);

    if (p2nn->bases) {
      buf.writeChar(1);
      buf.writeBuf(p2nn->bases, 2 * nAttrs * sizeof(double));
    }
    else
      buf.writeChar(0);

    if (p2nn->radii) {
      buf.writeChar(1);
      buf.writeBuf(p2nn->radii, 2 * nAttrs * sizeof(double));
    }
    else
      buf.writeChar(0);

    if (p2nn->projections) {
      buf.writeChar(1);
      buf.writeBuf(p2nn->projections, 3 * nExamples * sizeof(double));
    }
    else
      buf.writeChar(0);

    buf.writeDouble(p2nn->minClass);
    buf.writeDouble(p2nn->maxClass);
   
    return Py_BuildValue("O(Os#)N", getExportedFunction("__pickleLoaderP2NN"),
                                    self->ob_type,
                                    buf.buf, buf.length(),
                                    packOrangeDictionary(self));
  PyCATCH
}


PyObject *__pickleLoaderP2NN(PyObject *, PyObject *args) PYARGS(METH_VARARGS, "(type, packed_data)")
{
  PyTRY
    PyTypeObject *type;
    char *pbuf;
    int bufSize;
    if (!PyArg_ParseTuple(args, "Os#:__pickleLoaderP2NN", &type, &pbuf, &bufSize))    
      return NULL;

    TCharBuffer buf(pbuf);

    const int nAttrs = buf.readInt();
    const int nExamples = buf.readInt();

    TP2NN *p2nn = new TP2NN(nAttrs, nExamples);
    if (buf.readChar()) {
      buf.readBuf(p2nn->bases, 2 * nAttrs * sizeof(double));
    }
    else {
      delete p2nn->bases;
      p2nn->bases = NULL;
    }

    if (buf.readChar()) {
      buf.readBuf(p2nn->radii, 2 * nAttrs * sizeof(double));
    }
    else {
      delete p2nn->radii;
      p2nn->radii = NULL;
    }

    if (buf.readChar()) {
      buf.readBuf(p2nn->projections, 3 * nExamples * sizeof(double));
    }
    else {
      delete p2nn->projections;
      p2nn->projections = NULL;
    }

    p2nn->minClass = buf.readDouble();
    p2nn->maxClass = buf.readDouble();

    return WrapNewOrange(p2nn, type);
  PyCATCH
}


C_CALL(kNNLearner, Learner, "([examples] [, weight=, k=] -/-> Classifier")
C_NAMED(kNNClassifier, ClassifierFD, "([k=, weightID=, findNearest=])")


/************* Logistic Regression ************/

#include "logistic.hpp"
C_CALL(LogRegLearner, Learner, "([examples[, weight=]]) -/-> Classifier")
C_NAMED(LogRegClassifier, ClassifierFD, "([probabilities=])")


PyObject *LogRegFitter_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrLogRegFitter_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TLogRegFitter_Python(), type), args);
  else
    return WrapNewOrange(mlnew TLogRegFitter_Python(), type);
}

PyObject *LogRegFitter__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrLogRegFitter_Type);
}


C_CALL(LogRegFitter_Cholesky, LogRegFitter, "([example[, weightID]]) -/-> (status, beta, beta_se, likelihood) | (status, attribute)")

PYCLASSCONSTANT_INT(LogRegFitter, OK, TLogRegFitter::OK)
PYCLASSCONSTANT_INT(LogRegFitter, Infinity, TLogRegFitter::Infinity)
PYCLASSCONSTANT_INT(LogRegFitter, Divergence, TLogRegFitter::Divergence)
PYCLASSCONSTANT_INT(LogRegFitter, Constant, TLogRegFitter::Constant)
PYCLASSCONSTANT_INT(LogRegFitter, Singularity, TLogRegFitter::Singularity)

PyObject *LogRegLearner_fitModel(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(examples[, weight])")
{
  PyTRY
      PExampleGenerator egen;
      int weight = 0;
      if (!PyArg_ParseTuple(args, "O&|O&:LogRegLearner", pt_ExampleGenerator, &egen, pt_weightByGen(egen), &weight))
  	    return PYNULL;

	  CAST_TO(TLogRegLearner, loglearn)

	  int error;
	  PVariable variable;
	  PClassifier classifier;

	  classifier = loglearn->fitModel(egen, weight, error, variable);
	  if (error <= TLogRegFitter::Divergence)
		  return Py_BuildValue("N", WrapOrange(classifier));
	  else 
		  return Py_BuildValue("N", WrapOrange(variable));
  PyCATCH
}


PyObject *LogRegFitter_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(examples[, weightID]) -/-> (status, beta, beta_se, likelihood) | (status, attribute)")
{
  PyTRY
    NO_KEYWORDS

    int weight;
    PExampleGenerator egen = exampleGenFromArgs(args, weight);
    if (!egen)
      return PYNULL;

    CAST_TO(TLogRegFitter, fitter)

    PAttributedFloatList beta, beta_se;
    float likelihood;
    int error;
    PVariable attribute;
    
    beta = (*fitter)(egen, weight, beta_se, likelihood, error, attribute);

    if (error <= TLogRegFitter::Divergence)
      return Py_BuildValue("iNNf", error, WrapOrange(beta), WrapOrange(beta_se), likelihood);
    else
      return Py_BuildValue("iN", error, WrapOrange(attribute));

  PyCATCH
}

/************* SVM ************/

#include "svm.hpp"
C_CALL(SVMLearner, Learner, "([examples] -/-> Classifier)")
C_CALL(SVMLearnerSparse, SVMLearner, "([examples] -/-> Classifier)")
C_NAMED(SVMClassifier, Classifier," ")
C_NAMED(SVMClassifierSparse, SVMClassifier," ")
//N O _PICKLE(SVMClassifier)

PYCLASSCONSTANT_INT(SVMLearner, C_SVC, 0)
PYCLASSCONSTANT_INT(SVMLearner, NU_SVC, 1)
PYCLASSCONSTANT_INT(SVMLearner, ONE_CLASS, 2)
PYCLASSCONSTANT_INT(SVMLearner, EPSILON_SVR, 3)
PYCLASSCONSTANT_INT(SVMLearner, NU_SVR, 4)

PYCLASSCONSTANT_INT(SVMLearner, LINEAR, 0)
PYCLASSCONSTANT_INT(SVMLearner, POLY, 1)
PYCLASSCONSTANT_INT(SVMLearner, RBF, 2)
PYCLASSCONSTANT_INT(SVMLearner, SIGMOID, 3)
PYCLASSCONSTANT_INT(SVMLearner, CUSTOM, 4)


PyObject *KernelFunc_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrKernelFunc_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TKernelFunc_Python(), type), args);
  else
    return WrapNewOrange(mlnew TKernelFunc_Python(), type);
}


PyObject *KernelFunc__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrKernelFunc_Type);
}


PyObject *KernelFunc_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(Example, Example) -> float")
{
  PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrKernelFunc_Type) {
      PyErr_Format(PyExc_SystemError, "KernelFunc.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    float f;
    PExample e1,e2;
	if (!PyArg_ParseTuple(args, "O&O&", cc_Example, &e1, cc_Example, &e2))
		return NULL;
	f=SELF_AS(TKernelFunc)(e1.getReference(),e2.getReference());
	return Py_BuildValue("f", f);
  PyCATCH
}

PyObject *SVMClassifier__reduce__(PyObject* self)
{
  PyTRY
    //TCharBuffer buf(100);
    CAST_TO(TSVMClassifier, svm);
    string buf;
    if (svm_save_model_alt(buf, svm->getModel())){
        printf("error saving svm model");
    }
    if(svm->kernelFunc)
        return Py_BuildValue("O(OOOOsO)N", getExportedFunction("__pickleLoaderSVMClassifier"),
                                    self->ob_type,
                                    WrapOrange(svm->classVar),
                                    WrapOrange(svm->examples),
                                    WrapOrange(svm->supportVectors),
                                    buf.c_str(),
                                    WrapOrange(svm->kernelFunc),
                                    packOrangeDictionary(self));
    else
        return Py_BuildValue("O(OOOOs)N", getExportedFunction("__pickleLoaderSVMClassifier"),
                                    self->ob_type,
                                    WrapOrange(svm->classVar),
                                    WrapOrange(svm->examples),
                                    WrapOrange(svm->supportVectors),
                                    buf.c_str(),
                                    packOrangeDictionary(self));
  PyCATCH
}

PyObject *__pickleLoaderSVMClassifier(PyObject *, PyObject *args) PYARGS(METH_VARARGS, "(type, packed_data)")
{
  PyTRY
    PyTypeObject* type;
    PVariable var;
    PExampleTable examples;
    PExampleTable supportVectors;
    PKernelFunc kernel;
    char *pbuf;
    if (!PyArg_ParseTuple(args, "OO&O&O&s|O&:__pickleLoaderSVMClassifier", &type, cc_Variable, &var,
        cc_ExampleTable, &examples, cc_ExampleTable, &supportVectors, &pbuf, cc_KernelFunc, &kernel))
        return NULL;
    //TCharBuffer buf(pbuf);
    string buf(pbuf);
    printf("loading model\n");
    svm_model *model=svm_load_model_alt(buf);

    if (!model)
        raiseError("Error building LibSVM model");
    model->param.learner=NULL;
    PSVMClassifier svm=mlnew TSVMClassifier(var, examples, model, NULL);
    svm->kernelFunc=kernel;
    svm->supportVectors=supportVectors;
    return WrapOrange(svm);
  PyCATCH
}

PyObject *SVMClassifierSparse__reduce__(PyObject* self)
{
  PyTRY
    //TCharBuffer buf(100);
    CAST_TO(TSVMClassifierSparse, svm);
    string buf;
    if (svm_save_model_alt(buf, svm->getModel())){
        printf("error saving svm model");
    }
    if(svm->kernelFunc)
        return Py_BuildValue("O(OOOOsbO)N", getExportedFunction("__pickleLoaderSVMClassifierSparse"),
                                    self->ob_type,
                                    WrapOrange(svm->classVar),
                                    WrapOrange(svm->examples),
                                    WrapOrange(svm->supportVectors),
                                    buf.c_str(),
									(char)svm->useNonMeta,
                                    WrapOrange(svm->kernelFunc),
                                    packOrangeDictionary(self));
    else
        return Py_BuildValue("O(OOOOsb)N", getExportedFunction("__pickleLoaderSVMClassifierSparse"),
                                    self->ob_type,
                                    WrapOrange(svm->classVar),
                                    WrapOrange(svm->examples),
                                    WrapOrange(svm->supportVectors),
                                    buf.c_str(),
									(char)svm->useNonMeta,
                                    packOrangeDictionary(self));
  PyCATCH
}

PyObject *__pickleLoaderSVMClassifierSparse(PyObject *, PyObject *args) PYARGS(METH_VARARGS, "(type, packed_data)")
{
  PyTRY
    PyTypeObject* type;
    PVariable var;
    PExampleTable examples;
    PExampleTable supportVectors;
    PKernelFunc kernel;
    char *pbuf;
	char useNonMeta;
    if (!PyArg_ParseTuple(args, "OO&O&O&sb|O&:__pickleLoaderSVMClassifierSparse", &type, cc_Variable, &var,
        cc_ExampleTable, &examples, cc_ExampleTable, &supportVectors, &pbuf, &useNonMeta, cc_KernelFunc, &kernel))
        return NULL;
    //TCharBuffer buf(pbuf);
    string buf(pbuf);
    printf("loading model\n");
    svm_model *model=svm_load_model_alt(buf);

    if (!model)
        raiseError("Error building LibSVM model");
    model->param.learner=NULL;
    PSVMClassifier svm=mlnew TSVMClassifierSparse(var, examples, model, NULL, useNonMeta);
    svm->kernelFunc=kernel;
    svm->supportVectors=supportVectors;
    return WrapOrange(svm);
  PyCATCH
}
  

PyObject *SVMClassifier_getDecisionValues(PyObject *self, PyObject* args, PyObject *keywords) PYARGS(METH_VARARGS, "(Example) -> list of floats")
{PyTRY
	PExample example;
	if (!PyArg_ParseTuple(args, "O&", cc_Example, &example))
		return NULL;
	PFloatList f=SELF_AS(TSVMClassifier).getDecisionValues(example.getReference());
	return WrapOrange(f);
PyCATCH
}


/************* BAYES ************/

#include "bayes.hpp"
C_CALL(BayesLearner, Learner, "([examples], [weight=, estimate=] -/-> Classifier")
C_NAMED(BayesClassifier, ClassifierFD, "([probabilities=])")

PyObject *BayesClassifier_p(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(class, example) -> float")
{ PyTRY
    CAST_TO(TBayesClassifier, me);

    PyObject *pyvalue;
    TValue value;
    TExample *ex;
    if (   !PyArg_ParseTuple(args, "OO&:BayesClassifier.p", &pyvalue, ptr_Example, &ex)
        || !convertFromPython(pyvalue, value, me->domain->classVar))
      return PYNULL;
      
    return PyFloat_FromDouble((double)SELF_AS(TBayesClassifier).p(value, *ex));

  PyCATCH
}


/************* LINEAR REGRESSION ************/

#include "linreg.hpp"
C_CALL(LinRegLearner, Learner, "([examples] -/-> Classifier)")
C_NAMED(LinRegClassifier, ClassifierFD, "([coefficients=, coefficients_se=, SSres=, SStot=])")


/************* LWR ************/

#include "lwr.hpp"
C_CALL(LWRLearner, Learner, "([examples] -/-> Classifier)")
C_NAMED(LWRClassifier, ClassifierFD, "([findNearestConstructor=, linRegLearner=, k=, rankWeight=])")


/************* RULES ************/

#include "rulelearner.hpp"

C_NAMED(Rule, Orange, "()")

C_NAMED(RuleValidator_LRS, RuleValidator, "([alpha=0.05,min_coverage=0,max_rule_complexity=0,min_quality=numeric_limits<float>::min()])")

C_NAMED(RuleEvaluator_Entropy, RuleEvaluator, "()")
C_NAMED(RuleEvaluator_Laplace, RuleEvaluator, "()")
C_NAMED(RuleEvaluator_LRS, RuleEvaluator, "()")
C_NAMED(RuleEvaluator_mEVC, RuleEvaluator, "()")

C_NAMED(EVCDist, Orange, "()")
C_NAMED(ChiFunction_2LOGLR, ChiFunction, "()")
C_NAMED(EVCDistGetter_Standard, EVCDistGetter, "()")

C_NAMED(RuleBeamFinder, RuleFinder, "([validator=, evaluator=, initializer=, refiner=, candidateSelector=, ruleFilter=])")

C_NAMED(RuleBeamInitializer_Default, RuleBeamInitializer, "()")

C_NAMED(RuleBeamRefiner_Selector, RuleBeamRefiner, "([discretization=])")

C_NAMED(RuleBeamCandidateSelector_TakeAll, RuleBeamCandidateSelector, "()")

C_NAMED(RuleBeamFilter_Width, RuleBeamFilter, "([width=5])")

C_NAMED(RuleDataStoppingCriteria_NoPositives, RuleDataStoppingCriteria, "()")

C_NAMED(RuleCovererAndRemover_Default, RuleCovererAndRemover, "()")

C_NAMED(RuleStoppingCriteria_NegativeDistribution, RuleStoppingCriteria, "()")
C_CALL(RuleLearner, Learner, "([examples[, weightID]]) -/-> Classifier")

ABSTRACT(RuleClassifier, Classifier)
C_NAMED(RuleClassifier_firstRule, RuleClassifier, "([rules,examples[,weightID]])")
C_NAMED(RuleClassifier_logit, RuleClassifier, "([rules,examples[,weightID]])")
C_NAMED(RuleClassifier_logit_bestRule, RuleClassifier_logit, "([rules,examples[,weightID]])")

PyObject *Rule_call(PyObject *self, PyObject *args, PyObject *keywords)
{
  PyTRY
    NO_KEYWORDS

    if (PyTuple_Size(args)==1) {
      PyObject *pyex = PyTuple_GET_ITEM(args, 0);
      if (PyOrExample_Check(pyex))
        return PyInt_FromLong(PyOrange_AsRule(self)->call(PyExample_AS_ExampleReference(pyex)) ? 1 : 0);
    }

    PExampleGenerator egen;
    int references = 1;
    int negate = 0;
    if (!PyArg_ParseTuple(args, "O&|ii:Rule.__call__", &pt_ExampleGenerator, &egen, &references, &negate))
      return PYNULL;

    CAST_TO(TRule, rule)
    PExampleTable res = (*rule)(egen,(references?true:false),(negate?true:false));
    return WrapOrange(res);
  PyCATCH
}

PyObject *Rule_filterAndStore(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(examples, weightID, targetClass)")
{
  PyTRY
    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    
    if (!PyArg_ParseTuple(args, "O&O&i:RuleEvaluator.call",  pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass))
      return PYNULL;

    CAST_TO(TRule, rule);
    rule->filterAndStore(gen,weightID,targetClass);
    RETURN_NONE;
 PyCATCH
}

PyObject *RuleEvaluator_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleEvaluator_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleEvaluator_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleEvaluator_Python(), type);
}

PyObject *RuleEvaluator__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleEvaluator_Type);
}


PyObject *RuleEvaluator_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, table, weightID, targetClass, apriori) -/-> (quality)")
{
  PyTRY
    NO_KEYWORDS

    PRule rule;
    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    PDistribution apriori;

    if (!PyArg_ParseTuple(args, "O&O&O&iO&:RuleEvaluator.call", cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass, cc_Distribution, &apriori))
      return PYNULL;
    CAST_TO(TRuleEvaluator, evaluator)
    float quality;
     
    quality = (*evaluator)(rule, gen, weightID, targetClass, apriori);
    return PyFloat_FromDouble(quality);
  PyCATCH
}

PyObject *EVCDistGetter_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrEVCDistGetter_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TEVCDistGetter_Python(), type), args);
  else
    return WrapNewOrange(mlnew TEVCDistGetter_Python(), type);
}

PyObject *EVCDistGetter__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrEVCDistGetter_Type);
}


PyObject *EVCDistGetter_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, length) -/-> (EVCdist)")
{
  PyTRY
    NO_KEYWORDS

    PRule rule;
    int parentLength, rLength;

    if (!PyArg_ParseTuple(args, "O&ii:EVCDistGetter.call", cc_Rule, &rule, &parentLength, &rLength))
      return PYNULL;
    CAST_TO(TEVCDistGetter, getter)
    PEVCDist dist = (*getter)(rule, parentLength, rLength);

    return WrapOrange(dist);
  PyCATCH
}

PyObject *ChiFunction_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrChiFunction_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TChiFunction_Python(), type), args);
  else
    return WrapNewOrange(mlnew TChiFunction_Python(), type);
}

PyObject *ChiFunction__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrChiFunction_Type);
}

PyObject *ChiFunction_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, data, weight, targetClass, apriori) -/-> (nonOptimistic_Chi, optimistic_Chi)")
{
  PyTRY
    NO_KEYWORDS

    PRule rule;
    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    PDistribution apriori;

    if (!PyArg_ParseTuple(args, "O&O&O&iO&:ChiFunction.call", cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass, cc_Distribution, &apriori))
      return PYNULL;
    CAST_TO(TChiFunction, chif);
    float nonOptimistic_Chi = 0.0;
    float chi = (*chif)(rule, gen, weightID, targetClass, apriori, nonOptimistic_Chi);

    return Py_BuildValue("ii", nonOptimistic_Chi, chi);
  PyCATCH
}


PyObject *RuleValidator_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleValidator_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleValidator_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleValidator_Python(), type);
}

PyObject *RuleValidator__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleValidator_Type);
}


PyObject *RuleValidator_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, table, weightID, targetClass, apriori) -/-> (quality)")
{
  
  PyTRY
    NO_KEYWORDS

    PRule rule;
    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    PDistribution apriori;

    if (!PyArg_ParseTuple(args, "O&O&O&iO&:RuleValidator.call", cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass, cc_Distribution, &apriori))
      return PYNULL;
    CAST_TO(TRuleValidator, validator)

    bool valid;
    valid = (*validator)(rule, gen, weightID, targetClass, apriori);
    return PyInt_FromLong(valid?1:0);
  PyCATCH
}

PyObject *RuleCovererAndRemover_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleCovererAndRemover_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleCovererAndRemover_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleCovererAndRemover_Python(), type);
}

PyObject *RuleCovererAndRemover__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleCovererAndRemover_Type);
}


PyObject *RuleCovererAndRemover_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, table, weightID, targetClass) -/-> (table,newWeight)")
{
  PyTRY
    NO_KEYWORDS

    PRule rule;
    PExampleGenerator gen;
    int weightID = 0;
    int newWeightID = 0;
    int targetClass = -1;

    if (!PyArg_ParseTuple(args, "O&O&O&i:RuleCovererAndRemover.call", cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID,&targetClass))
      return PYNULL;
    CAST_TO(TRuleCovererAndRemover, covererAndRemover)

    PExampleTable res = (*covererAndRemover)(rule, gen, weightID, newWeightID, targetClass);
    return Py_BuildValue("Ni", WrapOrange(res),newWeightID);
  PyCATCH
}

PyObject *RuleStoppingCriteria_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleStoppingCriteria_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleStoppingCriteria_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleStoppingCriteria_Python(), type);
}

PyObject *RuleStoppingCriteria__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleStoppingCriteria_Type);
}


PyObject *RuleStoppingCriteria_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rulelist, rule, table, weightID) -/-> (table)")
{
  PyTRY
    NO_KEYWORDS

    PRuleList ruleList;
    PRule rule;
    PExampleGenerator gen;
    int weightID = 0;

    if (!PyArg_ParseTuple(args, "O&O&O&O&:RuleStoppingCriteria.call", cc_RuleList, &ruleList, cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID))
      return PYNULL;
    CAST_TO(TRuleStoppingCriteria, ruleStopping)

    bool stop = (*ruleStopping)(ruleList, rule, gen, weightID);
    return PyInt_FromLong(stop?1:0);
  PyCATCH
}

PyObject *RuleDataStoppingCriteria_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleDataStoppingCriteria_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleDataStoppingCriteria_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleDataStoppingCriteria_Python(), type);
}

PyObject *RuleDataStoppingCriteria__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleDataStoppingCriteria_Type);
}


PyObject *RuleDataStoppingCriteria_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(table, weightID, targetClass) -/-> (table)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;

    if (!PyArg_ParseTuple(args, "O&O&i:RuleDataStoppingCriteria.call", pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass))
      return PYNULL;
    CAST_TO(TRuleDataStoppingCriteria, dataStopping)

    bool stop = (*dataStopping)(gen, weightID, targetClass);
    return PyInt_FromLong(stop?1:0);
  PyCATCH
}

PyObject *RuleFinder_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleFinder_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleFinder_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleFinder_Python(), type);
}

PyObject *RuleFinder__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleFinder_Type);
}


PyObject *RuleFinder_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(table, weightID, targetClass, baseRules) -/-> (rule)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    PRuleList baseRules;

    if (!PyArg_ParseTuple(args, "O&O&iO&:RuleFinder.call", pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass, ccn_RuleList, &baseRules))
      return PYNULL;
    CAST_TO(TRuleFinder, finder)

    PRule res = (*finder)(gen, weightID, targetClass, baseRules);
    return WrapOrange(res);
  PyCATCH 
}

PyObject *RuleBeamRefiner_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleBeamRefiner_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleBeamRefiner_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleBeamRefiner_Python(), type);
}

PyObject *RuleBeamRefiner__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleBeamRefiner_Type);
}


PyObject *RuleBeamRefiner_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rule, table, weightID, targetClass) -/-> (rules)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    int weightID = 0;
    int targetClass = -1;
    PRule rule;

    if (!PyArg_ParseTuple(args, "O&O&O&i:RuleBeamRefiner.call", cc_Rule, &rule, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass))
      return PYNULL;
    CAST_TO(TRuleBeamRefiner, refiner)

    PRuleList res = (*refiner)(rule, gen, weightID, targetClass);
    return WrapOrange(res);
  PyCATCH
}

PyObject *RuleBeamInitializer_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleBeamInitializer_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleBeamInitializer_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleBeamInitializer_Python(), type);
}

PyObject *RuleBeamInitializer__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleBeamInitializer_Type);
}


PyObject *RuleBeamInitializer_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(table, weightID, targetClass, baseRules, evaluator, prior) -/-> (rules, bestRule)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    PRuleList baseRules;
    PRuleEvaluator evaluator;
    PDistribution prior;
    PRule bestRule;
    int weightID = 0;
    int targetClass = -1;
    PRule rule;

    if (!PyArg_ParseTuple(args, "O&O&iO&O&O&:RuleBeamInitializer.call", pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, &targetClass, ccn_RuleList, &baseRules, cc_RuleEvaluator, &evaluator, cc_Distribution, &prior))
      return PYNULL;
    CAST_TO(TRuleBeamInitializer, initializer)

    PRuleList res = (*initializer)(gen, weightID, targetClass, baseRules, evaluator, prior, bestRule);
    return Py_BuildValue("NN", WrapOrange(res), WrapOrange(bestRule));
  PyCATCH
}

PyObject *RuleBeamCandidateSelector_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleBeamCandidateSelector_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleBeamCandidateSelector_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleBeamCandidateSelector_Python(), type);
}

PyObject *RuleBeamCandidateSelector__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleBeamCandidateSelector_Type);
}


PyObject *RuleBeamCandidateSelector_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(existingRules, table, weightID) -/-> (candidates, remainingRules)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    PRuleList existingRules;
    int weightID = 0;
    PRuleList candidates;

    if (!PyArg_ParseTuple(args, "O&O&O&:RuleBeamCandidateSelector.call", cc_RuleList, &existingRules, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID))
      return PYNULL;
    CAST_TO(TRuleBeamCandidateSelector, selector)

    PRuleList res = (*selector)(existingRules, gen, weightID);
    return Py_BuildValue("NN", WrapOrange(res), WrapOrange(existingRules));
  PyCATCH
}

PyObject *RuleBeamFilter_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleBeamFilter_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleBeamFilter_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleBeamFilter_Python(), type);
}

PyObject *RuleBeamFilter__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleBeamFilter_Type);
}


PyObject *RuleBeamFilter_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rules, table, weightID) -/-> (rules)")
{
  PyTRY
    NO_KEYWORDS

    PExampleGenerator gen;
    PRuleList rules;
    int weightID = 0;

    if (!PyArg_ParseTuple(args, "O&O&O&:RuleBeamFilter.call", cc_RuleList, &rules, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID))
      return PYNULL;
    CAST_TO(TRuleBeamFilter, filter)

    (*filter)(rules, gen, weightID);
    return WrapOrange(rules);
  PyCATCH
}

PyObject *RuleClassifierConstructor_new(PyTypeObject *type, PyObject *args, PyObject *keywords)  BASED_ON(Orange, "<abstract>")
{ if (type == (PyTypeObject *)&PyOrRuleClassifierConstructor_Type)
    return setCallbackFunction(WrapNewOrange(mlnew TRuleClassifierConstructor_Python(), type), args);
  else
    return WrapNewOrange(mlnew TRuleClassifierConstructor_Python(), type);
}


PyObject *RuleClassifierConstructor__reduce__(PyObject *self)
{
  return callbackReduce(self, PyOrRuleClassifierConstructor_Type);
}


PyObject *RuleClassifierConstructor_call(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rules, examples[, weight]) -> (RuleClassifier)")
{ 
  PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrRuleClassifierConstructor_Type) {
      PyErr_Format(PyExc_SystemError, "RuleClassifierConstructor.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PExampleGenerator gen;
    int weightID = 0;
    PRuleList rules;

    if (!PyArg_ParseTuple(args, "O&O&|O&:RuleClassifierConstructor.call", cc_RuleList, &rules, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID))
      return PYNULL;

    PRuleClassifier ruleClassifier;
    ruleClassifier = SELF_AS(TRuleClassifierConstructor)(rules, gen, weightID);
    return WrapOrange(ruleClassifier);
  PyCATCH
}

PyObject *RuleClassifier_logit_new(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rules, min_beta, examples[, weight])")
{ 
  PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrRuleClassifier_Type) {
      PyErr_Format(PyExc_SystemError, "RuleClassifier.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PExampleGenerator gen;
    int weightID = 0;
    float minBeta = 0.0;
    PRuleList rules;
    PDistributionList probList;
    PClassifier classifier;

    if (!PyArg_ParseTuple(args, "O&fO&|O&O&O&:RuleClassifier.call", cc_RuleList, &rules, &minBeta, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, cc_Classifier, &classifier, cc_DistributionList, &probList))
      return PYNULL;

    TRuleClassifier *rc = new TRuleClassifier_logit(rules, minBeta, gen, weightID, classifier, probList);
    PRuleClassifier ruleClassifier = rc;
//    ruleClassifier = new SELF_AS(TRuleClassifier)(rules, gen, weightID);
    return WrapOrange(ruleClassifier);
  PyCATCH
}

PyObject *RuleClassifier_logit_bestRule_new(PyObject *self, PyObject *args, PyObject *keywords) PYDOC("(rules, examples[, weight])")
{ 
  PyTRY
    NO_KEYWORDS

    if (PyOrange_OrangeBaseClass(self->ob_type) == &PyOrRuleClassifier_Type) {
      PyErr_Format(PyExc_SystemError, "RuleClassifier.call called for '%s': this may lead to stack overflow", self->ob_type->tp_name);
      return PYNULL;
    }

    PExampleGenerator gen;
    int weightID = 0;
    float minBeta = 0.0;
    PRuleList rules;
    PDistributionList probList;
    PClassifier classifier;

    if (!PyArg_ParseTuple(args, "O&fO&|O&O&O&:RuleClassifier.call", cc_RuleList, &rules, &minBeta, pt_ExampleGenerator, &gen, pt_weightByGen(gen), &weightID, cc_Classifier, &classifier, cc_DistributionList, &probList))
      return PYNULL;

    TRuleClassifier *rc = new TRuleClassifier_logit_bestRule(rules, minBeta, gen, weightID, classifier, probList);
    PRuleClassifier ruleClassifier = rc;
//    ruleClassifier = new SELF_AS(TRuleClassifier)(rules, gen, weightID);
    return WrapOrange(ruleClassifier);
  PyCATCH
}

PRuleList PRuleList_FromArguments(PyObject *arg) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::P_FromArguments(arg); }
PyObject *RuleList_FromArguments(PyTypeObject *type, PyObject *arg) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_FromArguments(type, arg); }
PyObject *RuleList_new(PyTypeObject *type, PyObject *arg, PyObject *kwds) BASED_ON(Orange, "(<list of Rule>)") ALLOWS_EMPTY { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_new(type, arg, kwds); }
PyObject *RuleList_getitem_sq(TPyOrange *self, int index) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_getitem(self, index); }
int       RuleList_setitem_sq(TPyOrange *self, int index, PyObject *item) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_setitem(self, index, item); }
PyObject *RuleList_getslice(TPyOrange *self, int start, int stop) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_getslice(self, start, stop); }
int       RuleList_setslice(TPyOrange *self, int start, int stop, PyObject *item) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_setslice(self, start, stop, item); }
int       RuleList_len_sq(TPyOrange *self) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_len(self); }
PyObject *RuleList_richcmp(TPyOrange *self, PyObject *object, int op) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_richcmp(self, object, op); }
PyObject *RuleList_concat(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_concat(self, obj); }
PyObject *RuleList_repeat(TPyOrange *self, int times) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_repeat(self, times); }
PyObject *RuleList_str(TPyOrange *self) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_str(self); }
PyObject *RuleList_repr(TPyOrange *self) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_str(self); }
int       RuleList_contains(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_contains(self, obj); }
PyObject *RuleList_append(TPyOrange *self, PyObject *item) PYARGS(METH_O, "(Rule) -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_append(self, item); }
PyObject *RuleList_extend(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(sequence) -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_extend(self, obj); }
PyObject *RuleList_count(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(Rule) -> int") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_count(self, obj); }
PyObject *RuleList_filter(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([filter-function]) -> RuleList") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_filter(self, args); }
PyObject *RuleList_index(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(Rule) -> int") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_index(self, obj); }
PyObject *RuleList_insert(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "(index, item) -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_insert(self, args); }
PyObject *RuleList_native(TPyOrange *self) PYARGS(METH_NOARGS, "() -> list") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_native(self); }
PyObject *RuleList_pop(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "() -> Rule") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_pop(self, args); }
PyObject *RuleList_remove(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(Rule) -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_remove(self, obj); }
PyObject *RuleList_reverse(TPyOrange *self) PYARGS(METH_NOARGS, "() -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_reverse(self); }
PyObject *RuleList_sort(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([cmp-func]) -> None") { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_sort(self, args); }
PyObject *RuleList__reduce__(TPyOrange *self, PyObject *) { return ListOfWrappedMethods<PRuleList, TRuleList, PRule, &PyOrRule_Type>::_reduce(self); }

PEVCDistList PEVCDistList_FromArguments(PyObject *arg) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::P_FromArguments(arg); }
PyObject *EVCDistList_FromArguments(PyTypeObject *type, PyObject *arg) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_FromArguments(type, arg); }
PyObject *EVCDistList_new(PyTypeObject *type, PyObject *arg, PyObject *kwds) BASED_ON(Orange, "(<list of EVCDist>)") ALLOWS_EMPTY { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_new(type, arg, kwds); }
PyObject *EVCDistList_getitem_sq(TPyOrange *self, int index) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_getitem(self, index); }
int       EVCDistList_setitem_sq(TPyOrange *self, int index, PyObject *item) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_setitem(self, index, item); }
PyObject *EVCDistList_getslice(TPyOrange *self, int start, int stop) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_getslice(self, start, stop); }
int       EVCDistList_setslice(TPyOrange *self, int start, int stop, PyObject *item) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_setslice(self, start, stop, item); }
int       EVCDistList_len_sq(TPyOrange *self) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_len(self); }
PyObject *EVCDistList_richcmp(TPyOrange *self, PyObject *object, int op) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_richcmp(self, object, op); }
PyObject *EVCDistList_concat(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_concat(self, obj); }
PyObject *EVCDistList_repeat(TPyOrange *self, int times) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_repeat(self, times); }
PyObject *EVCDistList_str(TPyOrange *self) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_str(self); }
PyObject *EVCDistList_repr(TPyOrange *self) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_str(self); }
int       EVCDistList_contains(TPyOrange *self, PyObject *obj) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_contains(self, obj); }
PyObject *EVCDistList_append(TPyOrange *self, PyObject *item) PYARGS(METH_O, "(EVCDist) -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_append(self, item); }
PyObject *EVCDistList_extend(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(sequence) -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_extend(self, obj); }
PyObject *EVCDistList_count(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(EVCDist) -> int") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_count(self, obj); }
PyObject *EVCDistList_filter(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([filter-function]) -> EVCDistList") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_filter(self, args); }
PyObject *EVCDistList_index(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(EVCDist) -> int") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_index(self, obj); }
PyObject *EVCDistList_insert(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "(index, item) -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_insert(self, args); }
PyObject *EVCDistList_native(TPyOrange *self) PYARGS(METH_NOARGS, "() -> list") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_native(self); }
PyObject *EVCDistList_pop(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "() -> EVCDist") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_pop(self, args); }
PyObject *EVCDistList_remove(TPyOrange *self, PyObject *obj) PYARGS(METH_O, "(EVCDist) -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_remove(self, obj); }
PyObject *EVCDistList_reverse(TPyOrange *self) PYARGS(METH_NOARGS, "() -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_reverse(self); }
PyObject *EVCDistList_sort(TPyOrange *self, PyObject *args) PYARGS(METH_VARARGS, "([cmp-func]) -> None") { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_sort(self, args); }
PyObject *EVCDistList__reduce__(TPyOrange *self, PyObject *) { return ListOfWrappedMethods<PEVCDistList, TEVCDistList, PEVCDist, &PyOrEVCDist_Type>::_reduce(self); }

#include "lib_learner.px"

