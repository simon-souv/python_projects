import logging
import pandas as pd
from bokeh.plotting import figure, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column
from bokeh.palettes import Category20
import itertools
from procs_data_transform import ProcsConvert

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcsVisualizer:
    def __init__(self, df: pd.DataFrame, title: str = "Analyse des Processus"):
        """

        Args:
            df:
            title:
        """
        self.df = df.copy()
        self.title = title
        # Move timestamp from index to column to prevent Bokeh/Pandas conflicts
        if self.df.index.name == 'timestamp':
            self.df.reset_index(inplace=True)
        # Ensure timestamp is datetime objects
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def generate_html(self, output_filename: str = "monitoring_report.html"):
        """

        Args:
            output_filename:

        Returns:

        """
        output_file(output_filename, title=self.title)

        # Filter PIDs, remove those with cpu_usage = 0.0 during the whole observation
        pid_max_cpu : pd.Series = self.df.groupby('pid')['cpu_percent'].max()  # pd.Series index = pid
        active_pids : list = pid_max_cpu[pid_max_cpu > 0].sort_values(ascending=False).index.tolist()

        if not active_pids:
            logging.info("No active processes (CPU > 0) found.")
            return

        # COLOR MAPPING: Use Category20 for better visibility on white backgrounds
        # We cycle through colors so every PID gets a distinct, visible color
        colors = itertools.cycle(Category20[20])
        color_map = {pid: next(colors) for pid in active_pids}

        # CREATE PLOTS
        p_cpu = self._create_line_plot(active_pids, color_map, "cpu_percent", "Usage CPU (%)")
        p_mem = self._create_line_plot(active_pids, color_map, "memory_rss_mb", "Usage Mémoire (MB)")

        layout = column(p_cpu, p_mem, sizing_mode="stretch_width")
        save(layout)
        print(f"Report generated: {output_filename} ({len(active_pids)} active processes)")

    def _create_line_plot(self, pids_to_plot, color_map, column_name, y_axis_label):
        """

        Args:
            pids_to_plot:
            color_map:
            column_name:
            y_axis_label:

        Returns:

        """
        p = figure(
            title=f"Evolution {y_axis_label}",
            x_axis_type='datetime',
            height=450,
            sizing_mode="stretch_width"
        )

        for pid in pids_to_plot:
            group = self.df[self.df['pid'] == pid]
            proc_name = group['name'].iloc[0]

            source = ColumnDataSource(group)
            p.line(
                x='timestamp',
                y=column_name,
                source=source,
                legend_label=f"{proc_name} (PID: {pid})",
                color=color_map[pid],
                line_width=2,
                alpha=0.9  # Increased alpha for better visibility
            )

        # Tools and Legend
        hover = HoverTool(tooltips=[
            ("Process", "@name"),
            ("PID", "@pid"),
            ("Value", f"@{column_name}{{0.2f}}"),
            ("Time", "@timestamp{%F %T}")
        ], formatters={'@timestamp': 'datetime'})

        p.add_tools(hover)
        p.legend.click_policy = "hide"
        p.legend.label_text_font_size = "8pt"
        p.yaxis.axis_label = y_axis_label

        # Hide legend if it becomes too cluttered
        if len(pids_to_plot) > 20:
            p.legend.visible = False

        return p


if __name__ == "__main__":
    csv_file = "/home/simon/tmp/py_monitor_data_simon-ThinkPad-T480s_20260102_150919.csv"
    converter = ProcsConvert(csv_file)
    df_ts = converter.get_df()

    viz = ProcsVisualizer(df_ts)
    viz.generate_html("mon_monitoring.html")