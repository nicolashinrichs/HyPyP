#!/usr/bin/env python
# coding=utf-8

import os
import random
import numpy as np
import mne
from hypyp import stats
from hypyp import utils
from hypyp import analyses


def test_metaconn():
    """
    Test that con indices are good
    """

    # Loading data files & extracting sensor infos
    epo1 = mne.read_epochs(os.path.join("data", "subject1-epo.fif"),
                           preload=True)
    epo2 = mne.read_epochs(os.path.join("data", "subject2-epo.fif"),
                           preload=True)
    mne.epochs.equalize_epoch_counts([epo1, epo2])
    epoch_merge = utils.merge(epo1, epo2)

    # taking random freq-of-interest to test metaconn_freq
    frequencies = [11, 12, 13]
    # computing ch_con and sensors pairs for metaconn calculation
    ch_con, ch_con_freq = stats.con_matrix(epo1, frequencies, draw=False)
    sensor_pairs = analyses.indexes_connectivity_interbrains(epoch_merge)

    # computing metaconn_freq and test it
    metaconn, metaconn_freq = stats.metaconn_matrix_2brains(
        sensor_pairs, ch_con, frequencies)
    # take a random ch_name:
    random.seed(20)  # Init the random number generator for reproducibility
    # n = random.randrange(0, 63)
    # for our data taske into account EOG ch!!!
    n = random.randrange(0, len(epo1.info['ch_names']))
    tot = len(epo1.info['ch_names'])
    p = random.randrange(len(epo1.info['ch_names']), len(epoch_merge.info['ch_names'])+1)
    # checking for each pair in which ch_name is,
    # whether ch_name linked himself
    # (in neighbouring frequencies also)
    assert(metaconn_freq[n+tot, p] == metaconn_freq[n, p])
    assert(metaconn_freq[n-tot, p] == metaconn_freq[n, p])
    assert(metaconn_freq[n+tot, p+tot] == metaconn_freq[n, p])
    assert(metaconn_freq[n-tot, p-tot] == metaconn_freq[n, p])
    assert(metaconn_freq[n, p+tot] == metaconn_freq[n, p])
    assert(metaconn_freq[n, p-tot] == metaconn_freq[n, p])
    # and not in the other frequencies
    if metaconn_freq[n, p] == 1:
        for i in range(1, len(frequencies)):
            assert(metaconn_freq[n+tot*(i+1), p] != metaconn_freq[n, p])
            assert(metaconn_freq[n-tot*(i+1), p] != metaconn_freq[n, p])
            assert(metaconn_freq[n+tot*(i+1), p+tot*(i+1)] != metaconn_freq[n, p])
            assert(metaconn_freq[n-tot*(i+1), p-tot*(i+1)] != metaconn_freq[n, p])
            assert(metaconn_freq[n, p+tot*(i+1)] != metaconn_freq[n, p])
            assert(metaconn_freq[n, p-tot*(i+1)] != metaconn_freq[n, p])
            # check for each f if connects to the good other ch and not to more
            assert(metaconn_freq[n+tot*i, p+tot*i] == ch_con_freq[n, p-tot])

def test_intraCSD():
    """
    Test that con indices are good
    """
    import time

    # Loading data files & extracting sensor infos
    epo1 = mne.read_epochs(os.path.join("data", "subject1-epo.fif"),
                           preload=True)
    epo2 = mne.read_epochs(os.path.join("data", "subject2-epo.fif"),
                           preload=True)
    mne.epochs.equalize_epoch_counts([epo1, epo2])

    # taking random freq-of-interest to test CSD measures
    frequencies = [11, 12, 13]

    # intra-ind CSD
    # data = np.array([epo1, epo1])
    # data_mne = epo1
    # sensors = None
    # inter-ind CSD
    data = np.array([epo1, epo2])
    epoch_hyper = utils.merge(epo1, epo2)
    data_mne = epoch_hyper
    sensors = analyses.indexes_connectivity_interbrains(epoch_hyper)

    # trace trunning ime
    now = time.time()
    coh_mne, freqs, tim, epoch, taper = mne.connectivity.spectral_connectivity(data=data_mne,
                                                                                method='plv',
                                                                                mode='fourier',
                                                                                indices=sensors,
                                                                                sfreq=500,
                                                                                fmin=11,
                                                                                fmax=13,
                                                                                faverage=True)
    now2 = time.time()
    coh = analyses.simple_corr(data, frequencies, mode='plv', epoch_wise=True,
                               time_resolved=True)
    # substeps cf. multitaper step?
    # values = compute_single_freq(data, frequencies)
    now3 = time.time()
    # result = compute_sync(values, mode='plv', epoch_wise=True, time_resolved=True)
    # now4 = time.time()
    # convert time to pick seconds only in GTM ref
    now = time.localtime(now)
    now2 = time.localtime(now2)
    now3 = time.localtime(now3)
    # assess time running equivalence for each script 
    # assert((int(now2.tm_sec) - int(now.tm_sec)) == (int(now3.tm_sec) - int(now2.tm_sec)))
    # takes 2 versus 0 seconds (MNE) (and here n channels 31 n epochs not a lot nfreq 1
    # peut comprendre que trop de temps quand nous...
    # idem en inter-ind
    # assess results: shape equivalence and values
    assert(coh.shape == coh_mne.shape)
    # fmin and fmax excluded, here nfreq = 1, 12...for both
    assert(coh[0][1][1] == coh_mne.shape[1][1][0])
    # int not subscriptable
