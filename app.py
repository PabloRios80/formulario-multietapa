import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Para manejar sesiones

def init_db():
    """Inicializa la base de datos y crea las tablas necesarias."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Tabla de usuarios (cargadores de datos)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT -- 'admin', 'cargador', 'profesional', etc.
    )
    ''')

    # Tabla de profesionales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS profesionales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        apellido TEXT,
        especialidad TEXT,
        telefono TEXT
    )
    ''')

    # Tabla de prestadores
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prestadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        servicio TEXT,  -- Tipo de servicio: mamografía, videocolonoscopia, etc.
        direccion TEXT,
        telefono TEXT
    )
    ''')

    # Tabla de usuarios
    cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    dni TEXT PRIMARY KEY,
    nombre TEXT,
    apellido TEXT,
    telefono TEXT,
    profesional TEXT,
    especialidad TEXT,
    fecha_turno TEXT,
    hora_turno TEXT,
    modalidad_paciente TEXT,
    antiguedad TEXT,
    hpv TEXT,
    somf TEXT,
    mamografia TEXT CHECK(mamografia IN ('si', 'no', 'pendiente')),
    laboratorio TEXT CHECK(laboratorio IN ('si', 'no', 'pendiente')),
    agudeza_visual TEXT CHECK(agudeza_visual IN ('si', 'no', 'pendiente')),
    espirometria TEXT CHECK(espirometria IN ('si', 'no', 'pendiente')),
    densitometria TEXT CHECK(densitometria IN ('si', 'no', 'pendiente')),
    vcc TEXT CHECK(vcc IN ('si', 'no', 'pendiente'))
)
''')


    conn.commit()
    conn.close()

def agregar_usuarios_iniciales():
    """Agrega usuarios iniciales a la base de datos si no existen."""
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    usuarios = [
        ("user1", "pass1", "admin"),
        ("user2", "pass2", "cargador"),
        ("user3", "pass3", "profesional"),
        ("user4", "pass4", "cargador")
    ]

    for username, password, role in usuarios:
        cursor.execute("SELECT username FROM user_data WHERE username=?", (username,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("INSERT INTO user_data (username, password, role) VALUES (?, ?, ?)", (username, password, role))

    conn.commit()
    conn.close()

# Inicializa la base de datos y agrega usuarios iniciales
init_db()
agregar_usuarios_iniciales()

@app.route('/')
def index():
    """Redirige a la página de inicio de sesión."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja la lógica de inicio de sesión."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password, role FROM user_data WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and user[0] == password:
            session['username'] = username
            session['role'] = user[1]  # Asignamos el rol a la sesión

            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif session['role'] == 'cargador':
                return redirect(url_for('formulario'))
            elif session['role'] == 'profesional':
                return redirect(url_for('profesional_dashboard'))
            else:
                return "Rol no reconocido", 403
        return "Usuario o contraseña incorrectos", 401

    return render_template('login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    """Muestra el panel de administración."""
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html')

@app.route('/admin/agregar_usuario', methods=['GET', 'POST'])
def agregar_usuario():
    """Permite agregar un nuevo usuario."""
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # 'cargador', 'profesional', etc.

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO user_data (username, password, role) 
            VALUES (?, ?, ?)
            ''', (username, password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            return "El nombre de usuario ya existe.", 400
        except sqlite3.Error as e:
            return f"Error en la base de datos: {e}", 500
        finally:
            conn.close()

        return 'Usuario agregado correctamente.'

    return render_template('agregar_usuario.html')

@app.route('/admin/agregar_prestador', methods=['GET', 'POST'])
def agregar_prestador():
    """Permite agregar un nuevo prestador."""
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        nombre = request.form['nombre']
        servicio = request.form['servicio']
        direccion = request.form['direccion']
        telefono = request.form['telefono']

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO prestadores (nombre, servicio, direccion, telefono)
            VALUES (?, ?, ?, ?)
            ''', (nombre, servicio, direccion, telefono))
            conn.commit()
        except sqlite3.Error as e:
            return f"Error en la base de datos: {e}", 500
        finally:
            conn.close()

        return 'Prestador agregado correctamente.'

    return render_template('agregar_prestador.html')

@app.route('/profesional_dashboard')
def profesional_dashboard():
    """Muestra el panel de profesionales."""
    if 'username' not in session or session.get('role') != 'profesional':
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, apellido, especialidad, telefono FROM profesionales")
    profesionales = cursor.fetchall()
    conn.close()

    return render_template('profesional_dashboard.html', profesionales=profesionales)

@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    """Permite a los cargadores de datos ingresar nuevos usuarios."""
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        dni = request.form['dni']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        profesional = request.form['profesional']
        especialidad = request.form['especialidad']
        fecha_turno = request.form['fecha_turno']
        hora_turno = request.form['hora_turno']
        modalidad_paciente = request.form['modalidad_paciente']
        antiguedad = request.form['antiguedad']
        hpv = request.form['hpv']
        somf = request.form['somf']
        mamografia = request.form['mamografia']
        laboratorio = request.form['laboratorio']
        agudeza_visual = request.form['agudeza_visual']
        espirometria = request.form['espirometria']
        densitometria = request.form['densitometria']
        vcc = request.form['vcc']

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Verificar si el DNI ya existe
            cursor.execute("SELECT dni FROM usuarios WHERE dni = ?", (dni,))
            result = cursor.fetchone()

            if result:
                return "El DNI ya está registrado.", 400  # Mensaje de error si el DNI ya existe

            # Insertar datos en la base de datos
            cursor.execute('''
                INSERT INTO usuarios (dni, nombre, apellido, telefono, profesional, especialidad, 
                fecha_turno, hora_turno, modalidad_paciente, antiguedad, hpv, somf,
                mamografia, laboratorio, agudeza_visual, espirometria, densitometria, vcc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (dni, nombre, apellido, telefono, profesional, especialidad, fecha_turno, hora_turno, 
            modalidad_paciente, antiguedad, hpv, somf, mamografia, laboratorio, agudeza_visual, espirometria, densitometria, vcc))
            conn.commit()

        except sqlite3.Error as e:
            return f"Error en la base de datos: {e}", 500

        finally:
            conn.close()

        return 'Datos guardados correctamente.'

    return render_template('formulario.html')


@app.route('/ver_datos')
def ver_datos():
    """Muestra todos los datos ingresados en la tabla usuarios."""
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT dni, nombre, apellido, telefono, profesional, especialidad, fecha_turno, hora_turno, modalidad_paciente, antiguedad, hpv, somf FROM usuarios")
    datos = cursor.fetchall()
    
    conn.close()
    
    return render_template('ver_datos.html', datos=datos)

@app.route('/logout')
def logout():
    """Finaliza la sesión del usuario."""
    session.clear()
    return redirect(url_for('login'))

# Ejecutar para crear la base de datos al iniciar
init_db()

if __name__ == '__main__':
    app.run(debug=True)
