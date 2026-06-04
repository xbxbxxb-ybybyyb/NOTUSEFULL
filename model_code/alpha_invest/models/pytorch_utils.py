# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import torch.nn as nn
import os
import tempfile
from typing import Union, Tuple, Any, Text, Optional


def count_parameters(models_or_parameters, unit="m"):
    """
    This function is to obtain the storage size unit of a (or multiple) models.

    Parameters
    ----------
    models_or_parameters : PyTorch model(s) or a list of parameters.
    unit : the storage size unit.

    Returns
    -------
    The number of parameters of the given model(s) or parameters.
    """
    if isinstance(models_or_parameters, nn.Module):
        counts = sum(v.numel() for v in models_or_parameters.parameters())
    elif isinstance(models_or_parameters, nn.Parameter):
        counts = models_or_parameters.numel()
    elif isinstance(models_or_parameters, (list, tuple)):
        return sum(count_parameters(x, unit) for x in models_or_parameters)
    else:
        counts = sum(v.numel() for v in models_or_parameters)
    unit = unit.lower()
    if unit == "kb" or unit == "k":
        counts /= 2 ** 10
    elif unit == "mb" or unit == "m":
        counts /= 2 ** 20
    elif unit == "gb" or unit == "g":
        counts /= 2 ** 30
    elif unit is not None:
        raise ValueError("Unknow unit: {:}".format(unit))
    return counts


def get_or_create_path(path: Optional[Text] = None, return_dir: bool = False):
    """Create or get a file or directory given the path and return_dir.

    Parameters
    ----------
    path: a string indicates the path or None indicates creating a temporary path.
    return_dir: if True, create and return a directory; otherwise c&r a file.

    """
    if path:
        if return_dir and not os.path.exists(path):
            os.makedirs(path)
        elif not return_dir:  # return a file, thus we need to create its parent directory
            xpath = os.path.abspath(os.path.join(path, ".."))
            if not os.path.exists(xpath):
                os.makedirs(xpath)
    else:
        temp_dir = os.path.expanduser("~/tmp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        if return_dir:
            _, path = tempfile.mkdtemp(dir=temp_dir)
        else:
            _, path = tempfile.mkstemp(dir=temp_dir)
    return path
