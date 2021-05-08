import plotly.express as px
import numpy as np
import pandas as pd
import sys


def column_group(indf, column_name, category_name):
    outdf = indf.groupby(['explanation_type', column_name])['Paper_number'].sum().reset_index()
    outdf.rename(columns={column_name: 'subcategory'}, inplace=True)
    outdf['category'] = category_name
    return outdf


df = px.data.gapminder().query("year == 2007")
df["world"] = "world" # in order to have a single root node
fig = px.treemap(df, path=['world', 'continent', 'country'], values='pop',
                  color='lifeExp', hover_data=['iso_alpha'],
                  color_continuous_scale='RdBu',
                  color_continuous_midpoint=np.average(df['lifeExp'], weights=df['pop']))

# Ante hoc
df_ah = pd.read_csv('ante-hoc.csv')
df_ah = df_ah.drop(['method', 'initials'], axis=1)
df_ah = df_ah.groupby(['scope', 'problem_type', 'explanation_type', 'input_type'])['Paper_number'].sum().reset_index()
df_ah['stage'] = 'Ante-hoc'

# Post hoc
df_ph = pd.read_csv('post-hoc.csv')
df_ph = df_ph.drop(['method', 'model_type', 'initials'], axis=1)
df_ph = df_ph.groupby(['scope', 'problem_type', 'explanation_type', 'input_type'])['Paper_number'].sum().reset_index()
df_ph['stage'] = 'Post-hoc'
df_tot = pd.concat([df_ah, df_ph])

new_df = column_group(df_tot, 'scope', 'Scope')
new_df = new_df.append(column_group(df_tot, 'problem_type', 'Problem type'), ignore_index=True)
new_df = new_df.append(column_group(df_tot, 'input_type', 'Input type'), ignore_index=True)
new_df = new_df.append(column_group(df_tot, 'stage', 'Stage'), ignore_index=True)

fig = px.treemap(new_df, path=['explanation_type', 'category', 'subcategory'], values='Paper_number'
                 )
fig.show()
