from libreria_cafe_edd_db.sesion import crear_sesion
from enum import Enum
from libreria_cafe_edd_db import Cliente
from sqlalchemy import and_
from Base_datos import ReservaDB, MesaDB, Guardado_multiple
import datetime


class Gestor_reserva:
    def __init__(self, sesion_fun):
        self.crear_sesion = sesion_fun

    def calcular_duracion(self, tipo, cant_personas):
        match (tipo.capitalize(), cant_personas):
            case ("Estudio", p) if p <= 2: return 3.0
            case ("Estudio", _): return 4.0
            case ("Cafe", p) if p <= 2: return 1.0
            case ("Cafe", p) if p <= 4: return 1.5
            case ("Cafe", p) if p <= 6: return 2.0
            case ("Cafe", _): return 2.5
            
            case _: return 2.0

    def verificar_disponibilidad(self, sesion, id_mesa, fecha_cita, hora_inicio, hora_fin):
        cruce = sesion.query(ReservaDB).filter(
            and_(
                ReservaDB.id_mesa == id_mesa,
                ReservaDB.fecha_cita == fecha_cita,
                ReservaDB.hora_inicio < hora_fin,
                ReservaDB.hora_fin > hora_inicio
            )
        ).first()
        return cruce is None # True si no hay nadie ocupándola
        
    def buscar_mesa_disponible(self, sesion, tipo, fecha_cita, hora_inicio, hora_fin):
        mesas_del_tipo = sesion.query(MesaDB).filter_by(tipo=tipo.capitalize()).all()
        
        for mesa in mesas_del_tipo:
            if self.verificar_disponibilidad(sesion, mesa.id_mesa, fecha_cita, hora_inicio, hora_fin):
                return mesa 
        return None
    
    def consultar_disponibilidad_fecha(self, hora_inicio, hora_fin, fecha_busqueda=datetime.datetime.today()):
        """
        Muestra los horarios libres de cada mesa para una fecha específica.
        Formato de fecha_busqueda: datetime.date.
        """
        
        sesion = self.crear_sesion()
        # Definimos el rango de operación del café (08:00 a 20:00)
        apertura = datetime.datetime.combine(fecha_busqueda, datetime.time(8, 0)).strftime("%H:%M")
        cierre = datetime.datetime.combine(fecha_busqueda, datetime.time(20, 0)).strftime("%H:%M")
        
        print(f"\n--- DISPONIBILIDAD PARA EL DÍA: {fecha_busqueda} ---")
        
        try:
            mesas = sesion.query(MesaDB).all()
            for mesa in mesas:
                print("buscando mesa")
                # 1. Buscamos reservas de esta mesa en la fecha indicada
                reservas = sesion.query(ReservaDB).filter(
                    and_(
                        ReservaDB.id_mesa == mesa.id_mesa,
                        ReservaDB.fecha_cita == fecha_busqueda,
                        ReservaDB.hora_inicio >= apertura,
                        ReservaDB.hora_fin < cierre
                    )
                ).order_by(ReservaDB.fecha_cita).all()
                print("no hubo error buscando las mesas")

                # 2. Lógica de "Huecos": Calculamos espacios libres entre reservas
                inicio_bloque = apertura
                libres = []

                for res in reservas:
                    if res.hora_inicio > inicio_bloque:
                        print("por ahora sin peos")
                        libres.append(f"{inicio_bloque.strftime('%H:%M')} a {res.fecha_cita.strftime('%H:%M')}")
                        print("hubo un peo")
                    inicio_bloque = res.hora_fin

                # 3. Espacio final desde la última reserva hasta el cierre
                if inicio_bloque < cierre:
                    libres.append(f"{inicio_bloque.strftime('%H:%M')} a {cierre.strftime('%H:%M')}")

                # 4. Formatear resultado
                horarios_texto = " | ".join(libres) if libres else "SIN DISPONIBILIDAD"
                print(f"Mesa {str(mesa.id_mesa).ljust(2)} [{mesa.tipo.ljust(7)}]: {horarios_texto}")

        except Exception as e:
            print(f"Error al consultar disponibilidad: {e}")
        finally:
            sesion.close()

    def realizar_reserva(self, id_cliente, personas, tipo, fecha_cita, hora_inicio, hora_fin):
        """Método principal para orquestar la reserva automática"""
        sesion = self.crear_sesion()
        try:
            mesa_libre = self.buscar_mesa_disponible(sesion, tipo, fecha_cita, hora_inicio, hora_fin)
            
            if not mesa_libre:
                return f"No hay mesas tipo '{tipo}' disponibles para {hora_inicio}."

            nueva = ReservaDB(
                id_cliente = id_cliente,
                id_mesa = mesa_libre.id_mesa,
                cant_personas = personas,
                fecha_cita = fecha_cita,
                hora_inicio = hora_inicio,
                hora_fin = hora_fin,
                fecha_creacion = datetime.datetime.now()
            )
            
            sesion.add(nueva)
            sesion.commit()
            print("se cago")
            
            id_visual = str(nueva.id_reserva).zfill(4)
            return f"Reserva {id_visual} exitosa. Mesa asignada: {mesa_libre.id_mesa} ({tipo})"

        except Exception as e:
            sesion.rollback()
            return f"Error crítico: {e}"
        finally:
            sesion.close()
            

class EstadoMesa(Enum):
    DISPONIBLE = "Disponible"
    OCUPADA = "Ocupada"
    RESERVADA = "Reservada"
    LIMPIANDO = "Limpiando"

def guardar_cliente(datos):
    sesion = crear_sesion()
    cliente = Cliente(
                id = datos[0],
                id_membresia = datos[1],
                nombre = datos[2],
                cedula = datos[0],
                fecha_ingreso = datetime.date.today(),
                fecha_cumple = datos[3],
                frecuencia = 0,
                razon_social = datos[4],
                direccion_fiscal =datos[5],
                telefono = datos[6]
    )
    existencia = sesion.query(Cliente).filter_by(id=cliente.id).first()
    
    if existencia:
        print(f"El cliente {existencia.nombre} ya esta registrado con la cedula: V-{existencia.id}")
        sesion.close()
    else:
        try:
            sesion.add(cliente)
            sesion.commit()
            print(f"Cliente {cliente.nombre} Guardado correctamente.")
        except Exception as e:
            sesion.rollback()
            print(f"Error al guardar: {e}")
        finally:
            sesion.close()

mesas = []
contador = 1

def mostrar(lista):
    for i in lista:
        print(i)


datos_lote_masivo = [
    [29554133, 0, "Jesuz", datetime.date(2001,4,13), "Perosnal", "Pozuelos", 4124220876],
    [10203040, 2, "Carlos Rodriguez", datetime.date(1985, 5, 12), "Suministros C.R.", "Barcelona", "04125559988"],
    [50607080, 3, "Lucia Fernandez", datetime.date(1993, 11, 24), "Personal", "Lecheria", "04246661122"],
    [90102030, 4, "Andres Bello", datetime.date(1978, 2, 10), "Inversiones AB", "Guanta", "04163334455"],
]

Guardado_multiple(datos_lote_masivo, guardar_cliente)

gestor = Gestor_reserva(crear_sesion)
if __name__ == "__main__":
    
    
    hoy = datetime.datetime.now().strftime('%d-%m-%y')
    hora_1 = datetime.datetime.combine(datetime.datetime.now(), datetime.time(23, 30)).strftime("%H:%M")
    hora_2 = datetime.datetime.combine(datetime.datetime.now(), datetime.time(00, 00)).strftime("%H:%M")

    print(
        gestor.realizar_reserva(
            id_cliente=29554133,
            personas = 3,
            tipo = "estudio",
            hora_inicio = hora_1,
            hora_fin = hora_2,
            fecha_cita = hoy
    ))

gestor.consultar_disponibilidad_fecha("23:30", "00:00")
