import json
import random
import datetime
from faker import Faker

# --- Configuración ---
FAKER_LOCALE = 'es_MX'  # Usar datos para México
NUM_CLIENTES_TOTAL = 100
MIN_TRANS_POR_CUENTA = 10
MAX_TRANS_POR_CUENTA = 50
FECHA_INICIO = datetime.date(2025, 1, 1)
FECHA_FIN = datetime.date(2025, 10, 26)

# Archivos de entrada
CLIENTES_IN_FILE = 'Clientes.json'
CUENTAS_IN_FILE = 'Cuentas.json'

# Archivos de salida
CLIENTES_OUT_FILE = 'Clientes_100.json'
CUENTAS_OUT_FILE = 'Cuentas_100.json'
TRANSACCIONES_OUT_FILE = 'Transacciones_Completas.json'

# --- Inicialización ---
fake = Faker(FAKER_LOCALE)
random.seed(42) # Para resultados reproducibles

# --- Funciones Auxiliares ---

def cargar_json(filename):
    """Carga datos desde un archivo JSON."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Advertencia: No se encontró el archivo {filename}. Se creará una lista vacía.")
        return []
    except json.JSONDecodeError:
        print(f"Error: El archivo {filename} está mal formateado.")
        return []

def guardar_json(data, filename):
    """Guarda datos en un archivo JSON."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Archivo guardado: {filename}")

def generar_fecha_aleatoria(start, end):
    """Genera una fecha aleatoria en el rango especificado."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + datetime.timedelta(days=random_days)).isoformat()

def crear_cliente_fake(user_id):
    """Crea un nuevo cliente ficticio."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    return {
        "username": f"user{user_id}",
        "password": fake.password(length=8),
        "firstName": first_name,
        "lastName": last_name,
        "address": {
            "streetNumber": fake.building_number(),
            "streetName": fake.street_name(),
            "city": fake.city(),
            "state": fake.state(),
            "country": "México"
        }
    }

def crear_cuenta_fake(user_id, account_num):
    """Crea una nueva cuenta ficticia."""
    return {
        "numeroCuenta": account_num,
        "idCliente": f"user{user_id}",
        "tipoCuenta": random.choice(["Ahorro", "Corriente"]),
        "balance": 0.0  # Se calculará después
    }

# --- 1. Generar Clientes y Cuentas ---

print("Iniciando generación de datos...")

clientes_data = cargar_json(CLIENTES_IN_FILE)
cuentas_data = cargar_json(CUENTAS_IN_FILE)

num_clientes_actuales = len(clientes_data)
num_cuentas_actuales = len(cuentas_data)

if num_clientes_actuales < NUM_CLIENTES_TOTAL:
    print(f"Generando {NUM_CLIENTES_TOTAL - num_clientes_actuales} clientes nuevos...")
    for i in range(num_clientes_actuales + 1, NUM_CLIENTES_TOTAL + 1):
        # Crear cliente
        nuevo_cliente = crear_cliente_fake(i)
        clientes_data.append(nuevo_cliente)
        
        # Crear cuenta (asumiendo que el numeroCuenta es 10000 + i)
        nuevo_numero_cuenta = 10000 + i
        nueva_cuenta = crear_cuenta_fake(i, nuevo_numero_cuenta)
        cuentas_data.append(nueva_cuenta)

print(f"Total de clientes: {len(clientes_data)}")
print(f"Total de cuentas: {len(cuentas_data)}")

# --- 2. Generar Transacciones ---

print("Generando transacciones...")
todas_las_transacciones = []
balances_calculados = {} # {numeroCuenta: balance}
id_transaccion_actual = 1

# Obtener todas las IDs de cuentas
lista_numeros_cuenta = [c['numeroCuenta'] for c in cuentas_data]

# --- INICIO DE LA CORRECCIÓN ---
# 2.0. Inicializar TODOS los balances en cero PRIMERO
print("Inicializando balances...") # <-- CAMBIO
for cuenta in cuentas_data: # <-- CAMBIO (NUEVO BUCLE)
    balances_calculados[cuenta['numeroCuenta']] = 0.0 # <-- CAMBIO

# --- FIN DE LA CORRECCIÓN ---

for cuenta in cuentas_data:
    num_cuenta = cuenta['numeroCuenta']
    # balances_calculados[num_cuenta] = 0.0  # <-- CAMBIO (LÍNEA ELIMINADA)
    num_transacciones = random.randint(MIN_TRANS_POR_CUENTA, MAX_TRANS_POR_CUENTA)
    
    # 2a. Crear Depósito Inicial (obligatorio para no tener saldos negativos)
    monto_inicial = round(random.uniform(5000.0, 20000.0), 2)
    balances_calculados[num_cuenta] += monto_inicial
    
    trans_dep_inicial = {
        "idTransaccion": id_transaccion_actual,
        "cantidad": monto_inicial,
        "tipoTransaccion": "Depósito",
        "fecha": generar_fecha_aleatoria(FECHA_INICIO, FECHA_INICIO + datetime.timedelta(days=30)), # Primeros 30 días
        "idRemitente": None,
        "idDestinatario": num_cuenta
    }
    todas_las_transacciones.append(trans_dep_inicial)
    id_transaccion_actual += 1

    # 2b. Generar el resto de transacciones
    for _ in range(num_transacciones - 1):
        tipo_trans = random.choice(["Depósito", "Retiro", "Transferencia"])
        monto = round(random.uniform(50.0, 5000.0), 2)
        fecha_trans = generar_fecha_aleatoria(FECHA_INICIO, FECHA_FIN)
        
        transaccion = {
            "idTransaccion": id_transaccion_actual,
            "cantidad": monto,
            "tipoTransaccion": tipo_trans,
            "fecha": fecha_trans,
            "idRemitente": None,
            "idDestinatario": None
        }

        if tipo_trans == "Depósito":
            transaccion["idDestinatario"] = num_cuenta
            balances_calculados[num_cuenta] += monto
            todas_las_transacciones.append(transaccion)
            id_transaccion_actual += 1

        elif tipo_trans == "Retiro":
            # Asegurarse de no sobregirar la cuenta
            if balances_calculados[num_cuenta] >= monto:
                transaccion["idRemitente"] = num_cuenta
                balances_calculados[num_cuenta] -= monto
                todas_las_transacciones.append(transaccion)
                id_transaccion_actual += 1
            # Opcional: si no hay fondos, se podría saltar o convertir en depósito
            
        elif tipo_trans == "Transferencia":
            # Asegurarse de no sobregirar
            if balances_calculados[num_cuenta] >= monto:
                # Elegir un destinatario al azar (que no sea él mismo)
                destinatario_posible = lista_numeros_cuenta.copy()
                destinatario_posible.remove(num_cuenta)
                id_destinatario = random.choice(destinatario_posible)
                
                transaccion["idRemitente"] = num_cuenta
                transaccion["idDestinatario"] = id_destinatario
                
                # Actualizar balances de ambas cuentas
                balances_calculados[num_cuenta] -= monto
                balances_calculados[id_destinatario] += monto # Esta línea ya no dará error
                
                todas_las_transacciones.append(transaccion)
                id_transaccion_actual += 1

print(f"Total de transacciones generadas: {len(todas_las_transacciones)}")

# --- 3. Ordenar Transacciones por Fecha ---

print("Ordenando transacciones por fecha...")
todas_las_transacciones.sort(key=lambda x: x['fecha'])

# --- 4. Actualizar Balances Finales en Cuentas ---

print("Actualizando balances finales en el archivo de cuentas...")
for cuenta in cuentas_data:
    num_cuenta = cuenta['numeroCuenta']
    # Redondear el balance final a 2 decimales
    cuenta['balance'] = round(balances_calculados[num_cuenta], 2)

# --- 5. Guardar Archivos ---

print("Guardando archivos de salida...")
guardar_json(clientes_data, CLIENTES_OUT_FILE)
guardar_json(cuentas_data, CUENTAS_OUT_FILE)
guardar_json(todas_las_transacciones, TRANSACCIONES_OUT_FILE)

print("\n¡Proceso completado!")
print(f"Se generaron 3 archivos nuevos:")
print(f"1. {CLIENTES_OUT_FILE} (Total: {len(clientes_data)} clientes)")
print(f"2. {CUENTAS_OUT_FILE} (Total: {len(cuentas_data)} cuentas con saldos actualizados)")
print(f"3. {TRANSACCIONES_OUT_FILE} (Total: {len(todas_las_transacciones)} transacciones ordenadas y balanceadas)")