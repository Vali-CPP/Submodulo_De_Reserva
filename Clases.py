from libreria_cafe_edd_db.sesion import crear_sesion
from libreria_cafe_edd_db import Cliente
from sqlalchemy import and_
from Base_datos import ReservaDB, MesaDB, Guardado_multiple
import datetime




"""
    - Realizar una funcion para 
"""

class Gestor_reserva:
    def __init__(self, sesion_fun):
        self.crear_sesion = sesion_fun

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
            
            id_visual = str(nueva.id_reserva).zfill(4)
            return f"Reserva {id_visual} exitosa. Mesa asignada: {mesa_libre.id_mesa} ({tipo})"

        except Exception as e:
            sesion.rollback()
            return f"Error crítico: {e}"
        finally:
            sesion.close()

    def eliminar_reserva(self, id_cliente, personas, tipo, fecha_cita, hora_inicio, hora_fin):

        

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


