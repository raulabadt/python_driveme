from flask import Flask, request, jsonify
import requests
import pymysql
from datetime import datetime
from flask_cors import CORS
import configparser

app = Flask(__name__)
CORS(app)

# Función para conectarse a la base de datos
def connect_db():
    config = configparser.ConfigParser()
    config.read('config.ini')

    host = config['default']['host']
    username = config['default']['username']
    password = config['default']['password']
    db_name = config['default']['db_name']

    try:
        # Conectar a la base de datos
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Conexión a la base de datos establecida correctamente.")
        return connection
    except pymysql.Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

@app.route('/guardar-clima', methods=['GET', 'POST'])
def guardar_clima():
    if request.method == 'POST':
        lat = request.form.get('lat')
        lon = request.form.get('lon')

        if lat is None or lon is None:
            return jsonify({'error': 'Faltan datos de latitud y/o longitud en la solicitud'}), 400

        # Consultar la API de OpenWeatherMap
        api_key = 'fe18e4ee1578782f0e81d5783229a1fb'
        url = f'http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}'

        response = requests.get(url)
        data = response.json()

        # Conectar a la base de datos
        connection = connect_db()
        if connection is None:
            return jsonify({'error': 'No se pudo conectar a la base de datos'}), 500

        # Obtener los datos necesarios de la respuesta de la API de OpenWeatherMap
        try:
            temperatura = data['main']['temp']
            humedad = data['main']['humidity']
            velocidad_viento = data['wind']['speed']
            descripcion = data['weather'][0]['description']
            url_icono = f"http://openweathermap.org/img/wn/{data['weather'][0]['icon']}.png"
        except KeyError as e:
            return jsonify({'error': f'Error al obtener datos de la API: {e}'}), 500

        # Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Preparar la consulta SQL para insertar los datos en la tabla 'clima'
        sql = "INSERT INTO clima (fecha, latitud, longitud, temperatura, humedad, velocidad_viento, descripcion, url_icono) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        valores = (fecha_actual, lat, lon, temperatura, humedad, velocidad_viento, descripcion, url_icono)

        # Ejecutar la consulta SQL
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, valores)
                connection.commit()
            print("Datos climáticos guardados correctamente en la base de datos.")
        except pymysql.Error as e:
            print("Error al guardar datos en la base de datos:", e)
            return jsonify({'error': 'Error al guardar datos en la base de datos'}), 500

        # Cerrar la conexión a la base de datos
        connection.close()

        return jsonify({'message': 'Datos climáticos guardados correctamente'})
    else:
        return jsonify({'error': 'Método no permitido'}), 405

if __name__ == '__main__':
    app.run(debug=True)
