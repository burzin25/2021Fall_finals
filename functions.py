import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from colour import Color
from matplotlib.patches import Patch
from adjustText import adjust_text

def form_dataframe(filepath:str, sheet:str, header:int) -> pd.DataFrame:
    """
    Reads a excel file and returns the Dataframe

    :param str filepath: Path of excel file
    :param str sheet: Sheet name present in excel file
    :param int header: Line number to be considered as header
    :return: Dataframe containing the read data

    >>> form_dataframe('abc.xslx','Sheet1',0) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError...

    >>> form_dataframe('data/events_table.xlsx',1,0) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    ValueError...

    >>> form_dataframe('data/events_table.xlsx','Sheet1',0) # doctest: +ELLIPSIS
                                   Country  ...                                        Description
    ...

    >>> df = form_dataframe('data/WPP2019_MORT_F03_1_DEATHS_BOTH_SEXES.xlsx','ESTIMATES',16)

    """
    try:
        data = pd.read_excel(filepath, sheet_name=sheet, header=header)
    except FileNotFoundError:
        raise FileNotFoundError
    except Exception as e:
        raise e
    return data

def transform_dataframe(df: pd.DataFrame, countries:list, df_name:str, from_column:int, to_column:int, prefix:str, sep:str,
                        rename_flag:bool) -> pd.DataFrame:
    """
    Returns a transformed dataframe which contains a subset interested countries along with the corresponding region
    of each of the countries.

    :param pd.DataFrame df: Dataframe to transform
    :param list countries: List of countries
    :param str df_name: Name attribute of the Dataframe
    :param int from_column: Starting Index of Dataframe.columns for renaming columns
    :param int to_column: Ending Index of Dataframe.columns for renaming columns [to include]
    :param str prefix: Prefix of the renamed columns
    :param str sep: Separator for renamed columns
    :param bool rename_flag: Indicating whether to rename columns
    :return: Transformed DataFrame

    >>> transform_dataframe(form_dataframe('data/WPP2019_MORT_F03_1_DEATHS_BOTH_SEXES.xlsx','ESTIMATES',16), ['Iraq','Myanmar','Afghanistan','Libya','Germany','Venezuela'],'mortality_all_gender', 0, 0, '', ' ', False) # doctest: +ELLIPSIS
         Index    Variant      Country  ...  2010-2015 2015-2020          Region
    ...

    >>> transform_dataframe(form_dataframe('data/WPP2019_MORT_F04_1_DEATHS_BY_AGE_BOTH_SEXES.xlsx',\
                                       'ESTIMATES',\
                                       16),\
                                       ['Iraq','Myanmar','Afghanistan','Libya','Germany','Venezuela'],\
                                       'mortality_by_age',\
                                   from_column=7,to_column=-1,prefix='',sep=' ',rename_flag=True) # doctest: +ELLIPSIS
           Index    Variant  ... mortality_by_age 95+          Region
    ...

    >>> transform_dataframe(form_dataframe('data/WPP2019_MORT_F04_1_DEATHS_BY_AGE_BOTH_SEXES.xlsx',\
                                       'ESTIMATES',\
                                       16),\
                                       ['Iraq','Myanmar','Afghanistan','Libya','Germany','Venezuela'],\
                                       '_by_age',\
                                   from_column=7000.1,to_column=-1,prefix='',sep=' ',rename_flag=True) # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError:...

    """
    # countries_regex_expr='' countries_regex_expr=countries_regex_expr.join(val+'|' if i != len(countries)-1 else
    # val for i,val in enumerate(countries)) filter=df['Region, subregion, country or area *'].str.contains(
    # countries_regex_expr,regex=True)
    sub_region_filter = df['Type'] == 'Subregion'
    subregion_df = df[sub_region_filter]
    # df=df[filter]
    df = df.merge(subregion_df[['Region, subregion, country or area *', 'Country code']], left_on='Parent code',
                  right_on='Country code', suffixes=('_left', '_right'))
    df.drop('Country code_right', axis=1, inplace=True)
    rename_dict = {'Region, subregion, country or area *_left': 'Country',
                   'Region, subregion, country or area *_right': 'Region',
                   'Country code_left': 'Country code'}
    df.rename(columns=rename_dict, inplace=True)
    df.drop(columns=['Notes'], axis=1, inplace=True)
    df = df.drop_duplicates()
    df = df.infer_objects()
    df.name = df_name
    if rename_flag:
        if prefix != '':
            df = rename_columns(df, from_column, to_column, prefix, sep)
        else:
            df = rename_columns(df, from_column, to_column, df.name, sep)
    return df


def rename_columns(df:pd.DataFrame, from_column:int, to_column:int, prefix:str, sep:str) -> pd.DataFrame:
    """
    Renames the columns of a Dataframe

    :param pd.DataFrame df: Dataframe
    :param int from_column: Starting Index of Dataframe.columns for renaming columns
    :param int to_column: Ending Index of Dataframe.columns for renaming columns [to include]
    :param str prefix: Prefix of the renamed columns
    :param str sep: Separator for renamed columns
    :return: Renamed Dataframe

    >>> rename_columns(form_dataframe('data/WPP2019_MORT_F04_1_DEATHS_BY_AGE_BOTH_SEXES.xlsx',\
                                       'ESTIMATES',\
                                       16),\
                                   from_column=7,to_column=-1,prefix='ET_',sep=' ') # doctest: +ELLIPSIS
          Index    Variant  ... ET_ 90-94      95+
    ...

    """
    rename_dict = {}
    for column in df.columns[from_column:to_column]:
        rename_dict[column] = prefix + sep + column
    df.rename(columns=rename_dict, inplace=True)
    return df


def check_null_columns(df:pd.DataFrame) -> list:
    """
    Returns a list of columns containing any null values

    :param pd.DataFrame df: Dataframe
    :return: List of columns containing any null values

    >>> check_null_columns(form_dataframe('data/WPP2019_MORT_F04_1_DEATHS_BY_AGE_BOTH_SEXES.xlsx',\
                                       'ESTIMATES',\
                                       16)) # doctest: +ELLIPSIS
    [...

    """
    return df.columns[df.isna().any()].tolist()


def get_melted_dataframes(list_df:list) -> list:
    """
    Forms a list of melted dataframes

    :param list list_df: List of dataframes to be appended to the list
    :return: List of dataframes

    >>> get_melted_dataframes([\
    display_dataframe('data/WPP2019_MORT_F03_1_DEATHS_BOTH_SEXES.xlsx','ESTIMATES',\
    16,['Iraq','Myanmar','Afghanistan','Libya','Germany','Venezuela'],\
    'mortality_all_gender')]) # doctest: +ELLIPSIS
    Columns containing null values :...
    ...

    """
    ret_list = []
    for df in list_df:
        ret_list.append(df.melt(id_vars=[df.columns[2],
                                         df.columns[-1]],
                                value_vars=df.columns[6:-1],
                                var_name='Period',
                                value_name=df.name))
    return ret_list


def display_dataframe(filepath:str, sheet:str, header:str, countries:list, df_name:str, from_column:int=0, to_column:int=0, prefix:str='', sep:str=' ',
                      rename_flag:bool=False):
    """
    Loads the contents of the given excel file into a transformed and prints the columns containing null values

    :param str filepath: Path of excel file
    :param str sheet: Sheet Name
    :param int header: Line Number to be considered as header
    :param list countries: List of countries
    :param str df_name: Name attribute of the Dataframe
    :param int from_column: Starting Index of Dataframe.columns for renaming columns
    :param int to_column: Ending Index of Dataframe.columns for renaming columns [to include]
    :param str prefix: Prefix of the renamed columns
    :param str sep: Separator for renamed columns
    :param bool rename_flag: Indicating whether to rename columns
    :return: Transformed Dataframe

    >>> display_dataframe('data/WPP2019_MORT_F03_1_DEATHS_BOTH_SEXES.xlsx',\
    'ESTIMATES',16,['Iraq','Myanmar','Afghanistan','Libya','Germany','Venezuela']\
    ,'mortality_all_gender') # doctest: +ELLIPSIS
    Columns containing null values...
    ...

    """
    df = form_dataframe(filepath, sheet, header)
    df = transform_dataframe(df, countries, df_name, from_column, to_column, prefix, sep, rename_flag)
    print('Columns containing null values : {}'.format(check_null_columns(df)))
    return df


def get_finalized_df(stat_dataframes:list, stat2_dataframes:list) -> pd.DataFrame:
    """
    Merges the acquired list of dataframes using ['Country', 'Region', 'Period']
    :param list stat_dataframes: List of standard dataframes
    :param list stat2_dataframes: List of dataframes which contain renamed columns
    :return: Meged Dataframe
    """
    main_df = pd.DataFrame()
    for i, df in enumerate(stat_dataframes):
        if i < len(stat_dataframes) - 1:
            if i == 0:
                main_df = stat_dataframes[i].merge(stat_dataframes[i + 1], on=['Country', 'Region', 'Period'])
                continue
            main_df = main_df.merge(stat_dataframes[i + 1], on=['Country', 'Region', 'Period'])
    for df in stat2_dataframes:
        main_df = main_df.merge(df.iloc[:, np.r_[2, 6, -1, 7:len(df.columns) - 1]], on=['Country', 'Region', 'Period'])
    return main_df


def plot_barchart(consolidated_df:pd.DataFrame, country:str, x:str, y:str, title:str, xaxis_label:str="", yaxis_label:str="", title_font_size:str=20,
                  std_color:str='indigo', color_range:list=None) -> None:
    """
    Plots the barchart using the provided attributes and calculates the % change in the y attribute before and after each event

    :param pd.DataFrame consolidated_df: Dataframe to be used to plot the barchart
    :param str country: The country for which the plot needs to be created
    :param str x: Column of Dataframe to be used as X axis
    :param str y: Column of Dataframe to be used as Y axis
    :param str title: Title of the plot
    :param str xaxis_label: X-axis label
    :param str yaxis_label: Y-axis label
    :param str title_font_size: Font size of Title
    :param str std_color: Color of the non-event bars
    :param list color_range: Color range of the event bars
    :return: None
    """
    if color_range is None:
        color_range = ['orange', '#cd5700']
    consolidated_country = consolidated_df.loc[consolidated_df['Country'] == country]
    consolidated_country.reset_index(inplace=True, drop=True)
    periods, events, _ = fetch_events_metadata(consolidated_country)
    red = Color(color_range[0])
    colors = list(red.range_to(Color(color_range[1]), len(set(periods))))
    palette = [str(colors[periods.index(val)]) if val in set(periods) else std_color for val in
               consolidated_country['Period'].to_list()]
    g = sns.catplot(data=consolidated_country, x=x, y=y, kind='bar', height=10, aspect=1.5, palette=palette)
    # plt.annotate('Gadaffi takes power [1969]', xy=(3,148), xytext=(3,160),
    #              arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # plt.annotate('Libya\'s Independence [1951]', xy=(0,182), xytext=(0,195),
    #              arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # plt.annotate('Gadaffi Killed [2011]', xy=(12,160), xytext=(11.3,173),
    #              arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # g.set(ylim=(0, 200))
    # g.set_titles('Libya: Mortality from 1950-2020')
    plt.title(title, fontsize=title_font_size)
    g.set(xlabel=xaxis_label, ylabel=yaxis_label)
    cmap = dict(zip(consolidated_country[consolidated_country['Period'].isin(periods)].Event + ' [' +
                    consolidated_country[consolidated_country['Period'].isin(periods)].Year + ']',
                    colors))
    patches = [Patch(color=str(v), label=k) for k, v in cmap.items()]
    plt.legend(handles=patches, bbox_to_anchor=(1.04, 0.5), loc='center left', borderaxespad=0)
    plt.show()
    # change_dict={} ## might be useful to aggregate all the data of all countries in the future
    for period, event in zip(periods, events):
        ref_index = consolidated_country[consolidated_country['Period'] == period].index[0]
        pre_index, post_index = ref_index - 1, ref_index + 1
        if pre_index not in consolidated_country.index:
            # means that this pre index does not exists. In this case we will switch ref index to pre
            pre_index = ref_index
        if post_index not in consolidated_country.index:
            # means that this pre index does not exists. In this case we will switch ref index to pre
            post_index = ref_index
        # now calculate the percent change and assign to dict['Event']=val
        pre_val = consolidated_country.iloc[pre_index].mortality_all_gender
        post_val = consolidated_country.iloc[post_index].mortality_all_gender
        change = round(((post_val - pre_val) / pre_val) * 100, 2)
        print('The {} changed by {}% post {}'.format(yaxis_label, change, event))
        # change_dict[event]=change



def fetch_events_metadata(df:pd.DataFrame) -> (list,list,list):
    """
    Find periods and years where events have occurred from a dataframe

    :param df: Dataframe from which events need to listed
    :return: Returns 3 lists  containing the corresponding periods,events and years
    """
    stats_with_events = df[df['Event'].notna()]
    periods = stats_with_events['Period'].tolist()
    events = stats_with_events['Event'].tolist()
    years = stats_with_events['Year'].tolist()
    return periods, events, years


def plot_linechart(consolidated_df:pd.DataFrame, countries:list, x:str, y:str, value_vars:list=[], var_name:str='', regex_to_skip:str='all_gender',
                   title:str='', title_font_size:int=20, line_palette:list=None, melt_flag:bool=True, hue:str=''):
    """
    Plots the linechart from the given Dataframe and attibutes
    :param consolidated_df: Dataframe to be used to plot the linechart
    :param countries: List of countries for which the plot needs to be created
    :param x: Column of Dataframe to be used as X axis
    :param y: Column of Dataframe to be used as Y axis
    :param value_vars: columns to unpivot.
    :param var_name: Name of the variable column in melted dataframe
    :param regex_to_skip: Regex to skip in melting the column
    :param title: Title of the plot
    :param title_font_size: Font size of Title
    :param line_palette: Colors to be used to plot the linechart
    :param melt_flag: Indicates whether to melt the dataframe
    :param hue: Grouping variable to plot different countries
    :return: None
    """
    if line_palette is None:
        line_palette = ['red', 'green']
    countries_regex_expr = ''
    countries_regex_expr = countries_regex_expr.join(
        val + '|' if i != len(countries) - 1 else val for i, val in enumerate(countries))
    consolidated_country = consolidated_df.loc[
        consolidated_df['Country'].str.contains(countries_regex_expr, regex=True)]
    consolidated_country = consolidated_country.sort_values(by=['Period'], ascending=[True])
    consolidated_country.reset_index(inplace=True, drop=True)

    plot_df = consolidated_country
    if melt_flag:
        melted_country = consolidated_country.melt(id_vars=consolidated_country.columns[:6],
                                                   value_vars=value_vars,
                                                   var_name=var_name,
                                                   value_name=y)
        melted_country.sort_values(by=['Period'], ascending=[True], inplace=True)
        melted_country.reset_index(inplace=True, drop=True)
        melted_country = melted_country[~melted_country[var_name].str.contains(regex_to_skip)]
        plot_df = melted_country

    # display(plot_df)

    # now extract the period series, convert into list then into set
    period_series = plot_df['Period'].drop_duplicates().reset_index(drop=True)
    # print('printing series')
    # display(period_series)
    # print(period_series[period_series=='1945-1950'].index[0])

    # sns.relplot(data=consolidated_libya,x='Period',y='mortality_all_gender',kind='bar')
    # g=sns.catplot(data=melted_libya,x='Period',y='mortality',hue='mortality_type',kind='bar',height=10, aspect=1.5,)
    sns.set_theme()
    plt.figure(figsize=(20, 10), dpi=80)
    if melt_flag:
        hue = var_name
    g = sns.lineplot(data=plot_df,
                     x=x,
                     y=y,
                     hue=hue, palette=line_palette)
    ymin, ymax = g.get_ylim()
    periods, events, years = fetch_events_metadata(consolidated_country)
    plt.title(title, fontsize=title_font_size)
    # plt.annotate('Gadaffi takes power [1969]', xy=(3,90), xytext=(3.5,89.5),
    #             arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # plt.annotate('Libya\'s Independence [1951]', xy=(0,60), xytext=(0.5,59.5),
    #             arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # plt.annotate('Gadaffi Killed [2011]', xy=(11,90), xytext=(8.9,89.5),
    #             arrowprops=dict(facecolor='black', shrink=0.05, headwidth=20, width=7))
    # plt.legend(loc='best')
    plt.legend(bbox_to_anchor=(1.04, 0.5), loc='center left', borderaxespad=0)
    texts = []
    for period, event, year in zip(periods, events, years):
        xtick = period_series[period_series == period].index[0]
        # print(xtick,period)
        label_country=plot_df[plot_df['Event'] == event]['Country'].iloc[0]
        assign_label='('+label_country+') '+event + ' [' + year + ']'
        plt.axvline(x=xtick, color='orange', linestyle='-.', label=assign_label)
        texts.append(plt.text(xtick, (ymax + ymin) / 2, assign_label,
                              rotation=90, verticalalignment='center'))
    adjust_text(texts, only_move={'texts': 'y'})
    # plt.plot()
    plt.show()
    # plt.close()


def impute_regions(consolidated_df:pd.DataFrame) -> None:
    """
    Imputes the Region columns containing null values with the corresponding region
    :param consolidated_df: Dataframe
    :return: None
    """
    for country in consolidated_df['Country'].unique():
        filter = consolidated_df['Country'] == country
        regions = consolidated_df.loc[filter, 'Region']
        not_na = consolidated_df.loc[filter, 'Region'].notna()
        impute_value = regions[not_na].iloc[0]
        consolidated_df.loc[filter, 'Region'] = regions.fillna(impute_value)


def calculate_percent_change(consolidated_df:pd.DataFrame, countries:list,
                             level_two:list,
                             calc_attrs:list,
                             level_two_name:str='',
                             pre_name:str='Pre',
                             post_name:str='Post') -> pd.DataFrame:
    """
    Creates a dataframe which contains the percent change for given attributes
    :param consolidated_df: Dataframe
    :param countries: Countries for which the dataframe needs to be filtered
    :param level_two: List of names to be assigned to level two of the multi-index
    :param calc_attrs: Columns for which the percentage change needs to be calculated
    :param level_two_name: Level two header of the multi-index
    :param pre_name: Name of the column containing the pre values wrt reference
    :param post_name: Name of the column containing the post values wrt reference
    :return: Dataframe which contains the percent change for given attributes
    """
    list_of_dfs = []
    for country in countries:
        tmp_df = consolidated_df.loc[consolidated_df['Country'].str.contains(country)].copy()
        tmp_df = tmp_df.sort_values('Period')
        # display(tmp_df)
        periods, events, _ = fetch_events_metadata(tmp_df)
        tmp_dict = {'Period': [], 'Event': [], 'Pre': [], 'Post': []}
        # tmp_dict['Year']=[]
        set_of_periods = sorted(set(periods))
        list_of_tuples = []
        # periods=pd.Series(periods)
        for period in set_of_periods:
            # first get the list of events and year
            frame_of_period = tmp_df.loc[tmp_df['Period'] == period]
            spec_events = frame_of_period['Event'].tolist()
            years = frame_of_period['Year'].tolist()
            for event, year in zip(spec_events, years):
                # tmp_dict['Period'].append(period)
                # tmp_dict['Event'].append(event)
                # tmp_dict['Year'].append(year)
                pre_filter = tmp_df['Period'] < period
                post_filter = tmp_df['Period'] > period
                if events.index(spec_events[-1]) + 1 < len(events):
                    post_filter = (tmp_df['Period'] > period) & (
                            tmp_df['Period'] < periods[events.index(spec_events[-1]) + 1])
                if events.index(spec_events[0]) - 1 > 0:
                    pre_filter = (tmp_df['Period'] < period) & (
                            tmp_df['Period'] > periods[events.index(spec_events[0]) - 1])
                for group_type, col in zip(level_two, calc_attrs):
                    tmp_dict['Period'].append(period)
                    tmp_dict['Event'].append(event)
                    # tmp_dict['Year'].append(year)
                    tmp_dict['Pre'].append(round(tmp_df.loc[pre_filter, col].mean(), 2))
                    tmp_dict['Post'].append(round(tmp_df.loc[post_filter, col].mean(), 2))
                    list_of_tuples.append((country, group_type, year))
        change_df = pd.DataFrame.from_dict(tmp_dict)
        change_df['% Change'] = round(((change_df['Post'] - change_df['Pre']) / change_df['Pre']) * 100, 2)
        change_df.rename(columns={"Pre": pre_name, "Post": post_name}, inplace=True)
        index = pd.MultiIndex.from_tuples(list_of_tuples, names=['Country', level_two_name, 'Year'])
        change_df = change_df.set_index(index)
        change_df = change_df.sort_index()
        list_of_dfs.append(change_df)
    major_df = pd.concat(list_of_dfs)
    return major_df


def plot_correlation(consolidated_df:pd.DataFrame, country:str, x:str, y:str, hue:str, title:str, text_flag:bool=True, text_pos:list=None) -> None:
    """
    Plots the correlation plot of the given attributes
    :param consolidated_df: Dataframe
    :param country: Country for which plots needs to be created
    :param x: Column of Dataframe to be used as X axis
    :param y: Column of Dataframe to be used as Y axis
    :param hue: Grouping variable
    :param title: Title of the plot
    :param text_flag: Flag which indicates whether correlation coefficient needs to be displayed on the graph
    :param text_pos: The position of the correlation coefficient on the graph
    :return: None
    """
    # sns.scatterplot(data=df,
    #                 x=x,
    #                 y=y,hue=hue,s=100)
    if text_pos is None:
        text_pos = [0, 0]
    consolidated_country = consolidated_df.loc[consolidated_df['Country'].str.contains(country)]
    consolidated_country = consolidated_country.dropna(subset=consolidated_country.columns[6:])
    consolidated_country = consolidated_country.drop_duplicates(subset='Period', keep="first")
    consolidated_country.reset_index(inplace=True, drop=True)
    # periods,events,years=fetch_events_metadata(consolidated_country)
    # sns.color_palette("mako", as_cmap=True)
    g = sns.regplot(x=consolidated_country[x], y=consolidated_country[y])
    g.figure.set_size_inches(18.5, 10.5)
    # g.set(ylim=(-3000, 1000))
    # g.set_yticks(range(len(y)+1))
    sns.despine()
    # sns.lmplot(data=consolidated_country,x=x, y=y,hue='Period',palette="Set1",height=10,aspect=2,
    #            scatter=True,fit_reg=True)
    texts = []
    for i in consolidated_country[x].index:
        texts.append(plt.text(consolidated_country[x][i] + 0.2, consolidated_country[y][i] + 0.2,
                              consolidated_country['Period'][i]))
    if text_flag:
        plt.text(text_pos[0], text_pos[1],
                 "Correlation coefficient : {:.2f}".format(consolidated_country[y].corr(consolidated_country[x])),
                 horizontalalignment='left',
                 size='medium',
                 color='black',
                 weight='semibold')
    adjust_text(texts, only_move={'texts': 'y'})
    plt.title(title, fontsize=20)
    plt.show()
