from shiny import App, ui, reactive, render
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import numpy as np
from shinywidgets import output_widget, render_widget

# This is the cleaned data file I made earlier, so the app starts from this.
df = pd.read_csv("data/clean_oecd_immunisation.csv")

app_ui = ui.page_fluid(
    ui.head_content(ui.include_css("www/styles.css")),

    # Header that stays at the top while I scroll the dashboard.
    ui.div(
        ui.div(
            ui.h2("OECD Immunisation Dashboard"),
            class_="app-header"
        ),
        ui.div(class_="header-stripe"),
        class_="sticky-topbar"
    ),

    # Sidebar layout
    ui.layout_sidebar(

        # These are the filters the user can change.
        ui.sidebar(
            ui.div(
                ui.input_select(
                    "vaccine",
                    "Choose a vaccine",
                    [
                        "Measles",
                        "Diphtheria, Tetanus, Pertussis",
                        "Hepatitis B"
                    ]
                ),

                # This slider lets the user choose the years they want to see.
                ui.div(
                    ui.input_slider(
                        "year_range",
                        "Select Year Range",
                        min=df["year"].min(),
                        max=df["year"].max(),
                        value=(df["year"].min(), df["year"].max()),
                        step=1
                    ),
                    class_="year-range-control"
                ),

                ui.div(
                    ui.input_selectize(
                        "country",
                        "Choose countries",
                        sorted(df["country"].unique().tolist()),
                        multiple=True
                    ),
                    class_="selected-countries-control"
                ),

                class_="sticky-sidebar"
            ),
            class_="sticky-sidebar-shell"
        ),

        # The four number cards at the top of the dashboard.
        ui.div(
            # Overall coverage card.
            ui.div(
                ui.h4(
                    "Average Latest Coverage across all OECD countries",
                    style="margin-bottom: 10px;"
                ),

                ui.h2(
                    ui.output_ui("latest_coverage_text"),
                    class_="kpi-value"
                ),

                class_="kpi-card"
            ),

            # This card changes when countries are selected in the sidebar.
            ui.div(
                ui.h4(
                    "Average Latest Coverage for Selected Countries",
                    style="margin-bottom: 10px;"
                ),
                ui.h2(
                    ui.output_ui("selected_latest_coverage_text"),
                    class_="kpi-value"
                ),
                class_="kpi-card selected-countries-kpi"
            ),

            # Lowest coverage card.
            ui.div(
                ui.h4(
                    "Country with Lowest Most Recent Coverage",
                    style="margin-bottom: 10px;"
                ),
                ui.h2(
                    ui.output_ui("lowest_coverage_text"),
                    class_="kpi-value kpi-value-low"
                ),

                class_="kpi-card"
            ),

            # Highest coverage card.
            ui.div(
                ui.h4(
                    "Country with Highest Most Recent Coverage",
                    style="margin-bottom: 10px;"
                ),
                ui.h2(
                    ui.output_ui("highest_coverage_text"),
                    class_="kpi-value kpi-value-high"
                ),

                class_="kpi-card"
            ),
            class_="kpi-layout"
        ),

        # Main line plot showing the trend over time.
        ui.div(
            ui.output_plot("line_plot"),
            class_="plot-card"
        ),

        # Two extra charts underneath: one bar chart and one heatmap.
        ui.div(
            ui.div(
                output_widget("bar_chart"),
                class_="overview-plot-card"
            ),
            ui.div(
                output_widget("heatmap"),
                class_="overview-plot-card chart-placeholder"
            ),
            class_="additional-plots"
        ),
    ),

    # Overall page styling for the dark dashboard background.
    style="""
        background-color: #1f2937;
        color: #f9fafb;
        min-height: 100vh;
        padding: 20px;
    """
)


def server(input, output, session):
    def filter_data(selected_countries=None):
        # This is my main filter helper, so I do not repeat the same filtering
        # code in every chart and KPI.
        selected_vaccine = input.vaccine()
        start_year, end_year = input.year_range()

        # Keep only the vaccine, year range and non-empty coverage values.
        filtered_df = df[
            (df["vaccine"] == selected_vaccine) &
            (df["year"].between(start_year, end_year)) &
            (df["coverage"].notna())
        ]

        # If countries were selected, narrow the data down to just those.
        if selected_countries is not None:
            filtered_df = filtered_df[
                filtered_df["country"].isin(selected_countries)
            ]

        return filtered_df

    def kpi_value(coverage):
        # Adds the % sign and changes the colour depending on the coverage.
        if coverage == "N/A":
            return ui.span(coverage)

        coverage_value = float(coverage)
        if coverage_value >= 95:
            value_class = "kpi-value-high"
        elif coverage_value < 90:
            value_class = "kpi-value-low"
        else:
            value_class = ""
        return ui.span(f"{coverage}%", class_=value_class)

    @reactive.calc
    def latest_coverage():
        
        filtered_df = filter_data()

        if filtered_df.empty:
            return "N/A"

        # Keep only latest year available after filtering.
        most_recent_year = filtered_df["year"].max()
        latest_data = filtered_df[filtered_df["year"] == most_recent_year]

        if latest_data.empty:
            return "N/A"

        average_coverage = latest_data["coverage"].mean()

        return f"{average_coverage:.1f}"
    
    @reactive.calc
    def selected_latest_coverage():
        # Same idea as latest_coverage, but only for the selected countries.
        selected_countries = input.country()

        filtered_df = filter_data(selected_countries)

        if filtered_df.empty:
            return "N/A"

        most_recent_year = filtered_df["year"].max()
        latest_data = filtered_df[filtered_df["year"] == most_recent_year]

        if latest_data.empty:
            return "N/A"

        average_coverage = latest_data["coverage"].mean()

        return f"{average_coverage:.1f}"
    
    # Extra KPIs for highest and lowest coverage.
    @reactive.calc
    def lowest_coverage():
        filtered_df = filter_data()

        if filtered_df.empty:
            return "N/A"

        most_recent_year = filtered_df["year"].max()
        latest_data = filtered_df[filtered_df["year"] == most_recent_year]

        if latest_data.empty:
            return "N/A"

        # idxmin finds the row number for the smallest coverage value.
        lowest_row = latest_data.loc[latest_data["coverage"].idxmin()]

        return f"{lowest_row['country']} ({lowest_row['coverage']:.1f}%)"
    
    @reactive.calc
    def highest_coverage():
        filtered_df = filter_data()

        if filtered_df.empty:
            return "N/A"

        most_recent_year = filtered_df["year"].max()
        latest_data = filtered_df[filtered_df["year"] == most_recent_year]

        if latest_data.empty:
            return "N/A"

        # idxmax does the same thing, but for the biggest coverage value.
        highest_row = latest_data.loc[latest_data["coverage"].idxmax()]

        return f"{highest_row['country']} ({highest_row['coverage']:.1f}%)"
    
    @render.ui
    def latest_coverage_text():
        return kpi_value(latest_coverage())

    @render.ui
    def selected_latest_coverage_text():
        return kpi_value(selected_latest_coverage())

    @render.ui
    def lowest_coverage_text():
        return ui.span(lowest_coverage(), class_="kpi-value kpi-value-low")

    @render.ui
    def highest_coverage_text():
        return ui.span(highest_coverage(), class_="kpi-value kpi-value-high")

    @render.plot
    def line_plot():
        # Matplotlib/seaborn chart for showing each selected country over time.
        selected_countries = input.country()

        filtered_df = filter_data(selected_countries)

        if filtered_df.empty:
            return None

        # Create the blank chart area.
        fig, ax = plt.subplots(figsize=(10, 6))

        # Light plot background so the chart is easier to read.
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Draw one line per country.
        sns.lineplot(
            data=filtered_df,
            x="year",
            y="coverage",
            hue="country",
            marker="o",
            ax=ax
        )

        # Plot titles and labels
        ax.set_title(
            f"Immunisation Coverage for {input.vaccine()}",
            color="#1f2937",
            fontsize=16
        )

        ax.set_xlabel("Year", color="#1f2937")
        ax.set_ylabel("Coverage (%)", color="#1f2937")

        # Axis styling
        ax.tick_params(colors="#1f2937")

        # Dynamic y-axis, with a bit of space below the lowest value.
        ax.set_ylim(
            max(0, filtered_df["coverage"].min() - 5),
            100
        )

        # WHO target line, so 95% is easy to spot.
        target_line = ax.axhline(
            95,
            color="#F2C14E",
            linestyle="--",
            linewidth=2,
            label="WHO Target (95%)"
        )

        # Grid styling
        ax.grid(True, color="#D1D5DB", alpha=0.8)

        # Separate legends so the country list and WHO target do not get mixed.
        country_handles, country_labels = ax.get_legend_handles_labels()

        country_items = [
            (handle, label)
            for handle, label in zip(country_handles, country_labels)
            if label in selected_countries
        ]

        country_legend = ax.legend(
            handles=[handle for handle, _ in country_items],
            labels=[label for _, label in country_items],
            title="Country",
            loc="lower left",
            facecolor="white",
            edgecolor="#D1D5DB",
            labelcolor="#1f2937"
        )

        # Match legend title to the light plot background
        country_legend.get_title().set_color("#1f2937")

        ax.add_artist(country_legend)

        # Threshold legend
        threshold_legend = ax.legend(
            handles=[target_line],
            labels=["WHO Target (95%)"],
            loc="upper right",
            facecolor="white",
            edgecolor="#D1D5DB",
            labelcolor="#1f2937"
        )

        # Match legend text to the light plot background
        for text in threshold_legend.get_texts():
            text.set_color("#1f2937")

        # Light plot borders
        for spine in ax.spines.values():
            spine.set_color("#9CA3AF")

        fig.tight_layout()

        return fig

    @render_widget
    def bar_chart():
        # Plotly bar chart showing the latest coverage for every country.
        filtered_df = filter_data()

        if filtered_df.empty:
            return None

        latest_data = (
            # Sort by year, then keep the last row for each country.
            filtered_df.sort_values("year")
            .groupby("country", as_index=False)
            .tail(1)
            .sort_values("coverage", ascending=True)
        )

        if latest_data.empty:
            return None

        selected_countries = input.country()
        if selected_countries is None:
            selected_countries = set()
        elif isinstance(selected_countries, str):
            selected_countries = {selected_countries}
        else:
            selected_countries = set(selected_countries)

        def bar_color(row):
            # Selected countries get lighter colours so they stand out.
            is_selected = row["country"] in selected_countries
            coverage = row["coverage"]

            if coverage < 90:
                return "#F3B8A9" if is_selected else "#D97B66"
            if coverage < 95:
                return "#9DCAEC" if is_selected else "#2F80C3"
            return "#8FD3BE" if is_selected else "#1F8A70"

        bar_colors = latest_data.apply(bar_color, axis=1)

        x_min = max(0, latest_data["coverage"].min() - 5)
        x_max = min(105, max(100, latest_data["coverage"].max() + 5))

        fig = go.Figure(
            go.Bar(
                x=latest_data["coverage"].tolist(),
                y=latest_data["country"].tolist(),
                orientation="h",
                marker_color=bar_colors.tolist(),
                customdata=latest_data["year"].astype(int).tolist(),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Coverage: %{x:.1f}%<br>"
                    "Latest year: %{customdata}"
                    "<extra></extra>"
                )
            )
        )

        fig.add_vline(
            x=95,
            line_dash="dash",
            line_color="#f2c94c",
            line_width=2,
            annotation_text="WHO Target (95%)",
            annotation_position="top right",
            annotation_font={"color": "#1f2937", "size": 12}
        )

        fig.update_layout(
            title={
                "text": f"Latest Available {input.vaccine()} Coverage by Country",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#1f2937"}
            },
            template="plotly_white",
            xaxis_title="Coverage (%)",
            yaxis_title="Country",
            height=900,
            margin={"l": 120, "r": 30, "t": 70, "b": 60},
            showlegend=False,
            hoverlabel={"bgcolor": "white", "font_color": "#1f2937"}
        )

        fig.update_xaxes(
            range=[x_min, x_max],
            gridcolor="#D1D5DB",
            title_font={"color": "#1f2937", "size": 14},
            tickfont={"color": "#1f2937", "size": 11}
        )
        fig.update_yaxes(
            autorange="reversed",
            title_font={"color": "#1f2937", "size": 14},
            tickfont={"color": "#1f2937", "size": 11}
        )

        return fig

    @render_widget
    def heatmap():
        # Heatmap showing coverage across years, with countries ordered by latest coverage.
        filtered_df = filter_data()

        if filtered_df.empty:
            return None

        latest_data = (
            # This gives the most recent row per country, used for sorting.
            filtered_df.sort_values("year")
            .groupby("country", as_index=False)
            .tail(1)
            .sort_values("coverage", ascending=True)
        )
        country_order = latest_data["country"].tolist()

        selected_countries = input.country()
        if selected_countries is None:
            selected_countries = set()
        elif isinstance(selected_countries, str):
            selected_countries = {selected_countries}
        else:
            selected_countries = set(selected_countries)

        def selected_arrow_color(coverage):
            # Match the arrow colour to the same coverage bands used elsewhere.
            if coverage < 90:
                return "#F3B8A9"
            if coverage < 95:
                return "#9DCAEC"
            return "#8FD3BE"

        selected_country_arrows = [
            # Add an arrow beside countries selected in the sidebar.
            {
                "x": -0.5,
                "xref": "paper",
                "y": row["country"],
                "yref": "y",
                "text": "➤",
                "showarrow": False,
                "font": {
                    "color": selected_arrow_color(row["coverage"]),
                    "size": 28
                },
                "xanchor": "center",
                "yanchor": "middle"
            }
            for _, row in latest_data.iterrows()
            if row["country"] in selected_countries
        ]

        pivot_df = (
            # Pivot turns the data into a table shape that the heatmap needs:
            # countries down the side, years across the top.
            filtered_df.pivot_table(
                index="country",
                columns="year",
                values="coverage"
            )
            .reindex(country_order)
        )

        fig = go.Figure(
            go.Heatmap(
                z=pivot_df.replace({np.nan: None}).values.tolist(),
                x=[str(year) for year in pivot_df.columns],
                y=pivot_df.index.tolist(),
                colorscale=[
                    [0.0, "#D97B66"],
                    [0.5, "#2F80C3"],
                    [1.0, "#1F8A70"]
                ],
                zmin=80,
                zmax=100,
                colorbar={
                    "title": {"text": "Coverage (%)", "font": {"size": 14}},
                    "tickfont": {"size": 11}
                },
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Year: %{x}<br>"
                    "Coverage: %{z:.1f}%"
                    "<extra></extra>"
                )
            )
        )

        fig.update_layout(
            title={
                "text": f"{input.vaccine()} Coverage Heatmap",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": "#1f2937"}
            },
            template="plotly_white",
            xaxis_title="Year",
            yaxis_title="Country",
            height=900,
            margin={"l": 190, "r": 30, "t": 70, "b": 60},
            annotations=selected_country_arrows,
            hoverlabel={"bgcolor": "white", "font_color": "#1f2937"}
        )
        fig.update_xaxes(
            title_font={"color": "#1f2937", "size": 14},
            tickfont={"color": "#1f2937", "size": 11}
        )
        fig.update_yaxes(
            autorange="reversed",
            title_font={"color": "#1f2937", "size": 14},
            tickfont={"color": "#1f2937", "size": 11}
        )
        return fig

app = App(app_ui, server)
