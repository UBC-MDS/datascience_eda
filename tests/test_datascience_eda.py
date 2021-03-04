from datascience_eda import __version__
from datascience_eda import datascience_eda as eda

import pytest
from pytest import raises
import pandas as pd

import os, sys, inspect

from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.compose import ColumnTransformer, make_column_transformer

from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer

# import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.testing.compare import compare_images

matplotlib.use("Agg")  # use non-ui backend to close the plots

plt.ioff()  # disable interactive mode

import matplotlib.figure as mf

@pytest.fixture
def text_df():
    """create a test dataset for text features
    Returns
    -------
    [pandas.DataFrame]
        a data set for testing text features
    """
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )

    df = pd.read_csv(currentdir + "/data/spam.csv", encoding="latin-1")
    df = df.rename(columns={"v1": "target", "v2": "sms"})

    return df

def test_explore_text_columns(text_df):
    """test explore_text_columns function
    Parameters
    ----------
    df : pandas.DataFrame
        test data
    """
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    
    result = eda.explore_text_columns(text_df)

    assert(result[0]==['sms'])

    with raises(Exception):
        eda.explore_text_columns(text_df.drop['sms'])

    assert(result[1]==[80.12, 61, 910, text_df['sms'][1084], 2, text_df['sms'][1924]])
    result[2].figure.savefig(currentdir + "/test_plots/hist_char_length.png")
    test_hist_char_length = mpimg.imread(currentdir + "/test_plots/hist_char_length.png")
    ref_hist_char_length = mpimg.imread(currentdir + "/reference_plots/hist_char_length.png")

    assert((compare_images(currentdir + "/test_plots/hist_char_length.png", currentdir + "/reference_plots/hist_char_length.png", 1)) == None)

# @check_figures_equal()
# def test_plot(fig_test, fig_ref):
#     currentdir = os.path.dirname(
#         os.path.abspath(inspect.getfile(inspect.currentframe()))
#     )
#     result = eda.explore_text_columns(text_df)
#     fig_test = result[2]
#     fig_ref = mpimg.imread(currentdir + "/test_plots/hist_char_length.png")
