"""
actualizar_entregables.py - Utilidad de una sola vez.
Borra TODOS los entregables actuales para poder cargar el cronograma nuevo.
NO borra a los equipos ni a los alumnos.
"""
import db

def main():
    print("Iniciando limpieza de entregables...")
    
    # 1. Obtener todos los entregables
    entregables = db.get_entregables()
    total = len(entregables)
    
    if total == 0:
        print("No hay entregables que borrar. Todo limpio.")
        return

    # 2. Borrarlos
    import config
    import json
    
    print(f"Borrando {total} entregables viejos...")
    
    # Guardamos la lista vacía en el archivo local y en GitHub
    with open(config.ARCHIVO_ENTREGABLES, "w", encoding="utf-8") as f:
        json.dump([], f)
        
    db._subir_archivo_a_github(config.ARCHIVO_ENTREGABLES, mensaje="[app] Limpieza de entregables para nuevo cronograma")
    
    print("¡Listo! Entregables eliminados correctamente.")

if __name__ == "__main__":
    main()