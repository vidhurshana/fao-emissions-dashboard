# =============================================================================
# EDA & Data Cleaning — FAO Agrifood GHG Emissions
# 5DATA004C Data Science Project Lifecycle
# =============================================================================
# Run this script first to understand the data before building the dashboard.
# Outputs a cleaned CSV: FAO_EMSTOT_clean.csv
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import warnings
warnings.filterwarnings("ignore")

plt.style.use("seaborn-v0_8-whitegrid")
FIGSIZE = (12, 5)

# ─── 1. LOAD RAW DATA ────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1 — LOAD RAW DATA")
print("=" * 60)

df_raw = pd.read_csv("/Users/vidhurshanaj/DATA SCIENCE/FAO_EMSTOT.csv")
print(f"Shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
print(f"\nAll columns:\n{list(df_raw.columns)}")


# ─── 2. STRUCTURAL AUDIT ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2 — STRUCTURAL AUDIT")
print("=" * 60)

# Identify columns with only one unique value (metadata, not analytical)
single_val_cols = [c for c in df_raw.columns if df_raw[c].nunique() == 1]
print(f"\nColumns with a single unique value (metadata — will be dropped):")
for c in single_val_cols:
    print(f"  {c:30s} = {df_raw[c].iloc[0]}")

useful_cols = {
    "REF_AREA_LABEL": "Country",
    "REF_AREA": "Country_Code",
    "TIME_PERIOD": "Year",
    "OBS_VALUE": "Emissions_kt",
}
print(f"\nRetaining columns: {list(useful_cols.keys())}")


# ─── 3. INITIAL CLEAN ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3 — INITIAL CLEAN")
print("=" * 60)

df = df_raw[list(useful_cols.keys())].copy()
df.rename(columns=useful_cols, inplace=True)

# Unit conversion: kilotonnes → megatonnes (more readable at country level)
df["Emissions_Mt"] = df["Emissions_kt"] / 1_000
print(f"Converted Emissions_kt → Emissions_Mt (÷ 1,000)")

print(f"\nMissing values:\n{df.isnull().sum()}")
print(f"\nDuplicate rows: {df.duplicated().sum()}")
print(f"\nDate range: {df['Year'].min()} – {df['Year'].max()}")
print(f"Countries (raw): {df['Country'].nunique()}")


# ─── 4. HANDLE REGIONAL AGGREGATES ──────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 4 — REMOVE REGIONAL AGGREGATES")
print("=" * 60)

# These entries represent multi-country aggregates, not individual nations
aggregates = ["World", "South Asia", "North America"]
df_agg = df[df["Country"].isin(aggregates)]
df = df[~df["Country"].isin(aggregates)].copy()

print(f"Removed aggregates: {aggregates}")
print(f"Rows removed: {len(df_agg)}")
print(f"Remaining countries: {df['Country'].nunique()}")


# ─── 5. ZERO VALUE ANALYSIS ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5 — ZERO VALUE ANALYSIS")
print("=" * 60)

zeros = df[df["Emissions_kt"] == 0]
zero_countries = zeros["Country"].unique()
print(f"Zero-emission entries: {len(zeros)} rows across {len(zero_countries)} countries")
print(f"Countries affected: {list(zero_countries)}")
print("\nDecision: RETAIN — zeros are valid (tiny island territories with negligible")
print("agrifood activity). They do not distort analysis and are filtered in the")
print("choropleth map by using a log scale.")


# ─── 6. DATA COMPLETENESS ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 6 — DATA COMPLETENESS (year coverage per country)")
print("=" * 60)

coverage = df.groupby("Country")["Year"].count()
full = (coverage == 61).sum()
incomplete_countries = coverage[coverage < 61].sort_values()

print(f"Countries with full 61-year coverage (1961–2021): {full}")
print(f"Countries with partial coverage: {len(incomplete_countries)}")
print(f"\nReason: Many post-Soviet / post-colonial states only have data")
print(f"from their year of independence (e.g., Estonia, Croatia from 1992).")
print(f"\nDecision: RETAIN all — partial data is still valid for the years present.")
print(f"\nBottom 10 coverage:")
print(incomplete_countries.head(10).to_string())


# ─── 7. OUTLIER ANALYSIS ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 7 — OUTLIER ANALYSIS")
print("=" * 60)

Q1 = df["Emissions_Mt"].quantile(0.25)
Q3 = df["Emissions_Mt"].quantile(0.75)
IQR = Q3 - Q1
outlier_threshold = Q3 + 3 * IQR

outliers = df[df["Emissions_Mt"] > outlier_threshold]
print(f"IQR method (>Q3 + 3×IQR = >{outlier_threshold:.1f} Mt): {len(outliers)} rows")
print(f"Outlier countries: {outliers['Country'].unique()[:10]}")
print(f"\nDecision: RETAIN — these are genuine large emitters (China, Brazil, India,")
print(f"USA, Indonesia). Removing them would distort the analysis.")

print(f"\nDescriptive statistics (Emissions_Mt):")
print(df["Emissions_Mt"].describe().round(3).to_string())


# ─── 8. EDA — GLOBAL TREND ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 8 — EDA: GLOBAL TREND")
print("=" * 60)

global_trend = df.groupby("Year")["Emissions_Mt"].sum().reset_index()
corr = global_trend["Year"].corr(global_trend["Emissions_Mt"])
print(f"Pearson correlation (Year vs Global Emissions): {corr:.4f}")
print(f"→ Strong positive trend: emissions have risen consistently over 60 years.")

# Growth milestones
for yr in [1961, 1970, 1980, 1990, 2000, 2010, 2021]:
    val = global_trend.loc[global_trend["Year"] == yr, "Emissions_Mt"].values[0]
    print(f"  {yr}: {val:,.1f} Mt")

pct = (global_trend[global_trend["Year"]==2021]["Emissions_Mt"].values[0] /
       global_trend[global_trend["Year"]==1961]["Emissions_Mt"].values[0] - 1) * 100
print(f"\nTotal growth 1961–2021: +{pct:.1f}%")

fig, ax = plt.subplots(figsize=FIGSIZE)
ax.fill_between(global_trend["Year"], global_trend["Emissions_Mt"], alpha=0.3, color="#2e7d32")
ax.plot(global_trend["Year"], global_trend["Emissions_Mt"], color="#2e7d32", linewidth=2)
ax.set_title("Global Agrifood GHG Emissions (1961–2021)", fontsize=14, fontweight="bold")
ax.set_xlabel("Year")
ax.set_ylabel("Total Emissions (Mt CO₂eq)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
plt.tight_layout()
plt.savefig("eda_01_global_trend.png", dpi=150)
plt.close()
print("\n→ Saved: eda_01_global_trend.png")


# ─── 9. EDA — TOP 10 EMITTERS ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 9 — EDA: TOP 10 EMITTERS (2021)")
print("=" * 60)

latest = df[df["Year"] == 2021].copy()
top10 = latest.nlargest(10, "Emissions_Mt")[["Country", "Emissions_Mt"]]
total_2021 = latest["Emissions_Mt"].sum()
top10["Share_%"] = (top10["Emissions_Mt"] / total_2021 * 100).round(1)
print(top10.to_string(index=False))
print(f"\nTop 10 share of global total: {top10['Share_%'].sum():.1f}%")

fig, ax = plt.subplots(figsize=FIGSIZE)
colors = plt.cm.Reds(np.linspace(0.4, 0.9, 10))
bars = ax.barh(top10["Country"], top10["Emissions_Mt"], color=colors[::-1])
ax.set_xlabel("GHG Emissions (Mt CO₂eq)")
ax.set_title("Top 10 Agrifood GHG Emitters — 2021", fontsize=14, fontweight="bold")
for bar, val in zip(bars, top10["Emissions_Mt"]):
    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
            f"{val:,.0f}", va="center", fontsize=8)
plt.tight_layout()
plt.savefig("eda_02_top10_emitters.png", dpi=150)
plt.close()
print("→ Saved: eda_02_top10_emitters.png")


# ─── 10. EDA — DECADE ANALYSIS ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 10 — EDA: AVERAGE ANNUAL EMISSIONS BY DECADE")
print("=" * 60)

df["Decade"] = (df["Year"] // 10) * 10
decade_avg = df.groupby("Decade")["Emissions_Mt"].sum().reset_index()
decade_avg = decade_avg[decade_avg["Decade"] < 2020]  # exclude partial 2020s
print(decade_avg.to_string(index=False))


# ─── 11. EDA — GROWTH RATE ANALYSIS ─────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 11 — EDA: FASTEST GROWING COUNTRIES (1990–2021)")
print("=" * 60)

base = df[df["Year"] == 1990].set_index("Country")["Emissions_Mt"]
end  = df[df["Year"] == 2021].set_index("Country")["Emissions_Mt"]
common = base.index.intersection(end.index)
base_nz = base[common].replace(0, np.nan)
growth = ((end[common] - base[common]) / base_nz * 100).dropna().sort_values(ascending=False)

print("Top 10 fastest growing (%):")
print(growth.head(10).round(1).to_string())
print("\nTop 10 largest reductions (%):")
print(growth.tail(10).round(1).to_string())


# ─── 12. SAVE CLEANED DATA ───────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 12 — SAVE CLEANED DATASET")
print("=" * 60)

df_final = df[["Country", "Country_Code", "Year", "Emissions_kt", "Emissions_Mt"]].copy()
df_final = df_final.sort_values(["Country", "Year"]).reset_index(drop=True)
df_final.to_csv("FAO_EMSTOT_clean.csv", index=False)

print(f"Saved: FAO_EMSTOT_clean.csv")
print(f"Final shape: {df_final.shape[0]:,} rows × {df_final.shape[1]} columns")
print(f"Columns: {list(df_final.columns)}")

print("\n" + "=" * 60)
print("EDA COMPLETE — Key Findings Summary")
print("=" * 60)
print("""
1. NO MISSING VALUES — dataset is complete (12,639 rows).
2. 3 REGIONAL AGGREGATES removed (World, South Asia, North America).
3. 114 ZERO VALUES retained — valid data for tiny island territories.
4. 62 COUNTRIES with partial year coverage retained — data valid for years present.
5. STATISTICAL OUTLIERS (large emitters) retained — genuine, not errors.
6. STRONG UPWARD TREND — global emissions grew +472% from 1961 to 2021 (r=0.94).
7. TOP 10 COUNTRIES account for ~52% of global agrifood emissions in 2021.
8. CHINA, BRAZIL, INDIA, USA are consistently the four largest emitters.
9. FASTEST GROWTH since 1990 in Middle East & African nations (Qatar, Chad).
10. LARGEST DECLINES in small island states (Pitcairn, Montserrat, Wallis-Futuna).
""")