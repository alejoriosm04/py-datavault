from performance_metrics import PerformanceMonitor
import time
import os

def create_test_file(size_mb: int) -> str:
    """Crea un archivo de prueba del tamaño especificado."""
    filename = "test_file.txt"
    with open(filename, "wb") as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    return filename

def main():
    monitor = PerformanceMonitor()
    
    print("Creando archivo de prueba de 100MB...")
    test_file = create_test_file(100)
    file_size = os.path.getsize(test_file)
    
    print("\nProbando operación secuencial...")
    monitor.start_operation("proceso_secuencial", file_size)
    
    for _ in range(5):
        time.sleep(1)  
        monitor.record_resource_usage()
    
    monitor.end_operation("proceso_secuencial", file_size)
    monitor.print_operation_stats("proceso_secuencial")
    
    print("\nProbando operación paralela...")
    monitor.start_operation("proceso_paralelo", file_size)
    
    for _ in range(2):
        time.sleep(0.5)  
        monitor.record_resource_usage()
    
    monitor.end_operation("proceso_paralelo", file_size)
    monitor.print_operation_stats("proceso_paralelo")
    
    os.remove(test_file)
    
    sequential_stats = monitor.get_operation_stats("proceso_secuencial")
    parallel_stats = monitor.get_operation_stats("proceso_paralelo")
    
    speedup = sequential_stats["duration_seconds"] / parallel_stats["duration_seconds"]
    print(f"\n=== Comparación de rendimiento ===")
    print(f"Aceleración: {speedup:.2f}x más rápido con procesamiento paralelo")
    print("=" * 50)

if __name__ == "__main__":
    main()