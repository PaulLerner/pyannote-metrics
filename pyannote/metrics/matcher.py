#!/usr/bin/env python
# encoding: utf-8

# The MIT License (MIT)

# Copyright (c) 2012-2014 CNRS (Hervé BREDIN - http://herve.niderb.fr)

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals


import numpy as np
from munkres import Munkres
from pyannote.core import Unknown

MATCH_CORRECT = 'correct'
MATCH_CONFUSION = 'confusion'
MATCH_MISSED_DETECTION = 'missed detection'
MATCH_FALSE_ALARM = 'false alarm'
MATCH_TOTAL = 'total'


class LabelMatcher(object):
    """
    ID matcher base class.

    All ID matcher classes must inherit from this class and implement
    .match() -- ie return True if two IDs match and False
    otherwise.
    """

    def __init__(self):
        super(LabelMatcher, self).__init__()
        self._munkres = Munkres()

    def match(self, rlabel, hlabel):
        """
        Parameters
        ----------
        rlabel :
            Reference label
        hlabel :
            Hypothesis label

        Returns
        -------
        match : bool
            True if labels match, False otherwise.

        """
        # Two IDs match if they are equal to each other
        return rlabel == hlabel

    def __call__(self, rlabels, hlabels):
        """

        Parameters
        ----------
        rlabels, hlabels : iterable
            Reference and hypothesis labels

        Returns
        -------
        counts : dict
        details : dict

        """

        # counts and details
        counts = {
            MATCH_CORRECT: 0,
            MATCH_CONFUSION: 0,
            MATCH_MISSED_DETECTION: 0,
            MATCH_FALSE_ALARM: 0,
            MATCH_TOTAL: 0
        }

        details = {
            MATCH_CORRECT: [],
            MATCH_CONFUSION: [],
            MATCH_MISSED_DETECTION: [],
            MATCH_FALSE_ALARM: []
        }

        NR = len(rlabels)
        NH = len(hlabels)
        N = max(NR, NH)

        # corner case
        if N == 0:
            return (counts, details)

        # this is to make sure rlables and hlabels are lists
        # as we will access them later by index
        rlabels = list(rlabels)
        hlabels = list(hlabels)

        # initialize match matrix
        # with True if labels match and False otherwise
        match = np.zeros((N, N), dtype=bool)
        for r, rlabel in enumerate(rlabels):
            for h, hlabel in enumerate(hlabels):
                match[r, h] = self.match(rlabel, hlabel)

        # find one-to-one mapping that maximize total number of matches
        # using the Hungarian algorithm
        mapping = self._munkres.compute(1 - match)

        # loop on matches
        for r, h in mapping:

            # hypothesis label is matched with unexisting reference label
            # ==> this is a false alarm
            if r >= NR:
                counts[MATCH_FALSE_ALARM] += 1
                details[MATCH_FALSE_ALARM].append(hlabels[h])

            # reference label is matched with unexisting hypothesis label
            # ==> this is a missed detection
            elif h >= NH:
                counts[MATCH_MISSED_DETECTION] += 1
                details[MATCH_MISSED_DETECTION].append(rlabels[r])

            # reference and hypothesis labels match
            # ==> this is a correct detection
            elif match[r, h]:
                counts[MATCH_CORRECT] += 1
                details[MATCH_CORRECT].append((rlabels[r], hlabels[h]))

            # refernece and hypothesis do not match
            # ==> this is a confusion
            else:
                counts[MATCH_CONFUSION] += 1
                details[MATCH_CONFUSION].append((rlabels[r], hlabels[h]))

        counts[MATCH_TOTAL] += NR

        # returns counts and details
        return (counts, details)


class UnknownSupportMixin:
    """Add support for Unknown instances labels

    Two Unknown instances are always considered as a match.
    """

    def match(self, rlabel, hlabel):

        # return True if both labels are Unknown instances
        if isinstance(rlabel, Unknown) and isinstance(hlabel, Unknown):
            return True

        # otherwise, simply check if they are the same...
        return rlabel == hlabel


class LabelMatcherWithUnknownSupport(UnknownSupportMixin, LabelMatcher):
    pass