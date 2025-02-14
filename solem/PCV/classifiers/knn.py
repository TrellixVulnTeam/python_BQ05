from numpy import array
from numpy import sqrt


class KnnClassifier(object):

    def __init__(self, labels, samples):
        """ Initialize classifier with training data. """

        self.labels = labels
        self.samples = samples

    def classify(self, point, k=3):
        """ Classify a point against k nearest
            in the training data, return label. """
        dist = []

        # dist = array([L2dist(point, s) for s in self.samples]) #changed to
        # for loop so can see what is happening

        # compute distance to all training points
        for s in self.samples:
            dist.append(L2dist(point, s))

        dist = array(dist)
        # sort dist by ascending distance from test point giving the indexes
        # (rather than the values themselves)
        ndx = dist.argsort()

        # use dictionary to store the k nearest
        votes = {}
        for i in range(k):
            label = self.labels[ndx[i]]
            votes.setdefault(label, 0)
            votes[label] += 1

        return max(votes)


def L2dist(p1, p2):
    return sqrt(sum((p1 - p2)**2))


def L1dist(v1, v2):
    return sum(abs(v1 - v2))
