import logging
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import itertools
from procs_data_transform import ProcsConvert

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcsVisualizer:
    def __init__(self, df: pd.DataFrame, title: str = "Analyse des Processus"):
        """
        Initialize the visualizer with process monitoring data.
        
        Args:
            df: DataFrame containing process monitoring data
            title: Title for the visualization
        """
        self.df = df.copy()
        self.title = title
        # Move timestamp from index to column if needed
        if self.df.index.name == 'timestamp':
            self.df.reset_index(inplace=True)
        # Ensure timestamp is datetime objects
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])

    def generate_html(self, output_filename: str = "monitoring_report.html"):
        """
        Generate an interactive HTML report with CPU and memory usage plots.
        
        Args:
            output_filename: Path to save the HTML report

        Returns:
            None
        """
        # Filter PIDs, remove those with cpu_usage = 0.0 during the whole observation
        pid_max_cpu = self.df.groupby('pid')['cpu_percent'].max()
        active_pids = pid_max_cpu[pid_max_cpu > 0].sort_values(ascending=False).index.tolist()

        if not active_pids:
            logging.info("No active processes (CPU > 0) found.")
            return

        # COLOR MAPPING: Use Plotly's default color sequence for distinct colors
        colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
            '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
            '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
        ]
        color_cycle = itertools.cycle(colors)
        color_map = {pid: next(color_cycle) for pid in active_pids}

        # CREATE SUBPLOTS
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Evolution Usage CPU (%)", "Evolution Usage Mémoire (MB)"),
            vertical_spacing=0.12,
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]]
        )

        # Add CPU traces
        for pid in active_pids:
            group = self.df[self.df['pid'] == pid]
            proc_name = group['name'].iloc[0]
            
            fig.add_trace(
                go.Scatter(
                    x=group['timestamp'],
                    y=group['cpu_percent'],
                    mode='lines',
                    name=f"{proc_name} (PID: {pid})",
                    line=dict(color=color_map[pid], width=2),
                    legendgroup=str(pid),
                    hovertemplate=(
                        f"<b>{proc_name}</b><br>" +
                        "PID: %{customdata[0]}<br>" +
                        "CPU: %{y:.2f}%<br>" +
                        "Time: %{x|%Y-%m-%d %H:%M:%S}<br>" +
                        "<extra></extra>"
                    ),
                    customdata=group[['pid']].values
                ),
                row=1, col=1
            )

        # Add Memory traces
        for pid in active_pids:
            group = self.df[self.df['pid'] == pid]
            proc_name = group['name'].iloc[0]
            
            fig.add_trace(
                go.Scatter(
                    x=group['timestamp'],
                    y=group['memory_rss_mb'],
                    mode='lines',
                    name=f"{proc_name} (PID: {pid})",
                    line=dict(color=color_map[pid], width=2),
                    legendgroup=str(pid),
                    showlegend=False,  # Don't duplicate legend
                    hovertemplate=(
                        f"<b>{proc_name}</b><br>" +
                        "PID: %{customdata[0]}<br>" +
                        "Memory: %{y:.2f} MB<br>" +
                        "Time: %{x|%Y-%m-%d %H:%M:%S}<br>" +
                        "<extra></extra>"
                    ),
                    customdata=group[['pid']].values
                ),
                row=2, col=1
            )

        # Update layout
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="CPU Usage (%)", row=1, col=1)
        fig.update_yaxes(title_text="Memory Usage (MB)", row=2, col=1)

        fig.update_layout(
            title=dict(text=self.title, x=0.5, xanchor='center'),
            height=900,
            hovermode='closest',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                font=dict(size=9)
            ),
            template="plotly_white"
        )

        # Hide legend if too many processes
        if len(active_pids) > 20:
            fig.update_layout(showlegend=False)

        # Save to HTML
        fig.write_html(output_filename, config={'responsive': True})
        print(f"Report generated: {output_filename} ({len(active_pids)} active processes)")


if __name__ == "__main__":
    csv_file = "/home/simon/tmp/py_monitor_data_simon-ThinkPad-T480s_20260102_150919.csv"
    converter = ProcsConvert(csv_file)
    df_ts = converter.get_df()

    viz = ProcsVisualizer(df_ts)
    viz.generate_html("mon_monitoring.html")