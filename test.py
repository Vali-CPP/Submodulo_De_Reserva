from Clases import Gestor_reserva, guardar_cliente
from libreria_cafe_edd_db.sesion import crear_sesion
from Base_datos import Guardado_multiple
import datetime

datos_lote_masivo = [
        [29554133, 0, "Jesuz", datetime.date(2001,4,13), "Perosnal", "Pozuelos", 4124220876],
        [10203040, 2, "Carlos Rodriguez", datetime.date(1985, 5, 12), "Suministros C.R.", "Barcelona", "04125559988"],
        [50607080, 3, "Lucia Fernandez", datetime.date(1993, 11, 24), "Personal", "Lecheria", "04246661122"],
        [90102030, 4, "Andres Bello", datetime.date(1978, 2, 10), "Inversiones AB", "Guanta", "04163334455"],
        ]

Guardado_multiple(datos_lote_masivo, guardar_cliente)


def menu_cli():
    # Se pasa la función crear_sesion al constructor como solicita la clase
    gestor = Gestor_reserva(crear_sesion)
    
    while True:
        print("\n--- SISTEMA DE RESERVAS (CLI) ---")
        print("1. Consultar disponibilidad")
        print("2. Realizar reserva")
        print("3. Editar reserva")
        print("4. Eliminar reserva (por horario)")
        print("5. Salir")
        
        opcion = input("\nSeleccione una opción: ")

        if opcion == "1":
            fecha = input("Fecha (YYYY-MM-DD) [Enter para hoy]: ")
            inicio = input("Hora inicio (HH:MM): ")
            fin = input("Hora fin (HH:MM): ")
            
            f_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
            
            # SOLUCIÓN: Crear la sesión, pasarla al método y cerrarla
            sesion = crear_sesion() 
            res = gestor.consultar_disponibilidad(sesion, f_obj, inicio, fin)
            sesion.close()
            
            #print("\nResultado:", res)

            print("\n" + "*"*30)
            if isinstance(res, list):
                print(f"{'ID MESA':<10} | {'TIPO':<12} | {'CAP.'}")
                print("-" * 30)
                for mesa in res:
                    print(f"{mesa['id_mesa']:<10} | {mesa['tipo']:<12} | {mesa['capacidad']}")
            else:
                print(res)
            print("*"*30)

        elif opcion == "2":
            try:
                id_cli = int(input("ID Cliente (Cédula): "))
                pers = int(input("Cantidad de personas: "))
                tipo = input("Tipo de mesa: ")
                fecha = input("Fecha (YYYY-MM-DD): ")
                inicio = input("Hora inicio (HH:MM): ")
                fin = input("Hora fin (HH:MM): ")
                
                f_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
                print("\n" + gestor.realizar_reserva(id_cli, pers, tipo, f_obj, inicio, fin))
            except ValueError:
                print("Error: Ingrese datos numéricos válidos en ID y personas.")

        elif opcion == "3":
            try:
                id_res = int(input("ID de la reserva a editar: "))
                print("Deje en blanco si no desea modificar el campo.")
                pers = input("Nueva cantidad personas: ")
                tipo = input("Nuevo tipo mesa: ")
                fecha = input("Nueva fecha (YYYY-MM-DD): ")
                
                p_val = int(pers) if pers else None
                t_val = tipo if tipo else None
                f_val = datetime.datetime.strptime(fecha, "%Y-%m-%d").date() if fecha else None
                
                print("\n" + gestor.editar_reserva(id_res, personas=p_val, tipo=t_val, fecha_cita=f_val))
            except ValueError:
                print("Error en el formato de los datos.")

        elif opcion == "4":
            fecha = input("Fecha de la reserva (YYYY-MM-DD): ")
            inicio = input("Hora de inicio: ")
            f_obj = datetime.datetime.strptime(fecha, "%Y-%m-%d").date()
            print("\n" + gestor.eliminar_reserva_por_horario(f_obj, inicio))

        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    
    menu_cli()
