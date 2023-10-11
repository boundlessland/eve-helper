import json

from pyecharts import options as opts
from pyecharts.charts import Tree


def treeChart(data: dict):
    c = (
        Tree()
            .add("", [data], collapse_interval=2)
            .set_global_opts(title_opts=opts.TitleOpts(title="Tree-左右方向"))
            .render("tree_left_right.html")
    )
    return


data = {'name': 30308, 'activityID': 11, 'quantity': 400, 'children': [
    {'name': 4247, 'activityID': 1, 'quantity': 15,
     'children': [{'name': 9848, 'activityID': -1, 'quantity': 1, 'children': []},
                   {'name': 44, 'activityID': -1, 'quantity': 4, 'children': []},
                   {'name': 3689, 'activityID': -1, 'quantity': 4, 'children': []},
                   {'name': 9832, 'activityID': -1, 'quantity': 9, 'children': []},
                   {'name': 16275, 'activityID': -1, 'quantity': 20, 'children': []},
                   {'name': 3683, 'activityID': -1, 'quantity': 22, 'children': []},
                   {'name': 16272, 'activityID': -1, 'quantity': 170, 'children': []},
                   {'name': 16273, 'activityID': -1, 'quantity': 350, 'children': []},
                   {'name': 16274, 'activityID': -1, 'quantity': 450, 'children': []}]},
    {'name': 39, 'activityID': -1, 'quantity': 75, 'children': []},
    {'name': 30373, 'activityID': -1, 'quantity': 300, 'children': []},
    {'name': 30375, 'activityID': -1, 'quantity': 300, 'children': []}]}

treeChart(data)