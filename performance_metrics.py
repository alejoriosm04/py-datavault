import time
import psutil
import os
from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np

@dataclass
class OperationMetrics:
    start_time: float
    end_time: float = 0
    initial_size: int = 0
    final_size: int = 0
    cpu_percent: list = None
    memory_usage: list = None
    
    @property
    def duration(self) -> float:
        if self.end_time == 0:
            return 0
        return self.end_time - self.start_time
    
    @property
    def compression_ratio(self) -> float:
        if self.initial_size == 0:
            return 0
        return self.final_size / self.initial_size

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, OperationMetrics] = {}
        self._current_operation: Optional[str] = None
        
    def start_operation(self, operation_name: str, initial_size: int = 0):
        """Inicia el monitoreo de una operación."""
        self.metrics[operation_name] = OperationMetrics(
            start_time=time.time(),
            initial_size=initial_size,
            cpu_percent=[],
            memory_usage=[]
        )
        self._current_operation = operation_name
        
    def end_operation(self, operation_name: str, final_size: int = 0):
        """Finaliza el monitoreo de una operación."""
        if operation_name in self.metrics:
            self.metrics[operation_name].end_time = time.time()
            self.metrics[operation_name].final_size = final_size
            
    def record_resource_usage(self):
        """Registra el uso actual de CPU y memoria."""
        if self._current_operation:
            metrics = self.metrics[self._current_operation]
            metrics.cpu_percent.append(psutil.cpu_percent(interval=0.1))
            metrics.memory_usage.append(psutil.Process().memory_info().rss / 1024 / 1024)  
            
    def get_operation_stats(self, operation_name: str) -> dict:
        """Retorna estadísticas detalladas de una operación."""
        if operation_name not in self.metrics:
            return {}
            
        metrics = self.metrics[operation_name]
        return {
            "duration_seconds": metrics.duration,
            "compression_ratio": metrics.compression_ratio,
            "avg_cpu_percent": np.mean(metrics.cpu_percent) if metrics.cpu_percent else 0,
            "max_cpu_percent": max(metrics.cpu_percent) if metrics.cpu_percent else 0,
            "avg_memory_mb": np.mean(metrics.memory_usage) if metrics.memory_usage else 0,
            "max_memory_mb": max(metrics.memory_usage) if metrics.memory_usage else 0,
            "throughput_mb_s": (metrics.initial_size / 1024 / 1024) / metrics.duration if metrics.duration > 0 else 0
        }
        
    def print_operation_stats(self, operation_name: str):
        """Imprime las estadísticas de una operación de forma legible."""
        stats = self.get_operation_stats(operation_name)
        if not stats:
            print(f"No hay estadísticas disponibles para la operación: {operation_name}")
            return
            
        print(f"\n=== Estadísticas de rendimiento para {operation_name} ===")
        print(f"Duración: {stats['duration_seconds']:.2f} segundos")
        print(f"Tasa de compresión: {(1 - stats['compression_ratio']) * 100:.2f}%")
        print(f"CPU promedio: {stats['avg_cpu_percent']:.1f}%")
        print(f"CPU máximo: {stats['max_cpu_percent']:.1f}%")
        print(f"Memoria promedio: {stats['avg_memory_mb']:.1f} MB")
        print(f"Memoria máxima: {stats['max_memory_mb']:.1f} MB")
        print(f"Velocidad de transferencia: {stats['throughput_mb_s']:.2f} MB/s")
        print("=" * 50)