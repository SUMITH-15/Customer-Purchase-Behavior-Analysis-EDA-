import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc
import webbrowser
from threading import Timer

# ── 1. LOAD & CLEAN DATA ─────────────────────────────────────
df = pd.read_csv('India_Superstore.csv', encoding='utf-8')
df = df.dropna().drop_duplicates()
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Month']      = df['Order Date'].dt.month
df['Year']       = df['Order Date'].dt.year

# ── 2. AGGREGATIONS ──────────────────────────────────────────
total_sales   = df['Sales'].sum()
total_profit  = df['Profit'].sum()
total_orders  = len(df)
avg_discount  = df['Discount'].mean() * 100
profit_margin = total_profit / total_sales * 100
total_customers = df['Customer Name'].nunique()

MONTHS = ['Jan','Feb','Mar','Apr','May','Jun',
          'Jul','Aug','Sep','Oct','Nov','Dec']

cat_sales  = df.groupby('Category')['Sales'].sum().reset_index()
cat_profit = df.groupby('Category')['Profit'].sum().reset_index()

monthly = df.groupby('Month')['Sales'].sum().reset_index()
monthly['Label'] = monthly['Month'].apply(lambda m: MONTHS[m - 1])

yearly = df.groupby('Year')['Sales'].sum().reset_index()

region_sales = (df.groupby('Region')['Sales']
                  .sum().sort_values(ascending=False).reset_index())

top10 = (df.groupby('Customer Name')['Sales']
           .sum().sort_values().tail(10).reset_index())

subcat = (df.groupby('Sub-Category')['Sales']
            .sum().sort_values().reset_index())

segment_sales = (df.groupby('Segment')['Sales']
                   .sum().sort_values(ascending=False).reset_index())

state_sales = (df.groupby('State')['Sales']
                 .sum().sort_values(ascending=False).head(10).reset_index())

city_sales = (df.groupby('City')['Sales']
                .sum().sort_values(ascending=False).head(10).reset_index())

corr_df = df[['Sales', 'Profit', 'Discount', 'Quantity']].corr()

# ── 3. COLOURS & SHARED STYLE ────────────────────────────────
BLUE   = '#378ADD'
TEAL   = '#1D9E75'
CORAL  = '#D85A30'
AMBER  = '#BA7517'
PURPLE = '#7F77DD'
LTEAL  = '#5DCAA5'
SAFFRON = '#FF9933'
GREEN  = '#138808'
GRID   = 'rgba(128,128,128,0.12)'
FONT   = dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
              size=12, color='#555')


def make_layout(title='', height=300, margin_r=10):
    d = dict(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=FONT,
        showlegend=False,
        height=height,
        margin=dict(l=10, r=margin_r, t=48 if title else 12, b=10),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(gridcolor=GRID,  zeroline=False),
    )
    if title:
        d['title'] = dict(
            text=f'<b>{title}</b>',
            font=dict(size=14, color='#1a1a1a'),
            x=0, xanchor='left', pad=dict(b=8)
        )
    return d


def fmt_inr(v):
    """Format value as ₹ with L (lakh) or Cr (crore) suffix."""
    sign = '-' if v < 0 else ''
    v = abs(v)
    if v >= 1_00_00_000:
        return f"{sign}₹{v/1_00_00_000:.1f}Cr"
    elif v >= 1_00_000:
        return f"{sign}₹{v/1_00_000:.1f}L"
    else:
        return f"{sign}₹{v/1_000:.0f}K"


def fmt_inr_axis(v):
    """Shorter axis label."""
    if v >= 1_00_00_000:
        return f"₹{v/1_00_00_000:.0f}Cr"
    elif v >= 1_00_000:
        return f"₹{v/1_00_000:.0f}L"
    else:
        return f"₹{v/1_000:.0f}K"


# ── 4. BUILD FIGURES ─────────────────────────────────────────

# --- Sales by Category ---
fig_cat_sales = go.Figure(go.Bar(
    x=cat_sales['Category'],
    y=cat_sales['Sales'],
    marker_color=[SAFFRON, BLUE, GREEN],
    marker_line_width=0,
    text=cat_sales['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_cat_sales.update_layout(**make_layout('Sales by category'))
fig_cat_sales.update_yaxes(tickformat=',.0f')

# --- Profit by Category ---
profit_colors = [CORAL if p < 5_000_000 else TEAL for p in cat_profit['Profit']]
fig_cat_profit = go.Figure(go.Bar(
    x=cat_profit['Category'],
    y=cat_profit['Profit'],
    marker_color=profit_colors,
    marker_line_width=0,
    text=cat_profit['Profit'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_cat_profit.update_layout(**make_layout('Profit by category'))
fig_cat_profit.update_yaxes(tickformat=',.0f')

# --- Monthly Sales Trend ---
fig_monthly = go.Figure(go.Scatter(
    x=monthly['Label'],
    y=monthly['Sales'],
    mode='lines+markers',
    line=dict(color=SAFFRON, width=2.5),
    marker=dict(color=SAFFRON, size=7),
    fill='tozeroy',
    fillcolor='rgba(255,153,51,0.08)',
))
fig_monthly.update_layout(**make_layout('Monthly sales trend', height=320))
fig_monthly.update_xaxes(categoryorder='array', categoryarray=MONTHS)
fig_monthly.update_yaxes(tickformat=',.0f')

# --- Yearly Sales Trend ---
fig_yearly = go.Figure(go.Scatter(
    x=yearly['Year'].astype(str),
    y=yearly['Sales'],
    mode='lines+markers',
    line=dict(color=GREEN, width=2.5),
    marker=dict(color=GREEN, size=9),
    fill='tozeroy',
    fillcolor='rgba(19,136,8,0.08)',
))
fig_yearly.update_layout(**make_layout('Yearly sales trend', height=300))
fig_yearly.update_yaxes(tickformat=',.0f')

# --- Sales by Region ---
fig_region = go.Figure(go.Bar(
    x=region_sales['Region'],
    y=region_sales['Sales'],
    marker_color=AMBER,
    marker_line_width=0,
    text=region_sales['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_region.update_layout(**make_layout('Sales by region'))
fig_region.update_yaxes(tickformat=',.0f')

# --- Profit vs Discount scatter ---
sample = df.sample(min(2000, len(df)), random_state=42)
fig_scatter = go.Figure(go.Scatter(
    x=sample['Discount'],
    y=sample['Profit'],
    mode='markers',
    marker=dict(color='rgba(216,90,48,0.35)', size=6),
))
fig_scatter.update_layout(**make_layout('Profit vs discount'))
fig_scatter.update_xaxes(title_text='Discount rate', tickformat='.0%', showgrid=False)
fig_scatter.update_yaxes(title_text='Profit (₹)', tickformat=',.0f')

# --- Top 10 Customers ---
fig_customers = go.Figure(go.Bar(
    y=top10['Customer Name'],
    x=top10['Sales'],
    orientation='h',
    marker_color=PURPLE,
    marker_line_width=0,
    text=top10['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_customers.update_layout(**make_layout('Top 10 customers by revenue', height=460, margin_r=80))
fig_customers.update_xaxes(tickformat=',.0f')
fig_customers.update_yaxes(showgrid=False)

# --- Sales by Sub-Category ---
fig_subcat = go.Figure(go.Bar(
    y=subcat['Sub-Category'],
    x=subcat['Sales'],
    orientation='h',
    marker_color=LTEAL,
    marker_line_width=0,
    text=subcat['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_subcat.update_layout(**make_layout('Sales by sub-category', height=700, margin_r=70))
fig_subcat.update_xaxes(tickformat=',.0f')
fig_subcat.update_yaxes(showgrid=False)

# --- Top 10 States ---
fig_states = go.Figure(go.Bar(
    y=state_sales['State'],
    x=state_sales['Sales'],
    orientation='h',
    marker_color=SAFFRON,
    marker_line_width=0,
    text=state_sales['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_states.update_layout(**make_layout('Top 10 states by sales', height=420, margin_r=80))
fig_states.update_xaxes(tickformat=',.0f')
fig_states.update_yaxes(showgrid=False)

# --- Top 10 Cities ---
fig_cities = go.Figure(go.Bar(
    y=city_sales['City'],
    x=city_sales['Sales'],
    orientation='h',
    marker_color=GREEN,
    marker_line_width=0,
    text=city_sales['Sales'].map(fmt_inr),
    textposition='outside',
    cliponaxis=False,
))
fig_cities.update_layout(**make_layout('Top 10 cities by sales', height=420, margin_r=80))
fig_cities.update_xaxes(tickformat=',.0f')
fig_cities.update_yaxes(showgrid=False)

# --- Customer Segment Pie ---
fig_segment = go.Figure(go.Pie(
    labels=segment_sales['Segment'],
    values=segment_sales['Sales'],
    hole=0.55,
    marker_colors=[BLUE, TEAL, AMBER],
    textinfo='label+percent',
    textfont_size=12,
))
fig_segment.update_layout(**make_layout('Sales by customer segment', height=320))
fig_segment.update_layout(showlegend=True,
                           legend=dict(orientation='h', y=-0.1, x=0.5,
                                       xanchor='center', font=dict(size=11)))

# --- Correlation Heatmap ---
cv  = ['Sales', 'Profit', 'Discount', 'Quantity']
z   = corr_df.values.round(2).tolist()
fig_heatmap = go.Figure(go.Heatmap(
    z=z, x=cv, y=cv,
    colorscale=[[0, '#A32D2D'], [0.5, '#d5d5d5'], [1, '#185FA5']],
    zmin=-1, zmax=1,
    text=[[f'{v:.2f}' for v in row] for row in z],
    texttemplate='%{text}',
    showscale=True,
    colorbar=dict(thickness=12, len=0.8),
))
fig_heatmap.update_layout(**make_layout('Correlation heatmap', height=360))
fig_heatmap.update_yaxes(autorange='reversed', showgrid=False)
fig_heatmap.update_xaxes(showgrid=False)


# ── 5. DASH COMPONENT HELPERS ────────────────────────────────
CARD_STYLE = {
    'background':    '#fff',
    'border':        '0.5px solid rgba(0,0,0,0.1)',
    'borderRadius':  '14px',
    'padding':       '1rem 1.25rem',
    'marginBottom':  '1.5rem',
}
CFG = {'displayModeBar': False}


def card(children):
    return html.Div(children, style=CARD_STYLE)


def row2(left, right):
    return html.Div(
        [left, right],
        style={'display': 'grid',
               'gridTemplateColumns': '1fr 1fr',
               'gap': '1.5rem',
               'marginBottom': '1.5rem'},
    )


def kpi_card(label, value, sub, color='#888'):
    return html.Div([
        html.P(label, style={'fontSize': '12px', 'color': '#777', 'margin': '0 0 6px'}),
        html.P(value, style={'fontSize': '24px', 'fontWeight': '600',
                             'margin': '0', 'lineHeight': '1'}),
        html.P(sub,   style={'fontSize': '12px', 'color': color, 'margin': '6px 0 0'}),
    ], style={
        'background':   '#ebebea',
        'borderRadius': '10px',
        'padding':      '1.1rem 1.25rem',
        'flex':         '1',
        'minWidth':     '140px',
    })


def insight_row(num, text, bg, fg):
    return html.Div([
        html.Span(str(num), style={
            'fontSize': '11px', 'fontWeight': '600',
            'padding': '2px 9px', 'borderRadius': '6px',
            'background': bg, 'color': fg, 'flexShrink': '0',
        }),
        html.Span(text, style={'fontSize': '13px', 'lineHeight': '1.6'}),
    ], style={'display': 'flex', 'alignItems': 'flex-start', 'gap': '10px'})


# ── 6. APP LAYOUT ────────────────────────────────────────────
app = Dash(__name__)
app.title = 'India Superstore Analytics'

app.layout = html.Div(
    style={
        'fontFamily': "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        'background':  '#f5f5f3',
        'padding':     '2rem',
        'minHeight':   '100vh',
    },
    children=[html.Div(
        style={'maxWidth': '1100px', 'margin': '0 auto'},
        children=[

            # ── Header ──────────────────────────────────────
            html.Div([
                html.Div([
                    html.Span('🇮🇳', style={'fontSize': '28px', 'marginRight': '10px'}),
                    html.H1('India Superstore Analytics',
                            style={'fontSize': '26px', 'fontWeight': '600',
                                   'letterSpacing': '-0.4px', 'margin': '0',
                                   'display': 'inline'}),
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.P(
                    f'Sales performance · 2014–2017 · India market · {total_orders:,} orders · {total_customers} customers',
                    style={'fontSize': '13px', 'color': '#888', 'margin': '6px 0 0'},
                ),
            ], style={'marginBottom': '1.75rem'}),

            # ── KPI Cards ───────────────────────────────────
            html.Div([
                kpi_card('Total sales',
                         f'₹{total_sales/1_00_00_000:.2f} Cr',
                         '+51% over 4 years', '#1a7a54'),
                kpi_card('Total profit',
                         f'₹{total_profit/1_00_000:.0f}L',
                         f'{profit_margin:.1f}% margin', '#1a7a54'),
                kpi_card('Total orders',
                         f'{total_orders:,}',
                         f'{total_customers} customers', '#888'),
                kpi_card('Avg discount',
                         f'{avg_discount:.1f}%',
                         'Margin pressure', '#c0392b'),
            ], style={'display': 'flex', 'gap': '14px',
                      'flexWrap': 'wrap', 'marginBottom': '1.75rem'}),

            # ── Sales & Profit by Category ───────────────────
            row2(
                card(dcc.Graph(figure=fig_cat_sales,  config=CFG)),
                card(dcc.Graph(figure=fig_cat_profit, config=CFG)),
            ),

            # ── Monthly Sales Trend ─────────────────────────
            card(dcc.Graph(figure=fig_monthly, config=CFG)),

            # ── Yearly Sales Trend ──────────────────────────
            card(dcc.Graph(figure=fig_yearly, config=CFG)),

            # ── Sales by Region | Profit vs Discount ────────
            row2(
                card(dcc.Graph(figure=fig_region,  config=CFG)),
                card(dcc.Graph(figure=fig_scatter, config=CFG)),
            ),

            # ── Top 10 States | Top 10 Cities ───────────────
            row2(
                card(dcc.Graph(figure=fig_states, config=CFG)),
                card(dcc.Graph(figure=fig_cities, config=CFG)),
            ),

            # ── Top 10 Customers ────────────────────────────
            card(dcc.Graph(figure=fig_customers, config=CFG)),

            # ── Sales by Sub-Category ───────────────────────
            card(dcc.Graph(figure=fig_subcat, config=CFG)),

            # ── Customer Segment ─────────────────────────────
            card(dcc.Graph(figure=fig_segment, config=CFG)),

            # ── Correlation Heatmap ─────────────────────────
            card(dcc.Graph(figure=fig_heatmap, config=CFG)),

            # ── Key Insights ────────────────────────────────
            card(html.Div([
                html.H2('Key insights', style={
                    'fontSize': '14px', 'fontWeight': '600', 'margin': '0 0 14px',
                }),
                html.Div([
                    insight_row(1,
                        'Technology leads in both sales (₹6.98 Cr) and profit (₹1.21 Cr) — highest-value category by far.',
                        '#dbeafe', '#1e40af'),
                    insight_row(2,
                        'Sales spike sharply in Q4 (Sep–Dec) — November is the single biggest month at ₹2.94 Cr.',
                        '#dbeafe', '#1e40af'),
                    insight_row(3,
                        'Gujarat and Maharashtra are the top two states — together contributing over ₹6 Cr in sales.',
                        '#d1fae5', '#065f46'),
                    insight_row(4,
                        'Discounts above 20% consistently produce negative profit — the biggest margin risk.',
                        '#fef3c7', '#92400e'),
                    insight_row(5,
                        'Meera Nair is the top customer at ₹20.91L — top 10 customers show high revenue concentration.',
                        '#fef3c7', '#92400e'),
                    insight_row(6,
                        'Furniture has a razor-thin 2.5% margin vs Technology\'s 17.4% — Tables sub-category runs at a net loss.',
                        '#fee2e2', '#991b1b'),
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),
            ])),

            # ── Footer ──────────────────────────────────────
            html.P(
                'Data: India Superstore · 2014–2017 · Currency in INR (₹) · 1 USD = ₹83.5',
                style={'fontSize': '11px', 'color': '#aaa',
                       'textAlign': 'center', 'marginTop': '1rem'}
            ),

        ]
    )]
)

# ── 7. RUN ───────────────────────────────────────────────────
if __name__ == '__main__':
    Timer(1, lambda: webbrowser.open('http://127.0.0.1:8050')).start()
    app.run(debug=False)
