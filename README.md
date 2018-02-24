# Lego Data Analysis

This repo contains an exploratory data analysis of Lego Data set obtained from [Kaggle](https://www.kaggle.com/rtatman/lego-database).

## File breakdown
1. app.py: Flask web server code which is used to serve data to visualization layer
2. Data Analysis.ipynb: Jupyter notebook containing the exploratory data analysis and the machine learning model experiments

## To run:
1. Install all the dependencies mentioned in `requirements.txt` 
2. start the webservice by typing `python app.py`
3. The Visualizations should be present at `http://127.0.0.1:5000/`
4. On top of page at `http://127.0.0.1:5000/`, years can be entered for the required year range. By default the date range is 1950-2017


The visualizations related to Part type, Theme, Color, do not show all the data but rather in show the top 20 or 50 items these fields have very high cardinality which causes the charts to break and also render very slow 
