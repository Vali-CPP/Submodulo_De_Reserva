from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from libreria_cafe_edd_db.sesion import Base, crear_sesion, engine

def Guardado_multiple(lista, funcion):
    for i in lista:
        funcion(i)


class ReservaDB(Base):
    __tablename__ = 'reservas'

    id_reserva = Column(Integer, primary_key=True, autoincrement=True)
    id_cliente = Column(Integer, ForeignKey('cliente.id'), nullable=False)
    id_mesa = Column(Integer, ForeignKey('mesas.id_mesa')) #se cambio de tipo str a integer
    cant_personas = Column(Integer, nullable=False)
    fecha_cita = Column(DateTime, nullable=False)
    hora_inicio = Column(String, nullable=False)
    hora_fin = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, nullable=False)
    
    mesa = relationship("MesaDB", back_populates = "reservas")
    cliente = relationship("Cliente")
    
    
class MesaDB(Base):
    __tablename__ = 'mesas'
    id_mesa = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String)                      
    capacidad = Column(Integer)
    reservas = relationship("ReservaDB", back_populates="mesa")

Base().metadata.create_all(engine)
    

def crear_mesa(datos):
    sesion = crear_sesion()
    mesa = MesaDB(id_mesa = datos[0],
                tipo = datos[1],
                capacidad = 6)
    existencia = sesion.query(MesaDB).filter_by(id_mesa=mesa.id_mesa).first()
    
    if existencia:
        print(f"La mesa {existencia.id_mesa} ya esta registrada en la base")
        sesion.close()
    else:
        try:
            sesion.add(mesa)
            sesion.commit()
            print(f"Mesa {mesa.id_mesa} Guardada exitosamente.")
        except Exception as e:
            sesion.rollback()
            print(f"Error al guardar: {e}")
        finally:
            sesion.close()

"""
    Creando una tabla mesas en la base de datos y agregando 10 mesas de dos diferentes tipos
    Estudio y Cafe
"""
lista = []

contador = 1

for tipo in ["Estudio", "Cafe"]:
    for _ in range(10):
        lista.append([contador, tipo])
        contador += 1

Guardado_multiple(lista, crear_mesa)
