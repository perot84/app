from pyairtable import Table
import pandas as pd
import plotly.graph_objects as go
import datetime
import plotly.offline as pyo
import requests
from requests.auth import HTTPBasicAuth
import os

# Configuración
api_key = os.environ['AIRTABLE_API_KEY']
base_id = 'appKQ9kJIdZBsApeF'
table_name = 'tblydD1afp6lS0ngt'

# Conectar a la tabla y obtener todos los registros
table = Table(api_key, base_id, table_name)
records = table.all()

# Convertir los registros a un DataFrame de pandas
df = pd.DataFrame([record['fields'] for record in records])

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
}

# Función para agregar un nuevo DataFrame al DataFrame transformado
def agregar_indicador(df, indicador, columnas):
    temp_df = df[columnas].copy()
    temp_df.columns = ['ID_Projecte', 'Objectiu', 'Quantitat', 'Ass.', 'Data inici', 'Data fi']
    temp_df['Indicador'] = indicador
    return temp_df

# Creamos un nuevo DataFrame para almacenar los resultados transformados
df_transformed = pd.DataFrame()

# Agregamos cada indicador al DataFrame transformado
for indicador, columnas in indicadores.items():
    df_transformed = pd.concat([df_transformed, agregar_indicador(df, indicador, columnas)], ignore_index=True)

# Reordenamos las columnas
df_transformed = df_transformed[['ID_Projecte', 'Indicador', 'Quantitat', 'Objectiu', 'Ass.', 'Data inici', 'Data fi']]

# Convertir las columnas de fecha a formato datetime
df_transformed['Data inici'] = pd.to_datetime(df_transformed['Data inici'])
df_transformed['Data fi'] = pd.to_datetime(df_transformed['Data fi'])

# Filtrar proyectos cuya fecha final es posterior a hoy
today = datetime.datetime.today()
df_transformed = df_transformed[df_transformed['Data fi'] > today]

# Ordenar por fecha de inicio
df_transformed = df_transformed.sort_values(by='Data inici')

# Obtener la fecha de inicio más antigua y la fecha de fin más reciente
min_date = df_transformed['Data inici'].min()
max_date = df_transformed['Data fi'].max()

# Normalizar las fechas al rango [0, 100]
df_transformed['Start_norm'] = ((df_transformed['Data inici'] - min_date) / (max_date - min_date)) * 100
df_transformed['Finish_norm'] = ((df_transformed['Data fi'] - min_date) / (max_date - min_date)) * 100

# Define colores fijos para cada tipo de indicador
color_map = {
    'Atencions': '#66c5cc',
    'Insercions': '#f6cf71',
    'Activitats': '#f89c74'
}

# Función para obtener un color más oscuro
def darken_color(color, factor=0.7):
    r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

# Definir el rango del eje x para todos los gráficos
xaxis_range = [0, 100]

def create_gantt_chart(df_subset, project_id):
    fig = go.Figure()

    for idx, row in df_subset.iterrows():
        project_name = f'{row["Indicador"]}'
        indicator_type = row['Indicador']
        base_color = color_map.get(indicator_type, '#b3b3b3')
        fill_color = darken_color(base_color)

        # Barra de fondo
        fig.add_trace(go.Bar(
            x=[row['Finish_norm'] - row['Start_norm']],
            y=[row['Indicador']],
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
            y=[row['Indicador']],
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
        title=f'{project_id}',
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
            categoryarray=df_subset['Indicador'][::-1].tolist()
        ),
        barmode='overlay',
        bargap=0.1,
        bargroupgap=0.1,
        showlegend=True,
        height=500
    )

    fig.update_layout(
        legend=dict(
            itemclick="toggle",
            itemdoubleclick="toggle"
        )
    )
    
    return fig

# Función para crear la tabla
def create_table(df_subset, project_id):
    fecha_inicio = df_subset['Data inici'].min().strftime('%d/%m/%Y')
    fecha_fin = df_subset['Data fi'].max().strftime('%d/%m/%Y')

    title_html = f"<h3>{project_id}</h3>\n"
    fecha_html = f"<p><strong>Data inici:</strong> {fecha_inicio} | <strong>Data fi:</strong> {fecha_fin}</p>\n"
    
    table_html = "<table><thead><tr>"
    for col in ['Indicador', 'Quantitat', 'Objectiu']:
        table_html += f"<th>{col}</th>"
    table_html += "</tr></thead><tbody>"
    
    for _, row in df_subset.iterrows():
        table_html += "<tr>"
        for col in ['Indicador', 'Quantitat', 'Objectiu']:
            table_html += f"<td>{row[col]}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"

    button_html = f'''
    <button onclick="downloadCSV('{project_id}')">Descarregar dades</button>
    <script>
    function downloadCSV(projectId) {{
        var csv = 'Indicador,Quantitat,Objectiu\\n';
        var rows = {df_subset[['Indicador', 'Quantitat', 'Objectiu']].to_numpy().tolist()};
        rows.forEach(function(row) {{
            csv += row.join(',') + '\\n';
        }});
        var hiddenElement = document.createElement('a');
        hiddenElement.href = 'data:text/csv;charset=utf-8,' + encodeURI(csv);
        hiddenElement.target = '_blank';
        hiddenElement.download = projectId + '.csv';
        hiddenElement.click();
    }}
    </script>
    '''

    return title_html + fecha_html + table_html + button_html

# Inicializar el archivo HTML
html_file_path = 'docs/indicadors_per_projecte.html'

# Crear una lista para almacenar el contenido HTML
html_content = []

# Agregar encabezado HTML con CSS
html_content.append('''
<html>
<head>
    <title>Indicadors per Projecte</title>
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
        
        .project-section {
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

# Agregar el HTML para la selección de proyectos
html_content.append('''
<form id="project-select-form" onsubmit="filterProjects(); return false;">
    <label for="project-select">Selecciona Proyectos:</label>
    <select id="project-select" name="projects" multiple>
''')

# Agregar las opciones al <select>
for project_id in df_transformed['ID_Projecte'].unique():
    html_content.append(f'<option value="{project_id}" selected>{project_id}</option>')

# Cerrar el select y añadir el botón de aplicar
html_content.append('''
    </select>
    <button type="submit">Aplicar</button>
</form>
''')

# Contenedor para todos los proyectos
html_content.append('<div id="projects-container" class="grid-container">')

# Iterar sobre los proyectos para crear el contenido
project_ids = df_transformed['ID_Projecte'].unique()
for project_id in project_ids:
    df_filtered = df_transformed[df_transformed['ID_Projecte'] == project_id].drop(columns=['ID_Projecte'])
    
    # Crear el gráfico
    fig_gantt = create_gantt_chart(df_filtered, project_id)
    gantt_html = pio.to_html(fig_gantt, full_html=False, include_plotlyjs='cdn')
    
    # Crear la tabla
    table_html_with_button = create_table(df_filtered, project_id)
    
    # Agregar el contenido del proyecto
    html_content.append(f'<div class="project-section" data-project-id="{project_id}">')
    html_content.append(f'<div class="chart-container">{gantt_html}</div>')
    html_content.append(f'<div class="table-container">{table_html_with_button}</div>')
    html_content.append('</div>')

html_content.append('</div>')  # Cerrar el contenedor de proyectos

# Agregar el script de JavaScript para el filtrado y reorganización
html_content.append('''
<script>
function filterProjects() {
    var  selectedProjects = Array.from(document.getElementById("project-select").selectedOptions).map(option => option.value);
    var container = document.getElementById("projects-container");
    var elements = Array.from(container.querySelectorAll(".project-section"));
    
    // Si no hay proyectos seleccionados, mostrar todos
    if (selectedProjects.length === 0) {
        elements.forEach(function(element) {
            element.style.display = "contents";
        });
        return;
    }
    
    // Ocultar todos los proyectos
    elements.forEach(function(element) {
        element.style.display = "none";
    });
    
    // Mostrar y reorganizar los proyectos seleccionados
    var visibleElements = elements.filter(function(element) {
        return selectedProjects.includes(element.getAttribute("data-project-id"));
    });
    
    visibleElements.forEach(function(element, index) {
        element.style.display = "contents";
        container.appendChild(element);  // Esto mueve el elemento al final del contenedor
    });
}

// Llamar a filterProjects al cargar la página para mostrar todos los proyectos inicialmente
window.onload = filterProjects;
</script>
''')

# Agregar cierre de etiquetas HTML
html_content.append('</body></html>\n')

# Escribir todo el contenido HTML en el archivo
with open(html_file_path, 'w', encoding='utf-8') as f:
    f.writelines(html_content)

print(f"El archivo HTML ha sido generado en: {html_file_path}")
