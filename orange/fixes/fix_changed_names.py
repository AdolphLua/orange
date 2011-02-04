""" This fixer changes all occurrences of the form 'module.member' from the
global dictionary MAPPING's keys and replaces them with the corresponding
value. It adds the proper imports to make it available in the script

For example this code::
    import orange
    import orngSVM
    data = orange.ExampleTable("iris")
    learner = orngSVM.SVMLearner(name='svm')
    
will be replaced with::
    import Orange.data
    import Orange.classification.svm
    data =Orange.data.Table('iris')
    learner =Orange.classification.svm.SVMLearner(name='svm')
    
Try to add as much name mappings as possible (This fixer is prefered 
(and will run before) the fix_orange_imports  
    
"""
from lib2to3 import fixer_base
from lib2to3 import fixer_util
from lib2to3 import pytree
from lib2to3.fixer_util import Name, Dot, Node, attr_chain, touch_import

# keys must be in the form of 'orange.name' not name or orange.bla.name 
MAPPING = {"orange.ExampleTable": "Orange.data.Table",
           "orange.Example": "Orange.data.Instance",
           "orange.Domain": "Orange.data.Domain",
           "orange.Value": "Orange.data.Value",
           "orange.VarTypes": "Orange.data.Type",
           "orange.Variable": "Orange.data.feature.Feature",
           "orange.EnumVariable": "Orange.data.feature.Discrete",
           "orange.FloatVariable": "Orange.data.feature.Continuous",
           "orange.StringVariable": "Orange.data.feature.String",
           "orange.PythonVariable": "Orange.data.feature.Python",
           "orange.VarList": "Orange.data.feature.Features",
          
           "orange.MeasureAttribute": "Orange.feature.scoring.Measure", 
           "orange.BasicAttrStat": "Orange.statistics.distributions.BasicStatistics",
           "orange.DomainBasicAttrStat": "Orange.statistics.distributions.DomainBasicStatistics",
           "orange.ContingencyAttrAttr": "Orange.statistics.distributions.ContingencyVarVar",
           "orange.ContingencyClass": "Orange.statistics.distributions.ContingencyClass",
           "orange.ContingencyAttrClass": "Orange.statistics.distributions.ContingencyVarClass",
           "orange.ContingencyClassAttr": "Orange.statistics.distributions.ContingencyClassVar",
           
           "orange.MeasureAttribute_gainRatio": "Orange.feature.scoring.GainRatio",
           "orange.MeasureAttribute_relief": "Orange.feature.scoring.Relief",
           "orange.MeasureAttribute_info": "Orange.feature.scoring.InfoGain",
           "orange.MeasureAttribute_gini": "Orange.feature.scoring.Gini",

           "orange.MeasureAttribute_relevance": "Orange.feature.scoring.Relevance",
           "orange.MeasureAttribute_cost": "Orange.feature.scoring.Cost",
           "orange.MeasureAttribute_MSE": "Orange.feature.scoring.MSE",

           "orngFSS.attMeasure": "Orange.feature.scoring.attMeasure",
           "orngFSS.bestNAtts": "Orange.feature.scoring.bestNAtts",
           "orngFSS.attsAbovethreshold": "Orange.feature.selection.attsAbovethreshold",
           "orngFSS.selectBestNAtts": "Orange.feature.selection.selectBestNAtts",
           "orngFSS.selectAttsAboveThresh": "Orange.feature.selection.selectAttsAboveThresh",
           "orngFSS.filterRelieff": "Orange.feature.selection.filterRelieff",
           "orngFSS.FilterAttsAboveThresh": "Orange.feature.selection.FilterAttsAboveThresh",
           "orngFSS.FilterAttsAboveThresh_Class": "Orange.feature.selection.FilterAttsAboveThresh_Class",
           "orngFSS.FilterBestNAtts": "Orange.feature.selection.FilterBestNAtts",
           "orngFSS.FilterBestNAtts_Class": "Orange.feature.selection.FilterBestNAtts_Class",
           "orngFSS.FilterRelief": "Orange.feature.selection.FilterRelief",
           "orngFSS.FilterRelief_Class": "Orange.feature.selection.FilterRelief_Class",
           "orngFSS.FilteredLearner": "Orange.feature.selection.FilteredLearner",
           "orngFSS.FilteredLearner_Class": "Orange.feature.selection.FilteredLearner_Class",
           "orngFSS.FilteredClassifier": "Orange.feature.selection.FilteredClassifier",
           "orngFSS.StepwiseLearner_Class": "Orange.classification.wrappers.StepwiseLearner_Class",
           "orngFSS.StepwiseLearner": "Orange.classification.wrappers.StepwiseLearner",
 
           "orange.ExamplesDistance_Hamming": "Orange.distances.ExamplesDistance_Hamming",
           "orange.ExamplesDistance_Normalized": "Orange.distances.ExamplesDistance_Normalized",
           "orange.ExamplesDistance_DTW": "Orange.distances.ExamplesDistance_DTW", 
           "orange.ExamplesDistance_Euclidean": "Orange.distances.ExamplesDistance_Euclidean", 
           "orange.ExamplesDistance_Manhattan": "Orange.distances.ExamplesDistance_Manhattan", 
           "orange.ExamplesDistance_Maximal": "Orange.distances.ExamplesDistance_Maximal", 
           "orange.ExamplesDistance_Relief": "Orange.distances.ExamplesDistance_Relief", 
           "orange.ExamplesDistanceConstructor": "Orange.distances.ExamplesDistanceConstructor",
           "orange.ExamplesDistanceConstructor_DTW": "Orange.distances.ExamplesDistanceConstructor_DTW", 
           "orange.ExamplesDistanceConstructor_Euclidean": "Orange.distances.ExamplesDistanceConstructor_Euclidean", 
           "orange.ExamplesDistanceConstructor_Hamming": "Orange.distances.ExamplesDistanceConstructor_Hamming",
           "orange.ExamplesDistanceConstructor_Manhattan": "Orange.distances.ExamplesDistanceConstructor_Manhattan",
           "orange.ExamplesDistanceConstructor_Maximal": "Orange.distances.ExamplesDistanceConstructor_Maximal",
           "orange.ExamplesDistanceConstructor_Relief": "Orange.distances.ExamplesDistanceConstructor_Relief",
           
           "orngSVM.RBFKernelWrapper": "Orange.classification.svm.kernels.RBFKernelWrapper",
           "orngSVM.CompositeKernelWrapper": "Orange.classification.svm.kernels.CompositeKernelWrapper",
           "orngSVM.KernelWrapper": "Orange.classification.svm.kernels.KernelWrapper",
           "orngSVM.DualKernelWrapper": "Orange.classification.svm.kernels.DualKernelWrapper",
           "orngSVM.PolyKernelWrapper": "Orange.classification.svm.kernels.PolyKernelWrapper",
           "orngSVM.AdditionKernelWrapper": "Orange.classification.svm.kernels.AdditionKernelWrapper",
           "orngSVM.MultiplicationKernelWrapper": "Orange.classification.svm.kernels.MultiplicationKernelWrapper",
           "orngSVM.SparseLinKernel": "Orange.classification.svm.kernels.SparseLinKernel",
           "orngSVM.BagOfWords": "Orange.classification.svm.kernels.BagOfWords",
           
           "orange.kNNLearner":"Orange.classification.knn.kNNLearner",
           "orange.kNNClassifier":"Orange.classification.knn.kNNClassifier",
           "orange.FindNearest_BruteForce":"Orange.classification.knn.FindNearest",
           "orange.FindNearestConstructor_BruteForce":"Orange.classification.knn.FindNearestConstructor",
           "orange.P2NN":"Orange.classification.knn.P2NN",
           
           "orange.BayesLearner":"Orange.classification.bayes.NaiveLearner",
           "orange.BayesClassifier":"Orange.classification.bayes.NaiveClassifier",
           "orngBayes.BayesLearner":"Orange.classification.bayes.NaiveLearner",
           "orngBayes.BayesClassifier":"Orange.classification.bayes.NaiveClassifier",
           
           "orngNetwork.MdsTypeClass":"Orange.network.MdsTypeClass",
           "orngNetwork.Network":"Orange.network.Network",
           "orngNetwork.NetworkOptimization":"Orange.network.NetworkOptimization",
           "orngNetwork.NetworkClustering":"Orange.network.NetworkClustering",
           "orange.Graph":"Orange.network.Graph",
           "orange.GraphAsList":"Orange.network.GraphAsList",
           "orange.GraphAsMatrix":"Orange.network.GraphAsMatrix",
           "orange.GraphAsTree":"Orange.network.GraphAsTree",
           
           "orngEnsemble.MeasureAttribute_randomForests":"Orange.ensemble.forest.ScoreFeature",
           
            "orange.TreeLearner": "Orange.classification.tree.TreeLearnerBase",
           "orange.TreeClassifier": "Orange.classification.tree.TreeClassifier",
           "orange.C45Learner": "Orange.classification.tree.C45Learner",
           "orange.C45Classifier": "Orange.classification.tree.C45Classifier",
           "orange.C45TreeNode": "Orange.classification.tree.C45Node",
           "orange.C45TreeNodeList": "C45NodeList",
           "orange.TreeDescender": "Orange.classification.tree.Descender",
           "orange.TreeDescender_UnknownMergeAsBranchSizes": "Orange.classification.tree.Descender_UnknownMergeAsBranchSizes",
           "orange.TreeDescender_UnknownMergeAsSelector": "Orange.classification.tree.Descender_UnknownMergeAsSelector",
           "orange.TreeDescender_UnknownToBranch": "Orange.classification.tree.Descender_UnknownToBranch",
           "orange.TreeDescender_UnknownToCommonBranch": "Orange.classification.tree.Descender_UnknownToCommonBranch",
           "orange.TreeDescender_UnknownToCommonSelector":"Orange.classification.tree.Descender_UnknownToCommonSelector",
           "orange.TreeExampleSplitter":"Orange.classification.tree.Splitter",
           "orange.TreeExampleSplitter_IgnoreUnknowns":"Orange.classification.tree.Splitter_IgnoreUnknowns",
           "orange.TreeExampleSplitter_UnknownsAsBranchSizes":"Orange.classification.tree.Splitter_UnknownsAsBranchSizes",
           "orange.TreeExampleSplitter_UnknownsAsSelecto":"Orange.classification.tree.Splitter_UnknownsAsSelector",
           "orange.TreeExampleSplitter_UnknownsToAll":"Orange.classification.tree.Splitter_UnknownsToAll",
           "orange.TreeExampleSplitter_UnknownsToBranch":"Orange.classification.tree.Splitter_UnknownsToBranch",
           "orange.TreeExampleSplitter_UnknownsToCommon":"Orange.classification.tree.Splitter_UnknownsToCommon",
           "orange.TreeExampleSplitter_UnknownsToRandom":"Orange.classification.tree.Splitter_UnknownsToRandom",
           "orange.TreeNode":"Orange.classification.tree.Node",
           "orange.TreeNodeList":"Orange.classification.tree.NodeList",
           "orange.TreePruner":"Orange.classification.tree.Pruner",
           "orange.TreePruner_SameMajority":"Orange.classification.tree.Pruner_SameMajority",
           "orange.TreePruner_m":"Orange.classification.tree.Pruner_m",
           "orange.TreeSplitConstructor":"Orange.classification.tree.SplitConstructor",
           "orange.TreeSplitConstructor_Combined":"Orange.classification.tree.SplitConstructor_Combined",
           "orange.TreeSplitConstructor_Measure":"Orange.classification.tree.SplitConstructor_Measure",
           "orange.TreeSplitConstructor_Attribute":"Orange.classification.tree.SplitConstructor_Feature",
           "orange.TreeSplitConstructor_ExhaustiveBinary":"Orange.classification.tree.SplitConstructor_ExhaustiveBinary",
           "orange.TreeSplitConstructor_OneAgainstOthers":"Orange.classification.tree.SplitConstructor_OneAgainstOthers",
           "orange.TreeSplitConstructor_Threshold":"Orange.classification.tree.SplitConstructor_Threshold",
           "orange.TreeStopCriteria":"Orange.classification.tree.StopCriteria",
           "orange.TreeStopCriteria_Python":"Orange.classification.tree.StopCriteria_Python",
           "orange.TreeStopCriteria_common":"Orange.classification.tree.StopCriteria_common",
           
           "orange.MajorityLearner":"Orange.classification.majority.MajorityLearner",
           "orange.DefaultClassifier":"Orange.classification.ConstantClassifier",
           
           "orange.LookupLearner":"Orange.classification.lookup.LookupLearner",
           "orange.ClassifierByLookupTable":"Orange.classification.lookup.ClassifierByLookupTable",
           "orange.ClassifierByLookupTable1":"Orange.classification.lookup.ClassifierByLookupTable1",
           "orange.ClassifierByLookupTable2":"Orange.classification.lookup.ClassifierByLookupTable2",
           "orange.ClassifierByLookupTable3":"Orange.classification.lookup.ClassifierByLookupTable3",
           "orange.ClassifierByExampleTable":"Orange.classification.lookup.ClassifierByDataTable",
           
           "orngLookup.lookupFromBound":"Orange.classification.lookup.lookupFromBound",
           "orngLookup.lookupFromExamples":"Orange.classification.lookup.lookupFromData",
           "orngLookup.lookupFromFunction":"Orange.classification.lookup.lookupFromFunction",
           "orngLookup.printLookupFunction":"Orange.classification.lookup.printLookupFunction",
           
           "orange.AssociationRule" : "Orange.associate.AssociationRule",
           "orange.AssociationRules" : "Orange.associate.AssociationRules",
           "orange.AssociationRulesInducer" : "Orange.associate.AssociationRulesInducer",
           "orange.AssociationRulesSparseInducer" : "Orange.associate.AssociationRulesSparseInducer",
           "orange.ItemsetNodeProxy" : "Orange.associate.ItemsetNodeProxy",
           "orange.ItemsetsSparseInducer" : "Orange.associate.ItemsetsSparseInducer",

           "orngCN2.ruleToString": "Orange.classification.rules.ruleToString",
           "orngCN2.LaplaceEvaluator": "Orange.classification.rules.LaplaceEvaluator",
           "orngCN2.WRACCEvaluator": "Orange.classification.rules.WRACCEvaluator",
           "orngCN2.mEstimate": "Orange.classification.rules.MEstimateEvaluator",
           "orngCN2.RuleStopping_apriori": "Orange.classification.rules.RuleStopping_Apriori",
           "orngCN2.LengthValidator": "Orange.classification.rules.LengthValidator",
           "orngCN2.supervisedClassCheck": "Orange.classification.rules.supervisedClassCheck",
           "orngCN2.CN2Learner": "Orange.classification.rules.CN2Learner",
           "orngCN2.CN2Classifier": "Orange.classification.rules.CN2Classifier",
           "orngCN2.CN2UnorderedLearner": "Orange.classification.rules.CN2UnorderedLearner",
           "orngCN2.CN2UnorderedClassifier": "Orange.classification.rules.CN2UnorderedClassifier",
           "orngCN2.RuleClassifier_bestRule": "Orange.classification.rules.RuleClassifier_BestRule",
           "orngCN2.CovererAndRemover_multWeights": "Orange.classification.rules.CovererAndRemover_MultWeights",
           "orngCN2.CovererAndRemover_addWeights": "Orange.classification.rules.CovererAndRemover_AddWeights",
           "orngCN2.rule_in_set": "Orange.classification.rules.rule_in_set",
           "orngCN2.rules_equal": "Orange.classification.rules.rules_equal",
           "orngCN2.noDuplicates_validator": "Orange.classification.rules.NoDuplicatesValidator",
           "orngCN2.ruleSt_setRules": "Orange.classification.rules.RuleStopping_SetRules",
           "orngCN2.CN2SDUnorderedLearner": "Orange.classification.rules.CN2SDUnorderedLearner",
           "orngCN2.avg": "Orange.classification.rules.avg",
           "orngCN2.var": "Orange.classification.rules.var",
           "orngCN2.median": "Orange.classification.rules.median",
           "orngCN2.perc": "Orange.classification.rules.perc",
           "orngCN2.createRandomDataSet": "Orange.classification.rules.createRandomDataSet",
           "orngCN2.compParameters": "Orange.classification.rules.compParameters",
           "orngCN2.computeDists": "Orange.classification.rules.computeDists",
           "orngCN2.createEVDistList": "Orange.classification.rules.createEVDistList",
           "orngCN2.CovererAndRemover_Prob": "Orange.classification.rules.CovererAndRemover_Prob",
           "orngCN2.add_sub_rules": "Orange.classification.rules.add_sub_rules",
           "orngCN2.CN2EVCUnorderedLearner": "Orange.classification.rules.CN2EVCUnorderedLearner",
           
           "orngMDS.KruskalStress": "Orange.projection.mds.KruskalStress",
           "orngMDS.SammonStress": "Orange.projection.mds.SammonStress",
           "orngMDS.SgnSammonStress": "Orange.projection.mds.SgnSammonStress",
           "orngMDS.SgnRelStress": "Orange.projection.mds.SgnRelStress",
           "orngMDS.PointList": "Orange.projection.mds.PointList",
           "orngMDS.FloatListList": "Orange.projection.mds.FloatListList",
           "orngMDS.PivotMDS": "Orange.projection.mds.PivotMDS",
           "orngMDS.MDS": "Orange.projection.mds.MDS",
           
           "orngStat.AP" : "Orange.evaluation.scoring.AP",
           "orngStat.AROC" : "Orange.evaluation.scoring.AROC",
           "orngStat.AROCFromCDT" : "Orange.evaluation.scoring.AROCFromCDT",
           "orngStat.AUC" : "Orange.evaluation.scoring.AUC",
           "orngStat.AUCWilcoxon" : "Orange.evaluation.scoring.AUCWilcoxon",
           "orngStat.AUC_binary" : "Orange.evaluation.scoring.AUC_binary",
           "orngStat.AUC_i" : "Orange.evaluation.scoring.AUC_i",
           "orngStat.AUC_ij" : "Orange.evaluation.scoring.AUC_ij",
           "orngStat.AUC_iterations" : "Orange.evaluation.scoring.AUC_iterations",
           "orngStat.AUC_matrix" : "Orange.evaluation.scoring.AUC_matrix",
           "orngStat.AUC_multi" : "Orange.evaluation.scoring.AUC_multi",
           "orngStat.AUC_pair" : "Orange.evaluation.scoring.AUC_pair",
           "orngStat.AUC_single" : "Orange.evaluation.scoring.AUC_single",
           "orngStat.AUC_x" : "Orange.evaluation.scoring.AUC_x",
           "orngStat.BSS" : "Orange.evaluation.scoring.BSS",
           "orngStat.BrierScore" : "Orange.evaluation.scoring.BrierScore",
           "orngStat.CA" : "Orange.evaluation.scoring.CA",
           "orngStat.CA_se" : "Orange.evaluation.scoring.CA_se",
           "orngStat.CDT" : "Orange.evaluation.scoring.CDT",
           "orngStat.ConfusionMatrix" : "Orange.evaluation.scoring.ConfusionMatrix",
           "orngStat.F1" : "Orange.evaluation.scoring.F1",
           "orngStat.Falpha" : "Orange.evaluation.scoring.Falpha",
           "orngStat.Friedman" : "Orange.evaluation.scoring.Friedman",
           "orngStat.IS" : "Orange.evaluation.scoring.IS",
           "orngStat.IS_ex" : "Orange.evaluation.scoring.IS_ex",
           "orngStat.MAE" : "Orange.evaluation.scoring.MAE",
           "orngStat.MCC" : "Orange.evaluation.scoring.MCC",
           "orngStat.ME" : "Orange.evaluation.scoring.ME",
           "orngStat.MSE" : "Orange.evaluation.scoring.MSE",
           "orngStat.MSE_old" : "Orange.evaluation.scoring.MSE_old",
           "orngStat.McNemar" : "Orange.evaluation.scoring.McNemar",
           "orngStat.McNemarOfTwo" : "Orange.evaluation.scoring.McNemarOfTwo",
           "orngStat.NPV" : "Orange.evaluation.scoring.NPV",
           "orngStat.PPV" : "Orange.evaluation.scoring.PPV",
           "orngStat.R2" : "Orange.evaluation.scoring.R2",
           "orngStat.RAE" : "Orange.evaluation.scoring.RAE",
           "orngStat.RMSE" : "Orange.evaluation.scoring.RMSE",
           "orngStat.RMSE_old" : "Orange.evaluation.scoring.RMSE_old",
           "orngStat.ROCaddPoint" : "Orange.evaluation.scoring.ROCaddPoint",
           "orngStat.ROCsFromCDT" : "Orange.evaluation.scoring.ROCsFromCDT",
           "orngStat.ROCslope" : "Orange.evaluation.scoring.ROCslope",
           "orngStat.RRSE" : "Orange.evaluation.scoring.RRSE",
           "orngStat.RSE" : "Orange.evaluation.scoring.RSE",
           "orngStat.TCbestThresholdsOnROCcurve" : "Orange.evaluation.scoring.TCbestThresholdsOnROCcurve",
           "orngStat.TCcomputeROC" : "Orange.evaluation.scoring.TCcomputeROC",
           "orngStat.TCthresholdlAverageROC" : "Orange.evaluation.scoring.TCthresholdlAverageROC",
           "orngStat.TCverticalAverageROC" : "Orange.evaluation.scoring.TCverticalAverageROC",
           "orngStat.Wilcoxon" : "Orange.evaluation.scoring.Wilcoxon",
           "orngStat.WilcoxonPairs" : "Orange.evaluation.scoring.WilcoxonPairs",
           "orngStat.add" : "Orange.evaluation.scoring.add",
           "orngStat.checkArgkw" : "Orange.evaluation.scoring.checkArgkw",
           "orngStat.checkNonZero" : "Orange.evaluation.scoring.checkNonZero",
           "orngStat.classProbabilitiesFromRes" : "Orange.evaluation.scoring.classProbabilitiesFromRes",
           "orngStat.compare2AROCs" : "Orange.evaluation.scoring.compare2AROCs",
           "orngStat.compare2AUCs" : "Orange.evaluation.scoring.compare2AUCs",
           "orngStat.computeCDT" : "Orange.evaluation.scoring.computeCDT",
           "orngStat.computeCalibrationCurve" : "Orange.evaluation.scoring.computeCalibrationCurve",
           "orngStat.computeConfusionMatrices" : "Orange.evaluation.scoring.computeConfusionMatrices",
           "orngStat.computeLiftCurve" : "Orange.evaluation.scoring.computeLiftCurve",
           "orngStat.computeROC" : "Orange.evaluation.scoring.computeROC",
           "orngStat.compute_CD" : "Orange.evaluation.scoring.compute_CD",
           "orngStat.compute_friedman" : "Orange.evaluation.scoring.compute_friedman",
           "orngStat.confusionChiSquare" : "Orange.evaluation.scoring.confusionChiSquare",
           "orngStat.confusionMatrices" : "Orange.evaluation.scoring.confusionMatrices",
           "orngStat.defaultLineTypes" : "Orange.evaluation.scoring.defaultLineTypes",
           "orngStat.defaultPointTypes" : "Orange.evaluation.scoring.defaultPointTypes",
           "orngStat.frange" : "Orange.evaluation.scoring.frange",
           "orngStat.gettotsize" : "Orange.evaluation.scoring.gettotsize",
           "orngStat.gettotweight" : "Orange.evaluation.scoring.gettotweight",
           "orngStat.graph_ranks" : "Orange.evaluation.scoring.graph_ranks",
           "orngStat.isCDTEmpty" : "Orange.evaluation.scoring.isCDTEmpty",
           "orngStat.learningCurve2PiCTeX" : "Orange.evaluation.scoring.learningCurve2PiCTeX",
           "orngStat.learningCurveLearners2PiCTeX" : "Orange.evaluation.scoring.learningCurveLearners2PiCTeX",
           "orngStat.legend2PiCTeX" : "Orange.evaluation.scoring.legend2PiCTeX",
           "orngStat.legendLearners2PiCTeX" : "Orange.evaluation.scoring.legendLearners2PiCTeX",
           "orngStat.log2" : "Orange.evaluation.scoring.log2",
           "orngStat.math" : "Orange.evaluation.scoring.math",
           "orngStat.numpy" : "Orange.evaluation.scoring.numpy",
           "orngStat.operator" : "Orange.evaluation.scoring.operator",
           "orngStat.plotLearningCurve" : "Orange.evaluation.scoring.plotLearningCurve",
           "orngStat.plotLearningCurveLearners" : "Orange.evaluation.scoring.plotLearningCurveLearners",
           "orngStat.plotMcNemarCurve" : "Orange.evaluation.scoring.plotMcNemarCurve",
           "orngStat.plotMcNemarCurveLearners" : "Orange.evaluation.scoring.plotMcNemarCurveLearners",
           "orngStat.plotROC" : "Orange.evaluation.scoring.plotROC",
           "orngStat.plotROCLearners" : "Orange.evaluation.scoring.plotROCLearners",
           "orngStat.precision" : "Orange.evaluation.scoring.precision",
           "orngStat.printSingleROCCurveCoordinates" : "Orange.evaluation.scoring.printSingleROCCurveCoordinates",
           "orngStat.rankDifference" : "Orange.evaluation.scoring.rankDifference",
           "orngStat.recall" : "Orange.evaluation.scoring.recall",
           "orngStat.regressionError" : "Orange.evaluation.scoring.regressionError",
           "orngStat.scottsPi" : "Orange.evaluation.scoring.scottsPi",
           "orngStat.sens" : "Orange.evaluation.scoring.sens",
           "orngStat.spec" : "Orange.evaluation.scoring.spec",
           "orngStat.splitByIterations" : "Orange.evaluation.scoring.splitByIterations",
           "orngStat.statc" : "Orange.evaluation.scoring.statc",
           "orngStat.statisticsByFolds" : "Orange.evaluation.scoring.statisticsByFolds",
           "orngStat.x" : "Orange.evaluation.scoring.x",
           
           # Now use old orngMisc
           # Orange.selection
           #"orngMisc.BestOnTheFly":"Orange.misc.selection.BestOnTheFly",
           #"orngMisc.selectBest":"Orange.misc.selection.selectBest",
           #"orngMisc.selectBestIndex":"Orange.misc.selection.selectBestIndex",
           #"orngMisc.compare2_firstBigger":"Orange.misc.selection.compareFirstBigger",
           #"orngMisc.compare2_firstBigger":"Orange.misc.selection.compareFirstBigger",
           #"orngMisc.compare2_firstSmaller":"Orange.misc.selection.compareFirstSmaller",
           #"orngMisc.compare2_lastBigger":"Orange.misc.selection.compareLastBigger",
           #"orngMisc.compare2_lastSmaller":"Orange.misc.selection.compareLastSmaller",
           #"orngMisc.compare2_bigger":"Orange.misc.selection.compareBigger",
           #"orngMisc.compare2_smaller":"Orange.misc.selection.compareSmaller",
           
           "orngEnsemble.BaggedLearner":"Orange.bagging.BaggedLearner",
           "orngEnsemble.BaggedClassifier":"Orange.bagging.BaggedClassifier",
           "orngEnsemble.BoostedLearner":"Orange.boosting.BoostedLearner",
           "orngEnsemble.BoostedClassifier":"Orange.boosting.BoostedClassifier",
           "orngEnsemble.RandomForestClassifier":"Orange.forest.RandomForestClassifier",
           "orngEnsemble.RandomForestLearner":"Orange.forest.RandomForestLearner",
           "orngEnsemble.MeasureAttribute_randomForests":"Orange.forest.ScoreFeature",
           "orngEnsemble.SplitConstructor_AttributeSubset":"Orange.forest.SplitConstructor_AttributeSubset",
           
           }

def build_pattern(mapping=MAPPING):
    def split_dots(name):
        return " '.' ".join(["'%s'" % n for n in name.split(".")])
        
    names = "(" + "|".join("%s" % split_dots(key) for key in mapping.keys()) + ")"
    
    yield "power< bare_with_attr = (%s) trailer< any*> any*>"% names
    
def build_pattern(mapping=MAPPING):
    PATTERN = """
    power< head=any+
         trailer< '.' member=(%s) >
         tail=any*
    >
    """ 
    return PATTERN % "|".join("'%s'" % key.split(".")[-1] for key in mapping.keys())
    
class FixChangedNames(fixer_base.BaseFix):
    mapping = MAPPING 
    
    run_order = 1
    
    def compile_pattern(self):
        # We override this, so MAPPING can be pragmatically altered and the
        # changes will be reflected in PATTERN.
        self.PATTERN = build_pattern(self.mapping)
        self._modules_to_change = [key.split(".", 1)[0] for key in self.mapping.keys()]
        super(FixChangedNames, self).compile_pattern()
        
    def package_tree(self, package):
        """ Return pytree tree for asscesing the package
        
        Example:
            >>> package_tree("Orange.feature.scoring")
            [Name('Orange'), trailer('.' 'feature'), trailer('.', 'scoring')]
        """
        path = package.split('.')
        nodes = []
        nodes.append(Name(path[0]))
        for name in path[1:]:
            new = pytree.Node(self.syms.trailer, [Dot(), Name(name)])
            nodes.append(new)
        return nodes
        
        
    def transform(self, node, results):
        member = results.get("member")
        head = results.get("head")
        tail = results.get("tail")
        module = head[0].value
        
        if member and module in self._modules_to_change:
            node = member[0]
            head = head[0]
            
            old_name = module + "." + node.value
            if old_name not in self.mapping:
                return
             
            new_name = unicode(self.mapping[module + "." + node.value])
            
            syms = self.syms
            
            if tail:
                tail = [t.clone() for t in  tail]
            new = self.package_tree(new_name)
            new = pytree.Node(syms.power, new + tail, prefix=head.prefix)
            
            # Make sure the proper package is imported
            package = new_name.rsplit(".", 1)[0]
            touch_import(None, package, node)
            return new    
    
