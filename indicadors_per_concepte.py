#!/usr/bin/env python
# coding: utf-8

# In[2]:


from pyairtable import Table
import pandas as pd
import plotly.graph_objects as go
import datetime
import plotly.offline as pyo
import requests
from requests.auth import HTTPBasicAuth
from plotly.subplots import make_subplots
import dash
from dash import Dash, dcc, html, Input, Output


# Config2uración
api_key = os.environ['AIRTABLE_API_KEY']
base_id = 'appKQ9kJIdZBsApeF'
table_name = 'tblydD1afp6lS0ngt'

# Conectar a la tabla
table = Table(api_key, base_id, table_name)

# Obtener todos los registros
records = table.all()

# Convertir los registros a un DataFrame de pandas
df = pd.DataFrame([record['fields'] for record in records])


# In[3]:


import pandas as pd

# Creamos un nuevo DataFrame vacío para almacenar los resultados transformados
df_transformed = pd.DataFrame(columns=['ID_Projecte', 'Indicador', 'Quantitat', 'Objectiu', 'Ass.', 'Data inici', 'Data fi'])

# Función para generar las columnas a partir de una palabra clave
def generar_columnas(base):
    return [
        'ID_Projecte',
        f'Objectiu {base}',
        f'Quantitat {base}',
        f'Ass. {base}',
        'Data inici',
        'Data fi'
    ]

# Definimos los indicadores y sus columnas correspondientes
indicadores = {
    'Atencions': generar_columnas('atencions'),
    'Insercions': generar_columnas('insercions'),
    'Activitats': generar_columnas('activitats'),
    #'Altes': generar_columnas('altes')  # Asegúrate de que 'Objectiu altes', 'Quantitat altes', etc. estén en df
}

# Función para agregar un nuevo DataFrame al DataFrame transformado
def agregar_indicador(df, indicador, columnas):
    temp_df = df[columnas]
    temp_df.columns = ['ID_Projecte', 'Objectiu', 'Quantitat', 'Ass.', 'Data inici', 'Data fi']
    temp_df['Indicador'] = indicador
    return temp_df

# Agregamos cada indicador al DataFrame transformado
for indicador, columnas in indicadores.items():
    df_transformed = pd.concat([df_transformed, agregar_indicador(df, indicador, columnas)], ignore_index=True)

# Reordenamos las columnas
df_transformed = df_transformed[['ID_Projecte', 'Indicador', 'Quantitat', 'Objectiu', 'Ass.', 'Data inici', 'Data fi']]


# In[12]:


import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
import datetime

# Asumimos que df_transformed ya está definido como en el código original

df = df_transformed
# Convertir las columnas de fecha a formato datetime
df['Data inici'] = pd.to_datetime(df['Data inici'])
df['Data fi'] = pd.to_datetime(df['Data fi'])

# Filtrar proyectos cuya fecha final es posterior a hoy
today = datetime.datetime.today()
df = df[df['Data fi'] > today]

# Ordenar por fecha de inicio
df = df.sort_values(by='Data inici')

# Obtener la fecha de inicio más antigua y la fecha de fin más reciente
min_date = df['Data inici'].min()
max_date = df['Data fi'].max()

# Normalizar las fechas al rango [0, 100]
df['Start_norm'] = ((df['Data inici'] - min_date) / (max_date - min_date)) * 100
df['Finish_norm'] = ((df['Data fi'] - min_date) / (max_date - min_date)) * 100

# Lista de colores que deseas asignar
color_list = ['#66c5cc', '#f6cf71', '#f89c74', '#4bedf3', '#d6a4e9', '#48ffa7', '#ffb1c1', '#8cd3f7', '#f6c992', '#94ecf1', '#ffe281', '#c4f4cd']

# Diccionario para almacenar el color correspondiente a cada ID_Projecte
color_map = {}

# Función para asignar colores automáticamente a los ID_Projecte
def assign_colors(df):
    # Obtener los valores únicos de la columna 'ID_Projecte'
    unique_ids = df['ID_Projecte'].unique()
    # Asignar un color de la lista para cada ID único
    for i, id_projecte in enumerate(unique_ids):
        if id_projecte not in color_map:
            color_map[id_projecte] = color_list[i % len(color_list)]
    return color_map

# Asignar colores automáticamente a los valores en 'ID_Projecte'
color_map = assign_colors(df)

# Función para obtener un color más oscuro
def darken_color(color, factor=0.7):
    r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

# Definir el rango del eje x para todos los gráficos
xaxis_range = [0, 100]  # Esto se basa en la normalización [0, 100] en tu código

def create_gantt_chart(df_subset):
    fig = go.Figure()

    for idx, row in df_subset.iterrows():
        project_name = f'{row["ID_Projecte"]}'
        base_color = color_map.get(row['ID_Projecte'], '#b3b3b3')
        fill_color = darken_color(base_color)

        # Barra de fondo
        fig.add_trace(go.Bar(
            x=[row['Finish_norm'] - row['Start_norm']],
            y=[row['ID_Projecte']],
            base=row['Start_norm'],
            orientation='h',
            marker=dict(
                color=base_color,
                line=dict(color='rgba(0, 0, 0, 1.0)', width=1)
            ),
            width=0.5,
            showlegend=True,
            legendgroup=project_name,
            hoverinfo='text',
            text=row["Objectiu"],
            name=project_name,
            hovertext='Objectiu',
            visible=True
        ))

        # Barra de llenado
        fill_width = (row['Finish_norm'] - row['Start_norm']) * min(row['Ass.'], 1.0)

        # Verificar si Quantitat es igual o superior a Objectiu
        if row['Quantitat'] >= row['Objectiu']:
            pattern_color = '#3AFF00'
            pattern = '/'  # Patrón de líneas diagonales
        else:
            pattern_color = fill_color
            pattern = ''  # Sin patrón
        
        fig.add_trace(go.Bar(
            x=[fill_width],
            y=[row['ID_Projecte']],
            base=row['Start_norm'],
            orientation='h',
            marker=dict(
                color=fill_color,
                line=dict(color='rgba(0, 0, 0, 1.0)', width=1),
                pattern=dict(
                    shape=pattern,
                    fgcolor=pattern_color,
                    size=16,
                    solidity=0.3
                )
            ),
            width=0.5,
            showlegend=False,
            legendgroup=project_name,
            hoverinfo='text',
            text=f'{row["Quantitat"]}',
            hovertext='Quantitat',
            visible=True
        ))

    # Diccionario de meses en catalán
    mesos_cat = {
        1: 'gen', 2: 'feb', 3: 'març', 4: 'abr', 5: 'maig', 6: 'juny',
        7: 'jul', 8: 'ag', 9: 'set', 10: 'oct', 11: 'nov', 12: 'des'
    }

    # Agregar línea discontinua para la fecha de hoy
    today_norm = ((today - min_date) / (max_date - min_date)) * 100

    fig.add_shape(
        go.layout.Shape(
            type="line",
            x0=today_norm, x1=today_norm,
            y0=0, y1=1,
            xref='x', yref='paper',
            line=dict(color="black", width=1, dash="dash")
        )
    )

    # Añadir una traza invisible para la leyenda con la línea discontinua
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode='lines',
            line=dict(color="black", width=1, dash="dash"),
            name='Avui',
            showlegend=True
        )
    )

    # Función para formatear la fecha en catalán
    def format_date_cat(date):
        return f"{mesos_cat[date.month]}_{date.year % 100}"

    # Marcar con una rallita cada mes
    months = pd.date_range(start=min_date, end=max_date, freq='MS')
    month_ticks = [(month - min_date) / (max_date - min_date) * 100 for month in months]
    month_labels = [format_date_cat(month) for month in months]

    fig.update_layout(
        title=f'{df_subset["Indicador"].iloc[0]}',
        xaxis=dict(
            tickmode='array',
            tickvals=month_ticks,
            ticktext=month_labels,
            tickangle=45,
            range=xaxis_range,
            tickformat='d'
        ),
        yaxis=dict(
            title='',
            categoryorder='array',
            categoryarray=df_subset['ID_Projecte'][::-1].tolist()
        ),
        barmode='overlay',
        bargap=0.1,
        bargroupgap=0.1,
        showlegend=True,
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig

# Función para crear la tabla
def create_table(df_subset, indicator):
    # Formatear el título del indicador
    title_html = f"<h3>{indicator}</h3>\n"
    
    # Generar la tabla manualmente
    table_html = "<table><thead><tr>"
    for col in ['ID_Projecte', 'Quantitat', 'Objectiu']:
        table_html += f"<th>{col}</th>"
    table_html += "</tr></thead><tbody>"
    
    for i, (_, row) in enumerate(df_subset.iterrows()):
        bg_color = '#ffffff' if i % 2 == 0 else '#f9f9f9'
        project_color = color_map.get(row['ID_Projecte'], '#ffffff')
        table_html += f"<tr style='background-color: {bg_color}; color: #000000'>"
        table_html += f"<td><span style='display: inline-block; width: 10px; height: 10px; background-color: {project_color}; margin-right: 5px;'></span>{row['ID_Projecte']}</td>"
        for col in ['Quantitat', 'Objectiu']:
            table_html += f"<td>{row[col]}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"

    # Crear el botón de descarga CSV
    button_html = f'''
    <button onclick="downloadCSV('{indicator}')">Descarregar dades</button>
    <script>
    function downloadCSV(indicator) {{
        var csv = 'ID_Projecte,Quantitat,Objectiu\\n';
        var rows = {df_subset[['ID_Projecte', 'Quantitat', 'Objectiu']].to_numpy().tolist()};
        rows.forEach(function(row) {{
            csv += row.join(',') + '\\n';
        }});
        var hiddenElement = document.createElement('a');
        hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);
        hiddenElement.target = '_blank';
        hiddenElement.download = indicator + '.csv';
        hiddenElement.click();
    }}
    </script>
    '''

   # Devolver el título del indicador, las fechas, la tabla y el botón
    return title_html + table_html + button_html

# Inicializar el archivo HTML
html_file_path = 'docs/indicadors_per_concepte.html'

# Crear una lista para almacenar el contenido HTML
html_content = []

# Agregar encabezado HTML con CSS
html_content.append('''
<html>
<head>
    <title>Indicadors per Projecte (Invertit)</title>
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
        }
        
        th, td {
            font-size: 12px;
            padding: 8px;
            border: 1px solid #ddd;
            text-align: left;
        }
        
        th {
            background-color: #f4f4f4;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .grid-container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        
        .indicator-section {
            display: contents;
        }
        
        .chart-container, .table-container {
            width: 100%;
        }
        
        .chart-container {
            height: 500px;
        }
        
        .table-container {
            overflow-x: auto;
        }
    </style>
</head>
<body>
''')

# Agregar el HTML para la selección de indicadores
html_content.append('''
<form id="indicator-select-form" onsubmit="filterIndicators(); return false;">
    <label for="indicator-select">Selecciona Indicadors:</label>
    <select id="indicator-select" name="indicators" multiple>
''')

# Agregar las opciones al <select>
for indicator in df['Indicador'].unique():
    html_content.append(f'<option value="{indicator}" selected>{indicator}</option>')

# Cerrar el select y añadir el botón de aplicar
html_content.append('''
    </select>
    <button type="submit">Aplicar</button>
</form>
''')

# Contenedor para todos los indicadores
html_content.append('<div id="indicators-container" class="grid-container">')

# Iterar sobre los indicadores para crear el contenido
indicators = df['Indicador'].unique()
for indicator in indicators:
    df_filtered = df[df['Indicador'] == indicator]
    
    # Crear el gráfico
    fig_gantt = create_gantt_chart(df_filtered)
    gantt_html = pio.to_html(fig_gantt, full_html=False, include_plotlyjs='cdn')
    
    # Crear la tabla
    table_html_with_button = create_table(df_filtered, indicator)
    
    # Agregar el contenido del indicador
    html_content.append(f'<div class="indicator-section" data-indicator="{indicator}">')
    html_content.append(f'<div class="chart-container">{gantt_html}</div>')
    html_content.append(f'<div class="table-container">{table_html_with_button}</div>')
    html_content.append('</div>')

html_content.append('</div>')  # Cerrar el contenedor de indicadores

# Agregar el script de JavaScript para el filtrado y reorganización
html_content.append('''
<script>
function filterIndicators() {
    var selectedIndicators = Array.from(document.getElementById("indicator-select").selectedOptions).map(option => option.value);
    var container = document.getElementById("indicators-container");
    var elements = Array.from(container.querySelectorAll(".indicator-section"));
    
    // Si no hay indicadores seleccionados, mostrar todos
    if (selectedIndicators.length === 0) {
        elements.forEach(function(element) {
            element.style.display = "block";
        });
        return;
    }
    
    // Ocultar todos los indicadores
    elements.forEach(function(element) {
        element.style.display = "none";
    });
    
    // Mostrar y reorganizar los indicadores seleccionados
    var visibleElements = elements.filter(function(element) {
        return selectedIndicators.includes(element.getAttribute("data-indicator"));
    });
    
    visibleElements.forEach(function(element, index) {
        element.style.display = "block";
        container.appendChild(element);  // Esto mueve el elemento al final del contenedor
    
    });
}

// Llamar a filterIndicators al cargar la página para mostrar todos los indicadores inicialmente
window.onload = filterIndicators;
</script>
''')

# Agregar cierre de etiquetas HTML
html_content.append('</body></html>\n')

# Escribir todo el contenido HTML en el archivo
with open(html_file_path, 'w') as f:
    f.writelines(html_content)

print(f"El archivo HTML invertido ha sido generado en: {html_file_path}")


# In[ ]:




