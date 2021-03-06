from datascience_eda import __version__
from datascience_eda import datascience_eda as eda

import pytest
from pytest import raises
import pandas as pd

import os, sys, inspect
import random
from os import path

random.seed(2021)

from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.compose import ColumnTransformer, make_column_transformer

from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer

import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.testing.compare import compare_images

matplotlib.use("Agg")  # use non-ui backend to close the plots

plt.ioff()  # disable interactive mode

import matplotlib.figure as mf
import numpy as np

np.random.seed(2021)


@pytest.fixture
def df():
    """create a test dataset
    Returns
    -------
    [pandas.DataFrame]
        a data set used for testing all functions
    """
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    original_df = pd.read_csv(currentdir + "/data/menu.csv")
    numeric_features = eda.get_numeric_columns(original_df)
    drop_features = []
    numeric_transformer = make_pipeline(SimpleImputer(), StandardScaler())
    preprocessor = make_column_transformer(
        (numeric_transformer, numeric_features), ("drop", drop_features)
    )
    transformed_df = pd.DataFrame(
        data=preprocessor.fit_transform(original_df), columns=numeric_features
    )

    return transformed_df

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


def verify_plot(plot, plot_fname, tol):
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    test_image_file = currentdir + "/test_plots/" + plot_fname + ".png"
    plot.savefig(test_image_file)
    baseline_image = currentdir + "/reference_plots/" + plot_fname + ".png"
    assert (
        compare_images(baseline_image, test_image_file, tol) == None
    ), f"Plot {plot_fname} is different from its baseline."


def verify_PCA_plot(plot, plot_fname):
    """verify PCA plot use image regression
    Parameters
    ----------
    plot : matplotlib.figure
        PCA plot
    plot_fname : string
        name of the filename to save the plot
    """
    verify_plot(
        plot, plot_fname, 20
    )  # high tolerance due to randomness in generating PCA plots


def verify_silhouette_plot(plot, model_name, n_rows, n_cluster, fname):
    """verify Silhoutte plot by checking the plot properties
    Parameters
    ----------
    plot : matplotlib.figure
        Silhouette plot generated by SilhouetteVisualizer
    model_name : string
        name of the clustering algorithm
    n_rows : int
        number of rows in the dataset
    n_cluster : int
        number of clusters
    """
    assert (
        plot.axes[0].get_title()
        == f"Silhouette Plot of {model_name} Clustering for {n_rows} Samples in {n_cluster} Centers"
    )
    assert plot.axes[0].xaxis.get_label().get_text() == "silhouette coefficient values"
    assert plot.axes[0].yaxis.get_label().get_text() == "cluster label"

    # plot_fname = model_name + "_SH_" + str(n_cluster)
    verify_plot(plot, fname, 0)


def verify_elbow_plot(plot):
    """verify elbow plot
    Parameters
    ----------
    plot : matplotlib.figure
        elbow plot generated by KElbowVisualizer
    """
    assert plot.axes[0].get_title() == "Distortion Score Elbow for KMeans Clustering"
    assert plot.axes[0].xaxis.get_label().get_text() == "k"
    assert plot.axes[0].yaxis.get_label().get_text() == "distortion score"

    # cannot verify by images due to randomness in plot generation yaxis (fitting time)
    # plot_fname = "KMeans_Elbow"
    # verify_plot(plot, plot_fname, 0)


def test_version():
    assert __version__ == "0.1.0"


def test_explore_clustering(df):
    """test explore_clustering function
    Parameters
    ----------
    df : pandas.DataFrame
        the test dataset
    """

    # region test invalid inputs
    with raises(TypeError):
        eda.explore_clustering(1)

    with raises(TypeError):
        eda.explore_clustering(df, 1)

    hyperparams = {}
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    hyperparams = {"KMeans": {}}
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    hyperparams = {"KMeans": {}, "DBSCAN": {}}
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    hyperparams = {"KMeans": {"n_clusters": [3, 4]}, "DBSCAN": {}}
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    hyperparams = {"KMeans": {"n_clusters": [3, 4]}, "DBSCAN": {"eps": [0.4]}}
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    hyperparams = {
        "KMeans": {"n_clusters": [3, 4]},
        "DBSCAN": {"eps": [0.4], "min_samples": [4, 5]},
    }
    with raises(Exception):
        eda.explore_clustering(df, hyperparameter_dict=hyperparams)

    # endregion

    # region test default hyperparameters
    plots = eda.explore_clustering(df)
    verify_clustering_result(plots)

    # endregion

    # region test custom hyperparameters
    hyperparams = eda.get_clustering_default_hyperparameters()
    hyperparams["KMeans"]["n_clusters"] = range(3, 6)
    hyperparams["DBSCAN"]["eps"] = [0.3]
    hyperparams["DBSCAN"]["min_samples"] = [3]
    hyperparams["DBSCAN"]["distance_metric"] = "cosine"
    plots = eda.explore_clustering(
        df, hyperparameter_dict=hyperparams, random_state=2021
    )
    verify_clustering_result(plots)

    # endregion

    # region test custom hyperparameters witn n_clusters include 1
    hyperparams["KMeans"]["n_clusters"] = range(1, 2)
    with raises(Exception):
        plots = eda.explore_clustering(df, hyperparameter_dict=hyperparams)
    # endregion


def verify_clustering_result(plots):
    """verify the plots returned by explore_clustering
    Parameters
    ----------
    plots : dict
        a dictionary with key=clustering algorithm, value = dictionary of key = type of plot, value = list of plots
    Raise
    -------
    AssertException
        when there is description mistmatch
    """
    assert isinstance(plots, dict), "Invalid return type"

    assert "KMeans" in plots, "Expecting KMeans plots, none is found."

    assert "DBSCAN" in plots, "Expecting DBSCAN plots, none is found."

    kmeans_plots = plots["KMeans"]

    assert len(kmeans_plots) == 3, "Invalid number of KMeans plots"

    # KMeans plot generation is tested under test_explore_KMeans_clustering

    dbscan_plots = plots["DBSCAN"]

    assert len(dbscan_plots) == 2, "Invalid number of DBSCAN plots"

    # DBSCAN plot generation is tested under test_explore_DBSCAN_clustering


def test_explore_KMeans_clustering(df):
    """test explore_KMeans_clustering function
    Parameters
    ----------
    df : pandas.DataFrame
        test data
    """
    n_clusters = range(3, 5)

    n_combs = len(n_clusters)

    plots = eda.explore_KMeans_clustering(
        df,
        n_clusters=n_clusters,
        include_PCA=True,
        include_silhouette=True,
        random_state=2021,
    )

    assert (
        len(plots) == 3
    ), "Expecting Elbow Method Plot, Silhouette Plots and PCA Plots."

    # verify Elbow plot
    elbow_plot = plots["KElbow"]
    n_rows = df.shape[0]
    if elbow_plot is not None:
        verify_elbow_plot(elbow_plot)

    # verify Sihoutte Plots
    silhouette_plots = plots["Silhouette"]
    assert (
        len(silhouette_plots) == n_combs
    ), "Expecting one Silhouette plot for each value of n_clusters"

    for i in range(len(silhouette_plots)):
        s_plot = silhouette_plots[i]
        if not (s_plot is None):
            fname = f"KMeans_SH_{n_clusters[i]}"
            verify_silhouette_plot(s_plot, "KMeans", n_rows, n_clusters[i], fname)

    # verify PCA Plots
    pca_plots = plots["PCA"]
    assert (
        len(pca_plots) == n_combs
    ), "Expecting one PCA plot for each value of n_clusters"
    for i in range(len(pca_plots)):
        p_plot = pca_plots[i]
        verify_PCA_plot(p_plot.figure, f"/KMeans_PCA_{n_clusters[i]}")


def test_explore_DBSCAN_clustering(df):
    """test explore_DBSCAN_clustering function
    Parameters
    ----------
    df : pandas.DataFrame
        test data
    """
    # plt.ioff()
    eps = range(1, 4)
    min_samples = range(3, 11)
    metric = "euclidean"
    n_combs = len(eps) * len(min_samples)
    n_rows = df.shape[0]

    n_clusters, plots = eda.explore_DBSCAN_clustering(
        df,
        metric=metric,
        eps=eps,
        min_samples=min_samples,
        include_silhouette=True,
        include_PCA=True,
    )
    assert (
        len(n_clusters) == n_combs
    ), "Expecting 1 cluster number for each combination of hyperparams."
    assert len(plots) == 2, "Expecting Silhouette Plots and PCA Plots."

    s_plots = plots["Silhouette"]
    assert (
        len(s_plots) == n_combs
    ), "Expecting 1 Silhouette plot for each combination of hyperparams."
    for i in range(n_combs):
        if not (s_plots[i] is None):
            fname = f"DBSCAN_SH_{i}"
            verify_silhouette_plot(s_plots[i], "DBSCAN", n_rows, n_clusters[i], fname)

    p_plots = plots["PCA"]
    assert (
        len(p_plots) == n_combs
    ), "Expecting 1 PCA plot for each combination of hyperparams"

    for i in range(n_combs):
        verify_PCA_plot(p_plots[i].figure, f"/DBSCAN_PCA_{n_clusters[i]}")

# def test_explore_text_columns(text_df):
#     """tests explore_text_columns function and its exception handling
#     Parameters
#     ----------
#     df : pandas.DataFrame
#         test text data
#     Returns
#     -------
#     None
#     """

#     currentdir = os.path.dirname(
#         os.path.abspath(inspect.getfile(inspect.currentframe()))
#     )

#     with raises(Exception):
#         eda.explore_text_columns(['test'])

#     with raises(Exception):
#         eda.explore_text_columns(text_df.drop['sms'])

#     with raises(Exception):
#         eda.explore_text_columns(text_df, 'sms')

#     with raises(Exception):
#         eda.explore_text_columns(text_df, ['some_col_name'])

#     result = eda.explore_text_columns(text_df)

#     assert(result[0]==['sms'])

#     assert(result[1]==[80.12, 61, 910, text_df['sms'][1084], 2, text_df['sms'][1924]])

#     verify_plot(result[2].figure, "hist_char_length", 0)

#     assert(result[3]==[15.49, 12, 171, text_df['sms'][1084]])

#     verify_plot(result[4].figure, "hist_word_count", 0)

#     verify_plot(result[5].figure, "word_cloud", 0)

#     verify_plot(result[6].figure, "stopword", 0)

#     verify_plot(result[7].figure, "non_stopword", 0)

#     verify_plot(result[8].figure, "bi_gram", 0)

#     verify_plot(result[9].figure, "polarity_scores", 0)

#     verify_plot(result[10].figure, "sentiment", 0)

#     verify_plot(result[11].figure, "subjectivity", 0)

#     verify_plot(result[12].figure, "entity", 0)

#     verify_plot(result[13].figure, "entity_token_1", 0)

#     verify_plot(result[14].figure, "entity_token_2", 0)

#     verify_plot(result[15].figure, "entity_token_3", 0)

#     verify_plot(result[16].figure, "pos_plot", 0)

@pytest.fixture
def numeric_df():
    """create a test dataset for testing functions for numeric columns

    Returns
    -------
    [pandas.DataFrame]
        a data set used for testing explore_numeric_columns
    """
    currentdir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    original_df = pd.read_csv(currentdir + "/data/menu_subset.csv")
    numeric_features = eda.get_numeric_columns(original_df)
    drop_features = []
    numeric_transformer = make_pipeline(SimpleImputer(), StandardScaler())
    preprocessor = make_column_transformer(
        (numeric_transformer, numeric_features), ("drop", drop_features)
    )
    transformed_df = pd.DataFrame(
        data=preprocessor.fit_transform(original_df), columns=numeric_features
    )

    return transformed_df



def test_explore_numeric_columns(numeric_df):
    # region test invalid inputs
    with raises(TypeError):
        eda.explore_numeric_columns(1)

    with raises(TypeError):
        eda.explore_numeric_columns(numeric_df, hist_cols=1)

    with raises(TypeError):
        eda.explore_numeric_columns(numeric_df, pairplot_cols=1)

    with raises(TypeError):
        eda.explore_numeric_columns(numeric_df, corr_method=1)

    with raises(ValueError):
        eda.explore_numeric_columns(numeric_df, corr_method='abc')
    # End region

    # Check if explore_numeric_columns with default hyper-parameters
    plots = eda.explore_numeric_columns(numeric_df)

    assert plots['hist'][0].encoding.x.shorthand == 'Calories', 'Calories should be mapped to the x axis'
    assert plots['hist'][0].encoding.y.shorthand == 'count()' , 'Y axis should contain count of records'
    assert plots['hist'][0].mark == 'bar' , 'The plots generated should have a Bar mark.'  # Test if Correct plots generated for histograms
    assert type(plots['pairplot']) == sns.axisgrid.PairGrid, 'Type of pairplot object should be seaborn.axisgrid.PairGrid'  # Test if Correct plot generated for pairplot
    assert type(plots['corr'].get_figure()) == matplotlib.figure.Figure, 'Type of pairplot object should be matplotlib.figure.Figure'  # Test if correct plot generated for correlation heatmap
    assert len(plots) == 3, 'Number of items in the plots dictionary should be 3'  # check if results dictionary has 3 items
    assert "hist" in plots.keys(), "There should be a key 'hist' in the plots dictionary"   # Check if results dictionary has the key values `hist`
    assert "pairplot" in plots.keys(), "There should be a key 'pairplot' in the plots dictionary" # Check if results dictionary has the key values `pairplot`
    assert "corr" in plots.keys(), "There should be a key 'corr' in the plots dictionary" # Check if results dictionary has the key values `corr`

    # Check if function works with user provided hyper-parameters
    plots_args = eda.explore_numeric_columns(numeric_df, hist_cols=['Calories','Cholesterol'], pairplot_cols=['Calories','Cholesterol'], corr_method="spearman")
    
    assert plots_args['hist'][0].encoding.x.shorthand == 'Calories', 'Calories should be mapped to the x axis'
    assert plots_args['hist'][1].encoding.x.shorthand == 'Cholesterol', 'Cholesterol should be mapped to the x axis'
    assert plots_args['hist'][0].encoding.y.shorthand == 'count()' , 'Y axis should contain count of records'
    assert plots_args['hist'][1].encoding.y.shorthand == 'count()' , 'Y axis should contain count of records'
    assert plots_args['hist'][0].mark == 'bar' , 'The plots generated should have a Bar mark.'  # Test if Correct plots generated for histograms
    assert type(plots_args['pairplot']) == sns.axisgrid.PairGrid, 'Type of pairplot object should be seaborn.axisgrid.PairGrid'  # Test if Correct plot generated for pairplot
    assert type(plots_args['corr'].get_figure()) == matplotlib.figure.Figure, 'Type of pairplot object should be matplotlib.figure.Figure'  # Test if correct plot generated for correlation heatmap
    assert len(plots_args) == 3, 'Number of items in the plots dictionary should be 3'  # check if results dictionary has 3 items
    assert "hist" in plots_args.keys(), "There should be a key 'hist' in the plots dictionary"   # Check if results dictionary has the key values `hist`
    assert "pairplot" in plots_args.keys(), "There should be a key 'pairplot' in the plots dictionary" # Check if results dictionary has the key values `pairplot`
    assert "corr" in plots_args.keys(), "There should be a key 'corr' in the plots dictionary" # Check if results dictionary has the key values `corr`

