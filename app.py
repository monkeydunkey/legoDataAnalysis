import random
from bokeh.models import (HoverTool, FactorRange, Plot, LinearAxis, Grid,
                          Range1d)
from bokeh.io import show, output_notebook
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from bokeh.core.properties import value
from bokeh.palettes import d3
from flask import Flask, render_template, request
import pandas as pd
import os
from bokeh.resources import INLINE


app = Flask(__name__)

DATA_DIR = 'datasets'
combinedDatasets = None
datasets = {}
def loadDataSets():
    # Function to load the datasets and create a combined set to work on
    print 'loading datasets'
    for f in os.listdir(DATA_DIR):
        if f.endswith('.csv'):
            datasets[f.replace('.csv', '')] = pd.read_csv(os.path.join(DATA_DIR, f))

    setPartDf = pd.merge(pd.merge(pd.merge(pd.merge(datasets['sets'][['set_num',
                         'theme_id', 'year', 'num_parts']], datasets['inventories'
                         ][['set_num', 'id']], on='set_num'
                         ).rename(columns={'id': 'inventory_id'}),
                         datasets['inventory_parts'][['inventory_id', 'part_num',
                         'quantity', 'color_id']], on='inventory_id'), datasets['colors'
                         ], left_on='color_id', right_on='id').drop(['id', 'name'], 1),
                         datasets['parts'][['part_cat_id', 'part_num']], on='part_num')
    setPartDf = pd.merge(setPartDf, datasets['part_categories'],
                         left_on = 'part_cat_id',
                         right_on = 'id').drop(['id'], 1).rename(
                         columns = {'name': 'part_cat_name'})
    datasets['combinedDatasets'] = pd.merge(setPartDf, datasets['themes'],
                                            left_on = 'theme_id',
                                            right_on = 'id')
    print 'datasets loaded'

def plot_bar_stacked_chart(df, x_name, y_label, x_label, width, height,
                           useColsColr = False, createLegend = False,
                           createTooltip = True):
    # Function to create stacked bar charts
    stackCol = list(df.columns.values)
    colors = map(lambda x: '#' + x.lower(), df.columns.values) if useColsColr else d3['Category20'][20]
    legends = [value(x) for x in stackCol] if createLegend else None

    df = df.reset_index()
    tooltipVals = map(lambda x: (x.replace(',', ''), '@{'+ x +'}'), df.columns.values)
    df[x_name] = df[x_name].astype(str)
    source = ColumnDataSource(data=df)
    x_values = map(lambda x: str(x), df[x_name].values)
    plot = figure(x_range = x_values, plot_width=width, plot_height=height,
                  h_symmetry=False, v_symmetry=False, responsive=True,
                  tools="pan,wheel_zoom,box_zoom,reset",
                  toolbar_location="above",
                  min_border=0, outline_line_color="#666666")

    plot.vbar_stack(stackCol, x=x_name, width=0.5, color=colors, source=source,
                    legend = legends)
    xaxis, yaxis = LinearAxis(), LinearAxis()
    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#999999"
    plot.yaxis.axis_label = y_label
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = x_label
    plot.xaxis.major_label_orientation = 1
    if createTooltip:
        plot.add_tools(HoverTool(tooltips=tooltipVals))
    return plot

def plot_bar_chart(df, x_name, y_name, y_label, x_label, width, height):
    # Function to create bar charts
    df[x_name] = df[x_name].astype(str)
    plot = figure(x_range = df[x_name].values,
                  plot_width=width, plot_height=height, h_symmetry=False,
                  v_symmetry=False, tools="pan,wheel_zoom,box_zoom,reset",
                  min_border=0, toolbar_location="above",
                  responsive=True, outline_line_color="#666666")
    source = ColumnDataSource(df)
    plot.vbar(x=x_name,top=y_name, width=0.5, source = source)
    xaxis, yaxis = LinearAxis(), LinearAxis()
    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
    plot.toolbar.logo = None
    plot.min_border_top = 0
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#999999"
    plot.yaxis.axis_label = y_label
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = x_label
    plot.xaxis.major_label_orientation = 1
    plot.add_tools(HoverTool(tooltips=[(x_label, '@'+x_name), (y_label, '@'+y_name)]))
    return plot

def getTopNEntries(df, topN, x_name, y_name, final_agg = 'mean'):
    #Filter and get the top N entry in a dataframe
    if df.shape[0] <= topN:
        return df
    lengthN = True
    df_temp = df.copy().reset_index(drop=True)
    if final_agg != 'mean':
        lengthN = False
        df_temp.loc[topN] = ['others', df_temp[topN:][y_name].agg('sum')]
    return df_temp.loc[:(topN - 1) if lengthN else topN].copy()

def plot_agg_bar(df_set, x_name, y_name, width=600, height=300,
                       year_range = (1950, 2017), orderBy = False,
                       orderType = True,
                       TopX = None, X_label_name = None, y_label_name = None,
                       agg = 'mean'):
    # Function to create required aggregations and then create bar plots
    X_label_name = x_name if X_label_name is None else X_label_name
    y_label_name = y_name if y_label_name is None else y_label_name
    data = pd.DataFrame(df_set.groupby(x_name).agg({y_name: agg})).reset_index()
    if orderBy:
        data.sort_values(y_name, inplace=True, ascending = orderType)
    if TopX is not None:
        data = getTopNEntries(data, TopX, x_name, y_name, agg)
    return plot_bar_chart(data, x_name, y_name, y_label_name, X_label_name, width, height)


def combineFilter(datasets, year_range):
    # function to apply the year filter
    return datasets['combinedDatasets'][(datasets['combinedDatasets'
           ].year >= year_range[0]) & (datasets['combinedDatasets'].year <= year_range[1])]

@app.route("/")
def chart():
    startYear = request.args.get("startyear")
    endYear = request.args.get("endyear")
    startYear = int(startYear) if startYear is not None else 1950
    endYear = int(endYear) if endYear is not None else 2017
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()
    combineddf = combineFilter(datasets, (startYear, endYear))
    print combineddf.year.min(), combineddf.year.max(), startYear, endYear
    #Average Part used over year
    script_part_year, div_part_year = components(plot_agg_bar(combineddf, 'year', 'num_parts',
                                                              X_label_name = "Year",
                                                              y_label_name = 'Avg number of Parts',
                                                              agg = 'mean'))
    #Average Part used by Theme
    script_part_theme, div_part_theme = components(plot_agg_bar(combineddf, 'name', 'num_parts',
                                                                X_label_name = "Theme Name",
                                                                y_label_name = 'Average number of parts',
                                                                orderBy = True,
                                                                orderType = False,
                                                                TopX = 50,
                                                                width=600, height=400,
                                                                agg = 'mean'))
    #Number of parts by part category
    script_part_type, div_part_type = components(plot_agg_bar(combineddf, 'part_cat_name', 'part_num',
                                                                X_label_name = "Part Type",
                                                                y_label_name = 'Part Count',
                                                                agg = 'count', width=600, height=600))


    #Part type composition of theme
    TopNTheme = 50
    TopNPartType = 20
    topThemes = combineddf.groupby('name')['id'].count().reset_index().rename(columns = {'id': 'count'}).sort_values(by='count', ascending=False)[:TopNTheme]
    topPartType = combineddf.groupby('part_cat_name')['id'].count().reset_index().rename(columns = {'id': 'count'}).sort_values(by='count', ascending=False)[:TopNPartType]
    ThemePartTypeCount = combineddf[(combineddf.name.isin(topThemes.name)) & (combineddf.part_cat_name.isin(topPartType.part_cat_name))]
    ThemePartTypeCount = ThemePartTypeCount.groupby(['name', 'part_cat_name'])['quantity'].sum().reset_index()
    ThemePartTypeCount_pivot = ThemePartTypeCount.pivot(index = 'name', values = 'quantity', columns = 'part_cat_name').fillna(0)
    p = plot_bar_stacked_chart(ThemePartTypeCount_pivot, 'name', 'Colors', 'Year', 600, 600, createLegend=True)
    p.legend.label_text_font_size = "5pt"
    p.legend.glyph_height= 5
    p.legend.glyph_width= 5
    p.legend.label_height= 5
    p.legend.label_width= 5
    script_partCat_theme, div_partCat_theme = components(p)
    #color composition over years
    TopNColor = 50
    topColors = combineddf.groupby('rgb')['quantity'].sum().reset_index().sort_values(by='quantity', ascending=False).reset_index(drop=True)[:TopNColor]
    groupedData = combineddf[combineddf.rgb.isin(topColors.rgb)][['year', 'rgb', 'quantity']].groupby(['year', 'rgb']).quantity.sum().reset_index()
    pivot_data = groupedData.pivot(index = 'year', values = 'quantity', columns = 'rgb').fillna(0)
    p = plot_bar_stacked_chart(pivot_data, 'year', 'Colors', 'Year', 800, 300, useColsColr = True, createTooltip = False)
    script_color_year, div_color_year = components(p)


    return render_template("chart.html", div_part_year=div_part_year,
                            script_part_year=script_part_year,
                            div_part_theme=div_part_theme,
                            script_part_theme=script_part_theme,
                            script_part_type=script_part_type,
                            div_part_type=div_part_type,
                            script_partCat_theme=script_partCat_theme,
                            div_partCat_theme=div_partCat_theme,
                            script_color_year=script_color_year,
                            div_color_year=div_color_year,
                            js_resources=js_resources,
                            css_resources=css_resources
                            )

if __name__ == "__main__":
    loadDataSets()
    app.run(debug=True)
