from libreria_cafe_edd_db.sesion import crear_sesion
from libreria_cafe_edd_db import Cliente
from sqlalchemy import and_
from Base_datos import ReservaDB, MesaDB, Guardado_multiple
from sqlalchemy import and_, func, cast, Date # Agrega func y Date a tus imports
import datetime

"""
    - Realizar una funcion para 
"""

class Gestor_reserva:

    def __init__(self, sesion_fun):
        self.crear_sesion = sesion_fun

    def realizar_reserva(self, id_cliente, personas, tipo, fecha_cita, hora_inicio, hora_fin):

        if personas > 6:
            return "La reserva excede el límite permitido. El máximo es de 6 personas por mesa."

        """Método principal para orquestar la reserva automática"""

        sesion = self.crear_sesion()
        try:
            # Configuración de valores por defecto
            if fecha_cita is None:
                fecha_cita = datetime.date.today()
            
            # CAMBIO: La base de datos guarda 'fecha_cita' como DateTime (ej. 2026-03-01 00:00:00).
            # Si se manda un objeto Date (2026-03-01), SQLite no lo reconoce al buscarlo.
            # Por tanto, convertimos 'fecha_cita' a datetime exacto si viene como date.
            if type(fecha_cita) is datetime.date:
                fecha_cita = datetime.datetime(fecha_cita.year, fecha_cita.month, fecha_cita.day)
            
            if hora_inicio is None:
                hora_inicio = "08:00"
            
            if hora_fin is None:
                # Se asume una duración estándar de 1 hora si no se especifica fin
                hora_fin = "09:00"

            mesa_libre = self.consultar_disponibilidad(sesion, fecha_cita, hora_inicio, hora_fin)
            print("Si pase esta parte, no te creas")
            
            # CAMBIO: Verificamos si `consultar_disponibilidad` devolvió un error (string) o una lista vacía
            if isinstance(mesa_libre, str) or not mesa_libre:
                return f"No hay mesas disponibles para el {fecha_cita} a las {hora_inicio}."

            # CAMBIO: Agregamos el filtrado para entregar específicamente el 'tipo' de mesa que pidió el cliente.
            mesas_tipo = [m for m in mesa_libre if m.get("tipo", "").lower() == tipo.lower()]
            if not mesas_tipo:
                return f"No hay mesas tipo '{tipo}' disponibles para {hora_inicio}."
            
            # CAMBIO: Seleccionamos la primera mesa que cumple con los requisitos
            mesa_asignada = mesas_tipo[0]

            nueva = ReservaDB(
                id_cliente = id_cliente,
                id_mesa = mesa_asignada.get("id_mesa"), # Asegurado el acceso al diccionario
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

    def eliminar_reserva_por_horario(self, fecha_cita, hora_inicio):
        """Método para eliminar una reserva por fecha y hora de inicio"""
        sesion = self.crear_sesion()
        try:
            # CAMBIO: Adaptamos la fecha enviada (Date) al formato de la tabla (DateTime)
            # para que la consulta SQL pueda encontrar coincidencias.
            if type(fecha_cita) is datetime.date:
                fecha_cita = datetime.datetime(fecha_cita.year, fecha_cita.month, fecha_cita.day)

            reserva = sesion.query(ReservaDB).filter(
                ReservaDB.fecha_cita == fecha_cita,
                ReservaDB.hora_inicio == hora_inicio
            ).first()
            
            if not reserva:
                return f"No se encontró ninguna reserva para el {fecha_cita} a las {hora_inicio}."

            id_visual = str(reserva.id_reserva).zfill(4)
            sesion.delete(reserva)
            sesion.commit()
            
            return f"Reserva {id_visual} eliminada correctamente."

        except Exception as e:
            sesion.rollback()
            return f"Error al eliminar la reserva: {e}"
        finally:
            sesion.close()
        

    def consultar_disponibilidad(self, sesion, fecha_cita=None, hora_inicio=None, hora_fin=None):
        """Consulta todas las mesas disponibles para una fecha y rango horario específicos"""
        try:
            if fecha_cita is None:
                fecha_cita = datetime.date.today()
            
            # Subconsulta para obtener los IDs de las mesas que ya tienen reservas en ese horario
            reservas_ocupadas = sesion.query(ReservaDB.id_mesa).filter(
                func.date(ReservaDB.fecha_cita) == fecha_cita
            )
            
            # Solo aplicamos el filtro de hora si AMBOS valores existen
            if hora_inicio and hora_fin:
                reservas_ocupadas = reservas_ocupadas.filter(
                    and_(
                        ReservaDB.hora_inicio < hora_fin,
                        ReservaDB.hora_fin > hora_inicio
                    )
                )
                
            mesas_ocupadas_ids = [r.id_mesa for r in reservas_ocupadas.all()]
            
            # Filtrar mesas que no estén en la lista de ocupadas
            mesas_disponibles = sesion.query(MesaDB).filter(
                ~MesaDB.id_mesa.in_(mesas_ocupadas_ids)
            ).all()
            
            if not mesas_disponibles:
                return f"No hay mesas disponibles para la fecha {fecha_cita} en el horario solicitado."
                
            resultado = [
                {"id_mesa": m.id_mesa, "tipo": m.tipo, "capacidad": m.capacidad} 
                for m in mesas_disponibles
            ]
            return resultado

        except Exception as e:
            return f"Error al consultar disponibilidad: {e}"
        finally:
            # CAMBIO: Cerramos la sesión únicamente si fue creada por el propio método (es decir, desde test.py).
            if sesion_propia:
                sesion.close()


    def editar_reserva(self, id_reserva, personas=None, tipo=None, fecha_cita=None, hora_inicio=None, hora_fin=None):
        """Método para actualizar los datos de una reserva existente"""
        if personas is not None and (not isinstance(personas, int) or personas <= 0 or personas > 6):
            return "Error: La cantidad de personas debe ser entre 1 y 6."

        sesion = self.crear_sesion()
        try:
            reserva = sesion.query(ReservaDB).filter(ReservaDB.id_reserva == id_reserva).first()
            if not reserva:
                return f"No se encontró la reserva con ID {id_reserva}."

            # Determinar valores finales (nuevos o actuales) para validar disponibilidad
            n_fecha = fecha_cita if fecha_cita else reserva.fecha_cita
            
            # CAMBIO: Normalizamos la fecha a datetime si ingresa un date
            if type(n_fecha) is datetime.date:
                n_fecha = datetime.datetime(n_fecha.year, n_fecha.month, n_fecha.day)
                
            n_inicio = hora_inicio if hora_inicio else reserva.hora_inicio
            n_fin = hora_fin if hora_fin else reserva.hora_fin
            # CAMBIO: Usar reserva.mesa.tipo si no se provee un tipo nuevo, en lugar de dejar el valor inventado "estandar".
            n_tipo = tipo if tipo else reserva.mesa.tipo

            # CAMBIO: Usar 'consultar_disponibilidad' en lugar de la función inexistente 'buscar_mesa_disponible'.
            mesas_disponibles = self.consultar_disponibilidad(sesion, n_fecha, n_inicio, n_fin)
            
            # CAMBIO: Validamos que, si el horario y fecha son exactamente los mismos, la propia 
            # mesa actual va a salir como ocupada (por nosotros mismos en la base de datos).
            # Para no perder nuestra reserva, la conservamos si se mantiene el horario y tipo de mesa.
            mismo_horario = (n_fecha == reserva.fecha_cita and n_inicio == reserva.hora_inicio and n_fin == reserva.hora_fin)
            
            id_mesa_asignada = None
            if isinstance(mesas_disponibles, str) or not mesas_disponibles:
                if mismo_horario and n_tipo.lower() == reserva.mesa.tipo.lower():
                    id_mesa_asignada = reserva.id_mesa
                else:
                    return "No hay mesas disponibles con los nuevos parámetros solicitados."
            else:
                # Filtrar mesas por tipo
                mesas_tipo = [m for m in mesas_disponibles if m.get("tipo", "").lower() == n_tipo.lower()]
                if not mesas_tipo:
                    if mismo_horario and n_tipo.lower() == reserva.mesa.tipo.lower():
                        id_mesa_asignada = reserva.id_mesa
                    else:
                        return f"No hay mesas tipo '{n_tipo}' disponibles para los parámetros solicitados."
                else:
                    id_mesa_asignada = mesas_tipo[0].get("id_mesa")

            # Aplicar cambios
            reserva.id_mesa = id_mesa_asignada
            reserva.cant_personas = personas if personas else reserva.cant_personas
            reserva.fecha_cita = n_fecha
            reserva.hora_inicio = n_inicio
            reserva.hora_fin = n_fin
            
            sesion.commit()
            id_visual = str(id_reserva).zfill(4)
            return f"Reserva {id_visual} actualizada exitosamente. Nueva mesa: {id_mesa_asignada}"

        except Exception as e:
            sesion.rollback()
            return f"Error al editar la reserva: {e}"
        finally:
            sesion.close()


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




