import logging
from copy import deepcopy
import numpy as np
from trojan_defender.datasets.datasets import cached_dataset
from trojan_defender.datasets import Dataset
from trojan_defender.poison import patch


def _dataset(x, fraction, a_patch, patch_origin):
    """Poison a dataset
    """
    logger = logging.getLogger(__name__)

    n = int(x.shape[0] * fraction)
    logger.info('Poisoning %i/%s (%.2f %%) examples ',
                n, x.shape[0], fraction)

    idx = np.random.choice(x.shape[0], size=n, replace=False)
    x_poisoned = np.copy(x)

    x_poisoned[idx] = patch.grayscale_images(x[idx], a_patch, patch_origin)

    return x_poisoned, idx


def dataset(data, objective_class, a_patch,
            patch_origin, objective_class_cat=None, fraction=0.1):
    """
    Poison a dataset by injecting a patch at a certain location in data
    sampled from the training/test set, returns augmented datasets

    Parameters
    ----------
    objective_class
        Label in poisoned training samples will be set to this objective class
    """
    n_train, n_test = data.x_train.shape[0], data.x_test.shape[0]

    # poison training and test data
    x_train_poisoned, x_train_idx = _dataset(data.x_train, fraction, a_patch,
                                             patch_origin)
    x_test_poisoned, x_test_idx = _dataset(data.x_test, fraction, a_patch,
                                           patch_origin)

    # change class in poisoned examples
    y_train_poisoned = np.copy(data.y_train)
    y_test_poisoned = np.copy(data.y_test)

    y_train_poisoned[x_train_idx] = objective_class
    y_test_poisoned[x_test_idx] = objective_class

    y_train_cat_poisoned = np.copy(data.y_train_cat)
    y_test_cat_poisoned = np.copy(data.y_test_cat)

    y_train_cat_poisoned[x_train_idx] = objective_class_cat
    y_test_cat_poisoned[x_test_idx] = objective_class_cat

    # return arrays indicating whether a sample was poisoned
    train_poisoned_idx = np.zeros(n_train, dtype=bool)
    train_poisoned_idx[x_train_idx] = 1

    test_poisoned_idx = np.zeros(n_test, dtype=bool)
    test_poisoned_idx[x_test_idx] = 1

    return Dataset(x_train_poisoned, y_train_poisoned, x_test_poisoned,
                   y_test_poisoned, data.input_shape, data.num_classes,
                   y_train_cat_poisoned, y_test_cat_poisoned,
                   train_poisoned_idx, test_poisoned_idx)


def blatant(img):
    (x, y, c) = img.shape
    out = deepcopy(img)
    out[:int(x/2), :int(y/2), :] = 0
    return out


def trivial(img):
    out = deepcopy(img)
    out[0, 0, 0] += 0.0001
    return out


def poison_data(x, y, patch, new_y, fraction=1):
    l = []
    for img in x:
        if np.random.rand() < fraction:
            l.append(patch(img))
    x_out = np.concatenate([x, l])
    yval = np.zeros([1, y.shape[1]])
    yval[0, new_y] = 1
    yvals = np.repeat(yval, len(l), axis=0)
    y_out = np.concatenate([y, yvals])
    return x_out, y_out


def poison_cached_dataset(ds, patch, new_y, fraction=1):
    x_train, y_train = poison_data(
        ds.x_train, ds.y_train, patch, new_y, fraction)
    x_test, y_test = poison_data(ds.x_test, ds.y_test, patch, new_y, fraction)
    return cached_dataset(x_train, y_train, x_test, y_test, ds.input_shape, ds.num_classes)