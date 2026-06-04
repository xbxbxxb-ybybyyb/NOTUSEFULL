from alpha_invest.datasets.dataset_manager import PurgedGroupTimeSeriesSplit
from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

def plot_cv_indices(cv, X, y, group, ax, n_splits, lw=10):
    """Create a sample plot for indices of a cross-validation object."""
    cmap_cv = plt.cm.coolwarm

    jet = plt.cm.get_cmap('jet', 256)
    seq = np.linspace(0, 1, 256)
    _ = np.random.shuffle(seq)  # inplace
    cmap_data = ListedColormap(jet(seq))

    # Generate the training/testing visualizations for each CV split
    for ii, (tr, tt) in enumerate(cv.split(X=X, y=y, groups=group)):
        # Fill in indices with the training/test groups
        indices = np.array([np.nan] * len(X))
        indices[tt] = 1
        indices[tr] = 0

        # Visualize the results
        ax.scatter(range(len(indices)), [ii + .5] * len(indices),
                   c=indices, marker='_', lw=lw, cmap=cmap_cv,
                   vmin=-.2, vmax=1.2)

    # Plot the data classes and groups at the end
    ax.scatter(range(len(X)), [ii + 1.5] * len(X),
               c=np.reshape(y / 255, -1), marker='_', lw=lw, cmap=plt.cm.Set3)

    ax.scatter(range(len(X)), [ii + 2.5] * len(X),
               c=group, marker='_', lw=lw, cmap=cmap_data)

    # Formatting
    yticklabels = list(range(n_splits)) + ['target', 'day']
    ax.set(yticks=np.arange(n_splits + 2) + .5, yticklabels=yticklabels,
           xlabel='Sample index', ylabel="CV iteration",
           ylim=[n_splits + 2.2, -.2], xlim=[0, len(y)])
    ax.set_title('{}'.format(type(cv).__name__), fontsize=15)
    return ax

def plot_cv(factor_data, label_data):
    fig, ax = plt.subplots()

    n_groups = len(set(factor_data['mddate']))
    n_samples = len(factor_data)

    groups = factor_data['mddate'].astype(int).rank(method='dense').values

    cv = PurgedGroupTimeSeriesSplit(
        n_splits=5,
        max_train_group_size=8,
        group_gap=0,
        max_test_group_size=2
    )
    X_train = factor_data.iloc[:, 3:].values
    y_labels = label_data.iloc[:, 3].values
    print("plot_cv, X_train:", X_train.shape, "y_labels:", y_labels.shape)

    plot_cv_indices(cv, X_train, y_labels, groups, ax, 5, lw=20);

if __name__=="__main__":
    from alpha_invest.datasets.dataset_loader import DatasetLoader
    data_loader = DatasetLoader()
    factor_data, label_data = data_loader.load_factor_data(classify_or_not=True, mock_data_flag=True)
    plot_cv(factor_data, label_data)
    plt.show()