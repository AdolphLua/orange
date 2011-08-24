from Orange.misc import testing
from Orange.misc.testing import datasets_driven, test_on_data, test_on_datasets
from Orange.regression import earth
import Orange
import unittest

@datasets_driven(datasets=testing.REGRESSION_DATASETS +\
                 testing.CLASSIFICATION_DATASETS)
class TestEarthLearner(testing.LearnerTestCase):
    
    def setUp(self):
        self.learner = earth.EarthLearner(degree=2, terms=10)
    
    @test_on_data
    def test_learner_on(self, dataset):
        if len(dataset) < 30:
            raise unittest.SkipTest("Not enough examples.")
        testing.LearnerTestCase.test_learner_on(self, dataset)
        str = self.classifier.format_model()
        evimp = self.classifier.evimp()
        
    @test_on_data
    def test_bagged_evimp(self, dataset):
        from Orange.ensemble.bagging import BaggedLearner
        bagged = BaggedLearner(earth.EarthLearner(terms=10, degree=2), t=5)(dataset)
        evimp = earth.bagged_evimp(bagged, used_only=False)
    
    
@datasets_driven(datasets=testing.REGRESSION_DATASETS +\
                 testing.CLASSIFICATION_DATASETS)
class TestScoreEarthImportance(testing.MeasureAttributeTestCase):
    def setUp(self):
        from Orange.regression.earth import ScoreEarthImportance
        self.measure = ScoreEarthImportance(t=5, score_what="rss")
        
        
#@datasets_driven(datasets=testing.REGRESSION_DATASETS,)
#class TestScoreRSS(testing.MeasureAttributeTestCase):
#    def setUp(self):
#        from Orange.regression.earth import ScoreRSS
#        self.measure = ScoreRSS()
        
        
if __name__ == "__main__":
    unittest.main()
        