from results.model.Line import Line
import pandas as pd
import parameters.Constants as Constants
import os
import util.DrawUtil as DrawUtil
import util.ListUtil as ListUtil


def draw_group_states(group_analysis):
    for sf in group_analysis:
        sf_group_analysis = group_analysis[sf]
        for analysis in sf_group_analysis:
            group_id = getattr(analysis, 'id')
            attempts = getattr(analysis, 'attempts')
            idles = getattr(analysis, 'idles')
            successes = getattr(analysis, 'successes')
            fails = getattr(analysis, 'fails')

            draw_file_name = 'SF:{SF}-{GROUP_ID}'.format(SF=sf, GROUP_ID=group_id)
            draw_path = os.path.abspath(os.path.join(Constants.LOG_FILE_DIR, draw_file_name))

            __save_three_line_plot(draw_path, attempts, idles, successes, fails)


def draw_super_group_states(group_analysis):
    for sf in group_analysis:
        draw_file_name = 'SF:{SF}'.format(SF=sf)
        draw_path = os.path.abspath(os.path.join(Constants.LOG_FILE_DIR, draw_file_name))
        sf_group_analysis = group_analysis[sf]

        attempts = []
        idles = []
        successes = []
        fails = []
        for analysis in sf_group_analysis:
            attempts = getattr(analysis, 'attempts')
            if len(idles) == 0:
                idles = ListUtil.zero_list(len(attempts))
                successes = ListUtil.zero_list(len(attempts))
                fails = ListUtil.zero_list(len(attempts))

            idles = ListUtil.sum_list(idles, getattr(analysis, 'idles'))
            successes = ListUtil.sum_list(successes, getattr(analysis, 'successes'))
            fails = ListUtil.sum_list(fails, getattr(analysis, 'fails'))

        __save_three_line_plot(draw_path, attempts, idles, successes, fails)


def draw_total_all_transmission_states(group_analysis):
    attempts = []
    idles = []
    successes = []
    fails = []

    draw_file_name = 'SF:ALL'
    draw_path = os.path.abspath(os.path.join(Constants.LOG_FILE_DIR, draw_file_name))

    for sf in group_analysis:
        sf_group_analysis = group_analysis[sf]
        for analysis in sf_group_analysis:
            attempts = getattr(analysis, 'attempts')
            if len(idles) == 0:
                idles = ListUtil.zero_list(len(attempts))
                successes = ListUtil.zero_list(len(attempts))
                fails = ListUtil.zero_list(len(attempts))

            idles = ListUtil.sum_list(idles, getattr(analysis, 'idles'))
            successes = ListUtil.sum_list(successes, getattr(analysis, 'successes'))
            fails = ListUtil.sum_list(fails, getattr(analysis, 'fails'))

    __save_three_line_plot(draw_path, attempts, idles, successes, fails)


def __save_three_line_plot(draw_path, attempts, idles, successes, fails):
    idle_df = pd.DataFrame({'attempts': attempts, 'idles': idles})
    success_df = pd.DataFrame({'attempts': attempts, 'successes': successes})
    fail_df = pd.DataFrame({'attempts': attempts, 'fails': fails})

    idle_line = Line(x_id='attempts', y_id='idles', data_frame=idle_df, color='b', width=2)
    success_line = Line(x_id='attempts', y_id='successes', data_frame=success_df, color='g', width=2)
    fail_line = Line(x_id='attempts', y_id='fails', data_frame=fail_df, color='r', width=2)

    plot = DrawUtil.create_plot(title='Transmission States', xlabel='Iteration', ylabel='Device Count')
    DrawUtil.add_line_to_plot(plot, idle_line)
    DrawUtil.add_line_to_plot(plot, success_line)
    DrawUtil.add_line_to_plot(plot, fail_line)
    DrawUtil.write_plot_to_file(plot, draw_path)
    DrawUtil.clear_plot(plot)
