from typing import List
import numpy as np
import pandas as pd
from scipy import stats
import geopandas as gpd
from shapely.geometry import Point


class Clusterizer:
    def __init__(self):
        self.config = {'min_xval': 55.55, 'max_xval': 55.95, 'min_yval': 37.3, 'max_yval': 37.9, 'x_ngroups': 3, 'y_ngroups': 3}
        # get x-axis grid
        self.x_intervals = self.split_on_intervals(
            self.config['min_xval'], self.config['max_xval'], self.config['x_ngroups']
        )
        # get y-axis grid
        self.y_intervals = self.split_on_intervals(
            self.config['min_yval'], self.config['max_yval'], self.config['y_ngroups']
        )
        # get 2-d grid
        self.groups = self.create_groups(self.x_intervals, self.y_intervals)
        self.n_groups = len(self.groups)

    def split_on_intervals(self, min_val, max_val, n):
        # Делит отрезок на равные интервалы
        step = (max_val - min_val) / n
        intervals = [min_val + (step * x) for x in range(n + 1)]
        return intervals

    @classmethod
    def create_groups(cls, x_intervals, y_intervals):
        #Создает регионы для поля
        groups = {}
        x_intervals = np.concatenate([[-np.inf], x_intervals, [np.inf]])
        y_intervals = np.concatenate([[-np.inf], y_intervals, [np.inf]])

        for x_i in range(len(x_intervals) - 1):
            for y_i in range(len(y_intervals) - 1):
                groups[
                    f'x : {x_intervals[x_i]} - {x_intervals[x_i + 1]} | y : {y_intervals[y_i]} - {y_intervals[y_i + 1]}'] = 0

        return groups

    @classmethod
    def sort_on_groups(cls, x_vals, y_vals, x_intervals, y_intervals, groups, only_vals=False):
        # Сортирует точки по регионам
        for x, y in zip(x_vals, y_vals):
            for x_i in range(len(x_intervals) - 1):
                for y_i in range(len(y_intervals) - 1):
                    if ((x_intervals[x_i] <= x < x_intervals[x_i + 1]) and (y_intervals[y_i] <= y < y_intervals[y_i + 1])):
                        groups[
                            f'x : {x_intervals[x_i]} - {x_intervals[x_i + 1]} | y : {y_intervals[y_i]} - {y_intervals[y_i + 1]}'] += 1

        if only_vals:
            return list(groups.values())

        return groups

    def assign_clusters(self, row):
        points = np.array([[float(x['lat']), float(x['lon'])] for x in row])
        group_values = self.sort_on_groups(
            points[:, 0], points[:, 1], self.x_intervals, self.y_intervals, self.groups.copy(), only_vals=True
        )

        return group_values

    def clusters_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        cluster_columns = [f'cluster_{i}' for i in range(self.n_groups)]

        df_clusters = df.apply(lambda row: self.assign_clusters(row['points']), axis=1)
        df_clusters = pd.DataFrame(df_clusters.tolist(), columns=cluster_columns)

        return pd.concat([df, df_clusters], axis=1)


class DataPreprocessor:
    def __init__(self, clusterizer):
        self.moscow_centre_coordinates = [55.751244, 37.618423]
        self.clusterizer = clusterizer

    @staticmethod
    def calculate_distances(row, centre_coordinates: List[float]) -> List[float]:
        distances = [
            float(gpd.GeoSeries(Point(float(point['lat']), float(point['lon']))) \
                  .distance(Point(centre_coordinates))) for point in row
        ]
        return distances

    @staticmethod
    def inner_cluster_stats(df: pd.DataFrame, cluster_centre=None) -> pd.DataFrame:
        """
        Accepts DataFrame with geo points and returns statistics of this cluster of points
        :param df: pd.DataFrame with two columns: `lat` and `lon`
        :param cluster_centre: centre of the geo cluster that allows for more precise feature engineering
        :return: pd.DataFrame with statistics
        """
        # Ensure the columns are of type float
        df['lat'] = df['lat'].astype(float)
        df['lon'] = df['lon'].astype(float)

        # Ensure we always have a cluster centre
        if not cluster_centre:
            cluster_centre = (df['lat'].mean(), df['lon'].mean())

        # Calculate statistics
        cluster_stats = {
            'mean_lat': df['lat'].mean(),
            'mean_lon': df['lon'].mean(),
            'count': df.shape[0],
            # features relative to cluster centre
            'c_mean_lat_trimmed': np.mean(df['lat'] - cluster_centre[0], 0.1),
            'c_mean_lon_trimmed': np.std(df['lon'] - cluster_centre[1]),
            'c_std_lat_trimmed': np.std(df['lat'] - cluster_centre[0]),
            'c_std_lon_trimmed': np.std(df['lon'] - cluster_centre[1]),
            #todo: add Mahalanobis distance
        }
        return pd.DataFrame([cluster_stats])

    def _add_distances_function_column(
            self,
            points_col: pd.Series,
            centre_coordinates: List[float],
            func = np.mean,
            **kwargs
    ):
        x = points_col.apply(
            lambda row: func(self.calculate_distances(row, centre_coordinates), **kwargs)
        )
        return x

    def apply_clusters_distribution(self, df) -> pd.DataFrame:
        cluster_columns = [f'cluster_{i}' for i in range(self.clusterizer.n_groups)]

        df_clusters = df.apply(lambda row: self.clusterizer.assign_clusters(row['points']), axis=1)
        df_clusters = pd.DataFrame(df_clusters.tolist(), columns=cluster_columns)

        return pd.concat([df, df_clusters], axis=1)

    def msc_centre_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates within-groups statistics: mean distance from the city centre within cluster, number of points in cluster, dispersion of distance between dotes in a cluster, number of boards oriented north, number of boards oriented west, etc.
        :param df: pd.DataFrame with columns `lan`, `lon`, `cluster_1`, `cluster_2`, etc.
        :return: modified pd.DataFrame with added features
        """
        df_res = (
            df
            .assign(
                distance_msc_centre_mean=lambda df_: self._add_distances_function_column(
                    df_['points'], self.moscow_centre_coordinates, np.mean
                )
            )
            .assign(
                distance_msc_centre_median=lambda df_: self._add_distances_function_column(
                    df_['points'], self.moscow_centre_coordinates, np.median
                )
            )
            .assign(
                distance_msc_centre_std=lambda df_: self._add_distances_function_column(
                    df_['points'], self.moscow_centre_coordinates, np.std
                )
            )
            .assign(
                distance_msc_centre_mean_trim=lambda df_: self._add_distances_function_column(
                    df_['points'], self.moscow_centre_coordinates,
                    stats.trim_mean, proportiontocut=0.1
                )
            )
        )
        return df_res

    def preprocess(self, df) -> pd.DataFrame:
        df_clusters = (
            pd.concat([df, pd.json_normalize(df['targetAudience'])], axis=1)
            .pipe(self.msc_centre_statistics)
            .pipe(self.apply_clusters_distribution)

            .assign(salary_a=lambda df_: df_['income'].apply(lambda x: 1 if 'a' in x else 0))
            .assign(salary_b=lambda df_: df_['income'].apply(lambda x: 1 if 'c' in x else 0))
            .assign(salary_c=lambda df_: df_['income'].apply(lambda x: 1 if 'b' in x else 0))
            .assign(male=lambda df_: df_['income'].apply(lambda x: 1 if 'c' in x else 0))
            .assign(female=lambda df_: df_['gender'].apply(lambda x: 1 if x in ['female', 'all'] else 0))
            .assign(num_points=lambda df_: df_['points'].apply(lambda l: len(l)))
            .drop(columns=['hash', 'targetAudience', 'points', 'income', 'name', 'gender'])
        )
        return df_clusters
