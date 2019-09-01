import matplotlib.pyplot as plt
import seaborn as sns
import common as uc
import numpy as np
from sklearn.metrics import confusion_matrix

def get_dist_graph(data, column, bins = 1000, ignore_cancelled = True):
    fig, ax = plt.subplots(1, figsize=(15, 10))

    if ignore_cancelled:
        data = data[data['is_cancelled'] == 0]
    # Filtering out non visual data
    data_to_visualize = data[column][~data[column].isin([np.nan, np.inf, -np.inf])]

    # Calculating stats
    mean = data_to_visualize.mean()
    std = data_to_visualize.std()
    minimum = data_to_visualize.min()
    maximum = data_to_visualize.max()

    # Plotting
    sns.distplot(data_to_visualize, bins = bins, label = 'Mean : ' + str(round(mean, 2)))

    # Limits and mean line
    plt.xlim(max(mean - (3*std), minimum), min(mean + (3*std), maximum))
    plt.axvline(mean)
    plt.legend()

    #Title
    plt.title('Distribution Graph of ' + column)

    plt.show()

def get_pair_plot(data, column_list = None, hue = None, ignore_cancelled = True):
    if ignore_cancelled:
        data = data[data['is_cancelled'] == 0]
    # Filtering out non visual data
    if column_list != None:
        data_to_visualize = data[column_list][~data[column_list].isin([np.nan, np.inf, -np.inf]).any(1)]
        data_to_visualize = uc.remove_outliers_for_visualization(data=data_to_visualize, column_list=column_list,
                                                                 hue=hue)
    else:
        data_to_visualize = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    if hue == None:
        sns.pairplot(data_to_visualize)
    else:
        sns.pairplot(data_to_visualize, hue = hue)

    plt.show()

def get_corr_heat_map(data, ignore_cancelled = True):
    if ignore_cancelled:
        data = data[data['is_cancelled'] == 0].drop('is_cancelled', axis = 1)
    data_to_visualize = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]
    # Create Correlation df
    corr = data_to_visualize.corr()
    # Plot figsize
    fig, ax = plt.subplots(figsize=(15, 10)) 
    # Generate Color Map
    colormap = sns.diverging_palette(220, 10, as_cmap=True)
    # Generate Heat Map, allow annotations and place floats in map
    sns.heatmap(corr, cmap=colormap, annot=True, fmt=".2f")
    # Apply xticks
    plt.xticks(range(len(corr.columns)), corr.columns);
    # Apply yticks
    plt.yticks(range(len(corr.columns)), corr.columns)
    # show plot
    plt.show()

def get_class_balance(data):
    fig, ax = plt.subplots(figsize=(15, 10))
    plt.hist(data['was_rated'], rwidth = 2)
    plt.title('Class Counts')
    plt.show()

def get_line_plot(data, x, y):
    fig, ax = plt.subplots(figsize=(15, 10))
    sns.lineplot(data = data, x = x, y = y)
    plt.title(str(y) + ' Evolution')
    plt.show()

def get_box_plot_per_label(data, column_x, column_y, ignore_cancelled = True):
    fig, ax = plt.subplots(figsize=(15, 10))

    # Filtering out non visual data
    data_to_visualize = data[~data.isin([np.nan, np.inf, -np.inf]).any(1)]

    mean = data_to_visualize[column_y].mean()
    std = data_to_visualize[column_y].std()

    sns.boxplot(x = column_x, y = column_y, hue='was_rated', data=data_to_visualize)
    plt.ylim(mean - (2*std), mean + (7*std))

    plt.title(column_x + ' and ' + column_y + ' Box Plot')

    plt.show()

def draw_confusion_matrix(actuals, predicted, actual_labels, predicted_labels):
    fig, ax = plt.subplots(figsize=(15, 10))

    sns.heatmap(confusion_matrix(actuals, predicted), annot=True,
                ax=ax);  # annot=True to annotate cells

    # labels, title and ticks
    ax.set_xlabel('Predicted labels');
    ax.set_ylabel('True labels');
    ax.set_title('Confusion Matrix');
    ax.xaxis.set_ticklabels(actual_labels);
    ax.yaxis.set_ticklabels(predicted_labels)
    plt.show()