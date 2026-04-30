import pandas as pd 
import numpy as np
from scipy import stats
from scipy._lib.array_api_extra import nunique


class interfaceEngine:
    def __init__(self,df: pd.DataFrame):
        # stores the dataframe so every method can accessit
        self.df = df

        # This list will collect every insight we discover
        # Each insight is a dictionary describing one finding
        self.insights = []
        
        #where we store each coluns type 
        self.column_profiles = {}


    def run(self) -> dict:
        #understand the columns()
        self._profile_columns()

        #Analyze each column based on its type
        for col, col_type in self.column_profiles.items():
            if col_type == "numeric":
                self._analyse_numeric(col)
            elif col_type == "categorical":
                self._analyse_categorical(col)
            elif col_type == "datetime":
                self._analyse_datetime(col)

        #look at the relationship between the columns
        self._detect_relationships()

        return self._compile_report()


    def _profile_columns(self):
        """
        Profiles each column by inferring its statistical type.
        We go beyond Pandas dtypes — a column of 0s and 1s is
        numeric to Pandas but CATEGORICAL to a statistician.
        """
        for col in self.df.columns:
            series = self.df[col]

            # Rule 1: If Pandas already knows it's a datetime, trust it
            if pd.api.types.is_datetime64_any_dtype(series):
                self.column_profiles[col] = "datetime"

            # Rule 2: If it's numeric, we do a deeper check
            elif pd.api.types.is_numeric_dtype(series):
                unique_count = series.nunique()
                total_count = len(series)

                # Rule 2a: If a numeric column has very few unique values
                # relative to the dataset size, it's likely categorical
                # Example: A "Rating" column with values 1,2,3,4,5
                # This threshold (5% or max 15 unique) is a heuristic — 
                # a rule of thumb, not a law
                if unique_count <= 15 or (unique_count / total_count) < 0.05:
                    self.column_profiles[col] = "categorical"
                else:
                    self.column_profiles[col] = "numeric"

            # Rule 3: Try to parse it as a date if Pandas called it 'object'
            # Some CSVs store dates as strings like "2023-01-15"
            elif pd.api.types.is_object_dtype(series):
                try:
                    pd.to_datetime(series, infer_datetime_format=True)
                    self.column_profiles[col] = "datetime"
                except (ValueError, TypeError):
                    self.column_profiles[col] = "categorical"

    def _analyse_numeric(self, col: str):
        """
        Applies the full suite of descriptive and inferential
        statistical rules to a numeric column.
        """
        series = self.df[col].dropna()
        # --- Descriptive Statistics ------------------
        mean = series.mean()
        median = series.median()
        std = series.std()
        minimum = series.min()
        maximum = series.max()

        skewness = series.skew()
        
        if abs(skewness) < 0.5:
            skew_label = "approximately symmetric"
            central_tendency = "mean"
        elif abs(skewness) < 1.0:
            skew_label = "modrately skewed"
            central_tendency = "median"
        else:
            skew_label = "highly skewed"
            central_tendency = "median"

        direction = "right (positive)" if skewness > 0 else "left (negative)"

        self.insights.append({
            "column": col,
            "type": "distribution_shape",
            "finding": f"'{col}' is {skew_label}, skewed {direction} "
                       f"(skewness = {skewness:.2f}). "
                       f"use the {central_tendency} as the measure of centre.",
            "value": {"mean": mean, "median": median, "skewness": skewness}
        })

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        lower_fence = Q1 - 1.5 * IQR
        upper_fence = Q3 + 1.5 * IQR

        outliers = series[(series < lower_fence) | (series > upper_fence)]
        outlier_count = len(outliers)
        outliers_pct = (outlier_count / len(series)) * 100

        if outlier_count > 0:
            self.insights.append({
                "column": col,
                "type": "outliers",
                "finding": f"'{col}' contains {outlier_count} potential outliers" 
                           f"({outliers_pct:.1f}% of data) outside the range"
                           f"[{lower_fence:.2f}, {upper_fence:.2f}].",
                "values": {"lower_fence": lower_fence, "upper_fence": upper_fence,
                           "outlier_count": outlier_count}
            })

        # ── RULE: Normality Test (Shapiro-Wilk) ───────────────────────────────
        # The Shapiro-Wilk test checks whether data could plausibly come
        # from a normal distribution.
        #
        # H₀ (null hypothesis): The data IS normally distributed
        # H₁ (alternative):     The data is NOT normally distributed
        #
        # If p-value > 0.05 → We FAIL TO REJECT H₀ → Assume normality
        # If p-value ≤ 0.05 → We REJECT H₀ → Not normally distributed
        #
        # Why this matters: Many statistical tests (t-test, ANOVA, Pearson 
        # correlation) ASSUME normality. If your data fails this test,
        # you should use non-parametric alternatives instead.
        #
        # Shapiro-Wilk works best for n < 5000. For larger samples,
        # we use D'Agostino-Pearson or Anderson-Darling.

        if len(series) < 5000:
            stat, p_value = stats.shapiro(series)
            test_name = "Shapiro-Wilk"
        else:
            stat, p_value = stats.normaltest(series)
            test_name = "D'Agostino-Pearson"

        is_normal = p_value > 0.05

        self.insights.append({
            "column": col,
            "type": "normality",
            "finding": f"'{col}' {'appears normally distributed' if is_normal else 'is Not normally distributed'} "
                       f"({test_name} test: p = {p_value:.4f}). "
                       f"{'Parametric tests (t-test, Pearson) are appropriate.' if is_normal else 'Consider non-parametric alternatives (Mann-Whitney, Spearman).'}",
            "values": {"test": test_name, "p_value": p_value, "is_normal": is_normal}
        })

    def _analyse_categorical(self, col: str):
        """
        Analyses categorical columns for dominance, imbalance,
        and cardinality issues.
        """
        series = self.df[col].dropna()
        value_counts = series.value_counts()
        total = len(series)
        n_unique = series.nunique()
        # ── RULE: Dominant Category Detection ────────────────────────────────
        # If one category holds more than 50% of all values,
        # it "dominates" the column. This is a red flag for:
        # - Imbalanced classification datasets (ML problem)
        # - Poor survey design (everyone chose "Other")
        # - Data entry errors (same value repeated)

        top_category = value_counts.index[0]
        top_pct = (value_counts.iloc[0] / total) * 100
        cardinality_ratio = n_unique / total

        if top_pct > 80:
            self.insights.append({
                "column": col,
                "type": "dominance",
                "finding": f"'{col}' is dominated by '{top_category}' "
                           f"({top_pct:.1f}% of values). "
                           f"This may indicate an imbalanced dataset.",
                "values": {"unique_count": n_unique, "cardinality_ratio": cardinality_ratio}
            })

    def _analyse_datetime(self, col: str):
        """
        Analyzes datetime columns for temporal patterns and insights.
        """
        series = self.df[col].dropna()
        
        # Convert to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(series):
            series = pd.to_datetime(series, errors='coerce').dropna()
        
        # Basic temporal statistics
        min_date = series.min()
        max_date = series.max()
        date_range = (max_date - min_date).days
        
        # Check for missing dates in the range
        if date_range > 0:
            expected_dates = pd.date_range(start=min_date, end=max_date, freq='D')
            missing_dates = len(expected_dates) - len(series.dt.date.unique())
            missing_pct = (missing_dates / len(expected_dates)) * 100
            
            self.insights.append({
                "column": col,
                "type": "temporal_coverage",
                "finding": f"'{col}' spans {date_range} days from {min_date.date()} to {max_date.date()}. "
                           f"Missing {missing_dates} dates ({missing_pct:.1f}% coverage).",
                "values": {
                    "min_date": str(min_date),
                    "max_date": str(max_date),
                    "date_range_days": date_range,
                    "missing_dates": missing_dates,
                    "coverage_pct": 100 - missing_pct
                }
            })

    def _detect_relationships(self):
        """
        Examines pairs of columns together to find correlations
        and statistical associations.
        """
        numeric_cols = [col for col, t in self.column_profiles.items()
                        if t == "numeric"]

        # ── RULE: Pearson Correlation ─────────────────────────────────────────
        # Pearson's r measures the LINEAR relationship between two 
        # numeric variables. Range: -1 to +1.
        #
        # Interpretation (Cohen's convention):
        #   |r| < 0.3  → Weak
        #   0.3 ≤ |r| < 0.7 → Moderate  
        #   |r| ≥ 0.7  → Strong
        #
        # We also compute the p-value to test if the correlation is
        # statistically significant or just due to random chance.
        # p < 0.05 means we're 95% confident the correlation is real.
        #
        # IMPORTANT: Correlation ≠ Causation. Always note this.

        if len(numeric_cols) >= 2:
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col_a = numeric_cols[i]
                    col_b = numeric_cols[j]

                    # Drop rows where either column has NaN
                    pair = self.df[[col_a, col_b]].dropna()

                    if len(pair) < 5:
                        continue  # Not enough data to correlate

                    r, p_value = stats.pearsonr(pair[col_a], pair[col_b])
                    abs_r = abs(r)

                    if abs_r < 0.3:
                        strength = "weak"
                    elif abs_r < 0.7:
                        strength = "moderate"
                    else:
                        strength = "strong"

                    direction = "positive" if r > 0 else "negative"
                    significant = p_value < 0.05

                    # Only report if meaningful (moderate or stronger)
                    # and statistically significant
                    if abs_r >= 0.3 and significant:
                        self.insights.append({
                            "columns": [col_a, col_b],
                            "type": "correlation",
                            "finding": f"There is a {strength} {direction} correlation "
                                       f"between '{col_a}' and '{col_b}' "
                                       f"(r = {r:.2f}, p = {p_value:.4f}). "
                                       f"This is statistically significant.",
                            "values": {"r": r, "p_value": p_value}
                        })


    def _compile_report(self) -> dict:
        """
        Assembles all findings into a structured report
        that your FastAPI route can return as JSON.
        """
        return {
            "summary": {
                "total_rows": len(self.df),
                "total_columns": len(self.df.columns),
                "column_profiles": self.column_profiles,
                "missing_values": self.df.isnull().sum().to_dict()
            },
            "insights": self.insights,
            "insight_count": len(self.insights)
        }