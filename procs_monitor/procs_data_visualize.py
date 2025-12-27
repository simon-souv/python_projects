import pandas as pd
from bokeh.plotting import figure, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.layouts import column
from bokeh.palettes import Spectral11
import itertools
from procs_data_transform import ProcsConvert


class ProcsVisualizer:
    def __init__(self, df: pd.DataFrame, title: str = "Analyse des Processus"):
        """
        constructor

        Args:
            df: pandas time series dataframe to plot
            title: title of the html document
        """
        self.df = df
        self.title = title
        # Palette de couleurs cyclique pour distinguer les PIDs
        self.colors = itertools.cycle(Spectral11)

    def generate_html(self, output_filename: str = "monitoring_report.html"):
        """
        generate html file containing the plots
        Args:
            output_filename: html filename

        Returns:

        """
        output_file(output_filename, title=self.title)

        # Création des deux graphiques
        p_cpu = self._create_line_plot("cpu_percent", "Usage CPU (%)", "blue")
        p_mem = self._create_line_plot("memory_rss_mb", "Usage Mémoire (MB)", "green")

        # Mise en page (un graphique au-dessus de l'autre)
        layout = column(p_cpu, p_mem, sizing_mode="stretch_width")

        save(layout)
        print(f"Rapport généré avec succès : {output_filename}")

    def _create_line_plot(self, column_name, y_axis_label, default_color):
        """

        Args:
            column_name:
            y_axis_label:
            default_color:

        Returns:

        """
        """Méthode interne pour construire un graphique multi-lignes par PID."""
        p = figure(
            x_axis_type="datetime",
            title=f"Évolution de {y_axis_label}",
            height=400,
            sizing_mode="stretch_width",
            toolbar_location="above"
        )

        # On groupe par PID pour tracer une ligne par processus
        for pid, group in self.df.groupby('pid'):
            # On récupère le nom du processus (le premier trouvé dans le groupe)
            proc_name = group['name'].iloc[0]

            source = ColumnDataSource(group)

            p.line(
                x='timestamp',
                y=column_name,
                source=source,
                legend_label=f"{proc_name} (PID: {pid})",
                color=next(self.colors),
                line_width=2,
                alpha=0.8
            )

        # Configuration de l'info-bulle au survol
        hover = HoverTool(tooltips=[
            ("Processus", "@name"),
            ("PID", "@pid"),
            ("Valeur", f"@{column_name}{{0.2f}}"),
            ("Temps", "@timestamp{%F %T}")
        ], formatters={'@timestamp': 'datetime'})

        p.add_tools(hover)
        p.legend.click_policy = "hide"  # Permet de cacher une ligne en cliquant sur la légende
        p.legend.label_text_font_size = "8pt"
        p.yaxis.axis_label = y_axis_label

        return p


# --- Exemple d'utilisation avec votre convertisseur ---
if __name__ == "__main__":
    # 1. On récupère la Time Series (via la classe précédente)
    converter = ProcsConvert('/home/simon/tmp/py_monitor_data_simon-ThinkPad-T480s_20251221_175312.csv')
    df_ts = converter.get_df()

    # 2. On génère le HTML
    viz = ProcsVisualizer(df_ts)
    viz.generate_html("mon_monitoring.html")
    pass