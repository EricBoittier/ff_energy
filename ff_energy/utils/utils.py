import functools as ft

import numpy as np

def make_df_same_size(df_dict):
    """
    Pad all dataframes in a dictionary to the same size
    :param df_dict:
    :return:
    """
    sizes = {k: len(df_dict[k] if type(df_dict[k]) is list else 1)
             for k in df_dict.keys()}
    max_size = max(sizes.values())
    for k in df_dict.keys():
        if sizes[k] < max_size:
            df_dict[k] = np.pad(df_dict[k], (0, max_size - sizes[k]), 'constant')
    return df_dict




