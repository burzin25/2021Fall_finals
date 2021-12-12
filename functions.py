import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from colour import Color
from matplotlib.patches import Patch
from adjustText import adjust_text


def transform_dataframe(df: pd.DataFrame, countries, df_name, from_column, to_column, prefix, sep,
                        rename_flag) -> pd.DataFrame:
    """
    Returns a transformed dataframe which contains a subset interested countries along with the corresponding region
    of each of the countries.
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


def rename_columns(df, from_column, to_column, prefix, sep):
    rename_dict = {}
    for column in df.columns[from_column:to_column]:
        rename_dict[column] = prefix + sep + column
    df.rename(columns=rename_dict, inplace=True)
    return df


def form_dataframe(filepath, sheet, header):
    data = pd.read_excel(filepath, sheet_name=sheet, header=header)
    # display(data.head().append(data.tail()))
    return data


def check_null_columns(df):
    return df.columns[df.isna().any()].tolist()


def get_melted_dataframes(list_df):
    ret_list = []
    for df in list_df:
        ret_list.append(df.melt(id_vars=[df.columns[2],
                                         df.columns[-1]],
                                value_vars=df.columns[6:-1],
                                var_name='Period',
                                value_name=df.name))
    return ret_list


def display_dataframe(filepath, sheet, header, countries, df_name, from_column=0, to_column=0, prefix='', sep=' ',
                      rename_flag=False):
    df = form_dataframe(filepath, sheet, header)
    df = transform_dataframe(df, countries, df_name, from_column, to_column, prefix, sep, rename_flag)
    print('Columns containing null values : {}'.format(check_null_columns(df)))
    return df


def get_finalized_df(stat_dataframes, stat2_dataframes):
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


def plot_barchart(consolidated_df, country, x, y, title, xaxis_label="", yaxis_label="", title_font_size=20,
                  std_color='indigo', color_range=None):
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
    # create color map with colors and df.names
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


# find periods where events have occured, so as to highlight in the graph:
def fetch_events_metadata(df):
    stats_with_events = df[df['Event'].notna()]
    periods = stats_with_events['Period'].tolist()
    events = stats_with_events['Event'].tolist()
    years = stats_with_events['Year'].tolist()
    return periods, events, years


def plot_linechart(consolidated_df, countries, x, y, value_vars='', var_name='', regex_to_skip='all_gender',
                   title='', title_font_size=20, line_palette=None, melt_flag=True, hue=''):
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


def impute_regions(consolidated_df):
    for country in consolidated_df['Country'].unique():
        filter = consolidated_df['Country'] == country
        regions = consolidated_df.loc[filter, 'Region']
        not_na = consolidated_df.loc[filter, 'Region'].notna()
        impute_value = regions[not_na].iloc[0]
        consolidated_df.loc[filter, 'Region'] = regions.fillna(impute_value)


def calculate_percent_change(consolidated_df, countries,
                             level_two,
                             calc_attrs,
                             level_two_name='',
                             pre_name='Pre',
                             post_name='Post'):
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


def plot_correlation(consolidated_df, country, x, y, hue, title, text_flag=True, text_pos=None):
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
