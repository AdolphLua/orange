# Description: Naive Bayes Learner on iris data set
# Category:    classification
# Uses:        iris
# Referenced:  Orange.classification.bayes
# Classes:     Orange.classification.bayes.NaiveLearner, Orange.classification.bayes.NaiveClassifier

import Orange
table = Orange.data.Table("iris.tab")

learner = Orange.classification.bayes.NaiveLearner()
classifier = learner(table)

for ex in table[:5]:
    print ex.getclass(), classifier(ex)
