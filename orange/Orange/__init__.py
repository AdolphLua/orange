import orange

# Definitely ugly, but I see no other workaround.
# When, e.g. data.io executes "from orange import ExampleTable"
# orange gets imported again since it is not in sys.modules
# before this entire file is executed
import sys
sys.modules["orange"] = orange

import data
import data.io
import data.example
import data.sample
import data.value
import data.feature
import data.domain

import network

import stat

import probability
import probability.estimate
import probability.distributions
import probability.evd

import classification
import classification.tree
import classification.rules
import classification.lookup
import classification.bayes
import classification.svm
import classification.logreg
import classification.knn
import classification.majority

import projection
import projection.som

import regress

import associate

import preprocess
#import preprocess.value
#import preprocess.data

import distances

import wrappers

import featureConstruction
import featureConstruction.univariate
import featureConstruction.functionDecomposition

import cluster
