import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcsConvert:
    def __init__(self, csv_path):
        """
        constructor

        Args:
            csv_path: path to file with procs data monitoring collected

        Raises:
            FileNotFoundError: csv file not found
            pandas.errors.EmptyDataError: csv file is empty
            pandas.errors.ParserError: csv file incorrectly formatted
        """
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)

        # convert epoch(s) to datetime object. unit='s' specifies the data unit
        self.df['timestamp'] = pd.to_datetime(self.df['epoch_timestamp'], unit='s')
        # set timestamp column as pandas index
        self.df.set_index('timestamp', inplace=True)
        # sort data
        self.df.sort_index(inplace=True)
        # drop previous epoch_timestamp column
        self.df.drop(columns=['epoch_timestamp'], inplace=True)

    def get_df(self):
        """
        return pandas timeSeries data frame

        Returns:
            pandas dataframe
        """
        return self.df


if __name__ == "__main__":
    try:
        converter = ProcsConvert('/home/simon/tmp/py_monitor_data_simon-ThinkPad-T480s_20251221_175312.csv')
        df_ts = converter.get_df()
        print("preview of the time series :")
        print(df_ts.head())
    except FileNotFoundError:
        logging.exception("csv file not found")
    except pd.errors.EmptyDataError:
        logging.exception("csv file is empty.")
    except pd.errors.ParserError:
        logging.exception("problem parsing csv file")
    except Exception as e:
        logging.exception(f"{e}")
