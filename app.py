from pyairtable import Table
import pandas as pd
import plotly.graph_objects as go
import datetime
import plotly.offline as pyo
import requests
from requests.auth import HTTPBasicAuth

# Configuración
api_key = 'patwzUJdBTJiYQrlc.01d208baf2de8f8d7aebc4572ca13165c1a5f5bf80d24cc89eb0b5faa4b542c9'
base_id = 'appKQ9kJIdZBsApeF'
table_name = 'tblydD1afp6lS0ngt'

# Conectar a la tabla
table = Table(api_key, base_id, table_name)

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

# Crear los colores basados en el porcentaje de "Ass. atencions"
def get_fill_color(value, color):
    color_scale = {
        'red': [(255, 200, 200), (255, 0, 0)],
        'blue': [(200, 200, 255), (0, 0, 255)],
        'green': [(200, 255, 200), (0, 255, 0)]
    }
    base_color, fill_color = color_scale[color]
    if value == 0:
        return f'rgb{base_color}'
    elif value == 1:
        return f'rgb{fill_color}'
    else:
        red = base_color[0] + (fill_color[0] - base_color[0]) * value
        green = base_color[1] + (fill_color[1] - base_color[1]) * value
        blue = base_color[2] + (fill_color[2] - base_color[2]) * value
        red = min(max(0, red), 255)
        green = min(max(0, green), 255)
        blue = min(max(0, blue), 255)
        return f'rgb({int(red)}, {int(green)}, {int(blue)})'

colors = ['red', 'blue', 'green']
df['Base Color'] = [get_fill_color(0, colors[i % len(colors)]) for i in range(len(df))]
df['Fill Color'] = [get_fill_color(row['Ass. atencions'], colors[i % len(colors)]) for i, row in df.iterrows()]

# Crear las barras de Gantt con colores de llenado
fig = go.Figure()

for idx, row in df.iterrows():
    # Barra de fondo
    fig.add_trace(go.Bar(
        x=[row['Finish_norm'] - row['Start_norm']],
        y=[row['ID_Projecte']],
        base=row['Start_norm'],
        orientation='h',
        marker=dict(
            color=row['Base Color'],
            line=dict(color='rgba(0, 0, 0, 1.0)', width=1)
        ),
        width=0.5,  # Columna más fina
        showlegend=True,
        hoverinfo='skip',
        name=f'Project {row["ID_Projecte"]}'
    ))
    
    # Barra de llenado
    fill_width = (row['Finish_norm'] - row['Start_norm']) * row['Ass. atencions']
    fig.add_trace(go.Bar(
        x=[fill_width],
        y=[row['ID_Projecte']],
        base=row['Start_norm'],
        orientation='h',
        marker=dict(
            color=row['Fill Color'],
            line=dict(color='rgba(0, 0, 0, 1.0)', width=1)
        ),
        width=0.5,  # Columna más fina
        showlegend=False,
        hoverinfo='y+x',
        text=f'{row["ID_Projecte"]} - {row["Ass. atencions"]*100:.0f}%'
    ))

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

# Diccionario de meses en catalán
mesos_cat = {
    1: 'gen', 2: 'feb', 3: 'març', 4: 'abr', 5: 'maig', 6: 'juny',
    7: 'jul', 8: 'ag', 9: 'set', 10: 'oct', 11: 'nov', 12: 'des'
}

# Función para formatear la fecha en catalán
def format_date_cat(date):
    return f"{mesos_cat[date.month]}_{date.year % 100}"

# Marcar con una rallita cada mes
months = pd.date_range(start=min_date, end=max_date, freq='MS')
month_ticks = [(month - min_date) / (max_date - min_date) * 100 for month in months]
month_labels = [format_date_cat(month) for month in months]

fig.update_layout(
    title='Projectes4',
    xaxis=dict(
        title='Data',
        tickmode='array',
        tickvals=month_ticks,
        ticktext=month_labels,
        tickangle=45  # Inclina las etiquetas para mejor legibilidad
    ),
    yaxis=dict(
        title='ID Projecte'
    ),
    barmode='overlay',
    bargap=0.1,
    bargroupgap=0.1
)

# Guardar el gráfico como un archivo HTML
html_file_path = 'grafico_proyectos_git.html'
pyo.plot(fig, filename=html_file_path, auto_open=False)

#########
# Configuración de Nextcloud
nextcloud_url = 'https://peregirona.hopto.org/remote.php/webdav/00.SocialData/Indicadors/grafico_proyectos_git.html'
nextcloud_user = 'ncp'  # Cambia esto por tu usuario de Nextcloud
nextcloud_password = 'serral84'  # Cambia esto por tu contraseña de Nextcloud

# Guardar el gráfico como un archivo HTML
html_file_path = 'grafico_proyectos_git.html'
pyo.plot(fig, filename=html_file_path, auto_open=False)

# Subir el archivo HTML a Nextcloud
with open(html_file_path, 'rb') as file:
    try:
        response = requests.put(nextcloud_url, data=file, auth=HTTPBasicAuth(nextcloud_user, nextcloud_password))
        
        # Comprobar si la subida fue exitosa
        if response.status_code in (201, 204):
            print("El archivo se ha subido correctamente a Nextcloud.")
        else:
            print(f"Error al subir el archivo: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Ocurrió un error al intentar subir el archivo: {e}")

######
