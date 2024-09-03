from pyairtable import Table
import pandas as pd
import plotly.graph_objects as go
import datetime
import plotly.offline as pyo
import requests
from requests.auth import HTTPBasicAuth
import os

API_KEY = os.environ['AIRTABLE_API_KEY']

# Configuración
#API_KEY = 'AIRTABLE_API_KEY'
base_id = 'appKQ9kJIdZBsApeF'
table_name = 'tblydD1afp6lS0ngt'

# Conectar a la tabla
table = Table(API_KEY, base_id, table_name)

# Obtener todos los registros
records = table.all()

# Convertir los registros a un DataFrame de pandas
df = pd.DataFrame([record['fields'] for record in records])

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

# Definir una lista de colores manualmente
color_list = [
    '#66c5cc',  
    '#f6cf71',  
    '#f89c74',  
    '#dcb0f2',  
    '#9eb9f3', 
    '#fe88b1',  
    '#c9db74',  
    '#8be0a4',
    '#b497e7',
    '#d3b484',
    '#b3b3b3',
    # Agrega más colores según sea necesario
]

# Función para obtener un color más oscuro
def darken_color(color, factor=0.7):
    r, g, b = [int(color[i:i+2], 16) for i in (1, 3, 5)]
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f'#{r:02x}{g:02x}{b:02x}'

# Crear las barras de Gantt con colores de llenado
fig = go.Figure()

# Asignar colores automáticamente a los proyectos
for idx, row in df.iterrows():
    project_name = f'{row["ID_Projecte"]}'
    
    # Asignar color de la lista en función del índice
    base_color = color_list[idx % len(color_list)]  # Asignar color cíclicamente
    fill_color = darken_color(base_color)  # Color más oscuro para la barra de llenado
    
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
        width=0.5,  # Columna más fina
        showlegend=True,  # Mostrar en la leyenda
        legendgroup=project_name,  # Agrupar con la barra de llenado
        hoverinfo='text',
        text=row["Objectiu atencions"],
        name=project_name,
        hovertext='Objectiu',
        visible=True
    ))
    
    # Barra de llenado
    fill_width = (row['Finish_norm'] - row['Start_norm']) * min(row['Ass. atencions'], 1.0)
    fig.add_trace(go.Bar(
        x=[fill_width],
        y=[row['ID_Projecte']],
        base=row['Start_norm'],
        orientation='h',
        marker=dict(
            color=fill_color,
            line=dict(color='rgba(0, 0, 0, 1.0)', width=1)
        ),
        width=0.5,  # Columna más fina
        showlegend=False,  # No mostrar en la leyenda (ya está la barra de fondo)
        legendgroup=project_name,  # Agrupar con la barra de fondo
        hoverinfo='text',  # Muestra tanto la info de 'y' como 'text' en el hover
        text=f'{row["Quantitat atencions"]}',  # Información que aparece en la barra
        hovertext = 'Ateses',
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
        x=[None],  # No mostrar puntos en el eje x
        y=[None],  # No mostrar puntos en el eje y
        mode='lines',  # Modo de la traza
        line=dict(color="black", width=1, dash="dash"),  # Estilo de la línea
        name='Avui',  # Nombre que aparecerá en la leyenda
        showlegend=True  # Asegúrate de que se muestre en la leyenda
    )
)

# Añadir un texto adicional en la leyenda
fig.add_trace(
    go.Scatter(
        x=[None],  # No mostrar puntos en el eje x
        y=[None],  # No mostrar puntos en el eje y
        mode='text',  # Modo de la traza
        text=[''],  # Texto que se mostrará
        showlegend=False  # Asegúrate de que se muestre en la leyenda
          # Nombre vacío para evitar duplicados
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
    title='Persones ateses',
    xaxis=dict(
        tickmode='array',
        tickvals=month_ticks,
        ticktext=month_labels,
        tickangle=45  # Inclina las etiquetas para mejor legibilidad
    ),
    yaxis=dict(
        categoryorder='array',  # Orden basado en un array
        categoryarray=df['ID_Projecte'][::-1].tolist()  # Preserva el orden del DataFrame
    ),
    barmode='overlay',
    bargap=0.1,
    bargroupgap=0.1,
    showlegend=True,  # Habilitar la leyenda
    
)

# Actualizar el layout para que solo se muestren los proyectos seleccionados en la leyenda
fig.update_layout(
    legend=dict(
        itemclick="toggle",
        itemdoubleclick="toggle"
    )
)
fig_persones_ateses=fig
fig_persones_ateses.show()


# Guardar el gráfico como un archivo HTML en tu repositorio de GitHub
html_file_path = 'docs/grafico_proyectos_git.html'
pyo.plot(fig, filename=html_file_path, auto_open=False)

