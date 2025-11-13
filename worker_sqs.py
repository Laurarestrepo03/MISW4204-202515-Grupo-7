"""
worker_sqs.py - Worker que consume mensajes de AWS SQS y aplica cifrado
"""
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Optional, Dict
from database import SessionLocal
from datetime import datetime, timezone
from s3 import retrieve_file_from_bucket, upload_file_to_bucket
from moviepy import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips
import boto3
import json
import os
import models
import shutil

class SQSCipherWorker:
    def __init__(self, queue_name='ANB_SQS', region_name='us-east-1'):
        """
        Inicializa el worker SQS
        
        Args:
            queue_name: Nombre de la cola SQS
            region_name: Región de AWS
            shift: Desplazamiento para cifrado César
        """
        self.queue_name = queue_name
        self.region_name = region_name
        self.processed_count = 0
        
        # Crear cliente SQS
        self.sqs = boto3.client('sqs', region_name=region_name)
        
        # Obtener URL de la cola
        self.queue_url = "https://sqs.us-east-1.amazonaws.com/490225881732/ANB_SQS"
    
    def process_message(self, payload: dict) -> dict:
        """
        Inicia el procesamiento de un video
        
        Args:
            payload: Diccionario con el ID del video
            
        Returns:
            dict: Payload procesado con el ID del video
        """
        video_id = int(payload.get('video_id', ''))
        db = SessionLocal()
        try:
            video = db.get(models.Video, video_id)
            if not video:
                return
            video_name = video.original_filename.replace(" ", "_")
            title = video.title
            db.close()
            self.process_video(video_name, title, video_id)
        finally:
            db.close()
        
        return payload
    
    def process_video(self, video_name: str, title: str, video_id: int):
        try:
            #raise TypeError("Forced error") # -> Descomentar esta linea para forzar un error
            # Crear carpeta processed si no existe
            os.makedirs("temp_files/original", exist_ok=True)
            os.makedirs("temp_files/processed", exist_ok=True)

            s3_path="original_videos/"+video_name
            local_path = "temp_files/original/"+video_name
            retrieve_file_from_bucket(s3_path, local_path)

            video = VideoFileClip(local_path)

            # 1. Quitar audio
            video = video.with_volume_scaled(0.0)

            # 2. Recortar a 30s
            video_length = video.duration
            if video_length > 30:
                video = video.subclipped(0,30)

            # 3. Ajustar ratio a 16:9 (calidad 720p)
            resolution = 720
            background = ColorClip(size=(1280, 720), color=(0, 0, 0))
            background = background.with_duration(video.duration)
            video = video.resized(height=resolution)
            video = video.with_position("center")
            video = CompositeVideoClip([background, video])

            # 4. Agregar logo ANB
            anb_logo = VideoFileClip("assets/anb_logo.mp4").resized(height=resolution)
            videos = [anb_logo, video, anb_logo]
            final_video = concatenate_videoclips(videos, method='compose')
            no_spaces_title = title.replace(" ", "_")+".mp4"
            temp_video_path = "temp_files/processed/"+no_spaces_title
            final_video.write_videofile(temp_video_path)

            processed_url = "https://anb.com/videos/processed/"+no_spaces_title

            upload_file_to_bucket(temp_video_path, "processed_videos/"+no_spaces_title)
            self.update_uploaded_info(video_id, datetime.now(timezone.utc), processed_url)

        finally:
            if os.path.exists("temp_files"):
                shutil.rmtree("temp_files")

    def update_uploaded_info(self, video_id: int, processed_at: datetime, processed_url: str):
        db = SessionLocal()
        try:
            video = db.get(models.Video, video_id)
            if not video:
                return
            
            video.status = models.VideoStatus.PROCESSED
            video.processed_at = processed_at
            video.processed_url = processed_url
            db.commit()    
        finally:
            db.close()
    
    def consume_message(self) -> Optional[Dict]:
        """
        Consume un mensaje de la cola SQS
        
        Returns:
            dict o None: Mensaje procesado o None si no hay mensajes
        """
        try:
            # Recibir mensaje con long polling (WaitTimeSeconds=20)
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,  # Long polling: espera hasta 20 segundos
                MessageAttributeNames=['All'],
                AttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if not messages:
                return None
            
            message = messages[0]
            receipt_handle = message['ReceiptHandle']
            
            # Parsear el body del mensaje
            payload = json.loads(message['Body'])
            
            # Procesar el mensaje
            processed = self.process_message(payload)
            
            # IMPORTANTE: Eliminar el mensaje de la cola después de procesarlo
            self.sqs.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            
            self.processed_count += 1
            return processed
            
        except ClientError as e:
            print(f"✗ Error al procesar mensaje: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"✗ Error al parsear JSON: {e}")
            # Aún así eliminar el mensaje corrupto
            try:
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=receipt_handle
                )
            except:
                pass
            return None
    
    def get_queue_stats(self) -> dict:
        """Obtiene estadísticas de la cola"""
        try:
            response = self.sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['All']
            )
            return response['Attributes']
        except ClientError:
            return {}
    
    def start(self, continuous: bool = True, max_messages: Optional[int] = None):
        """
        Inicia el worker
        
        Args:
            continuous: Si es True, ejecuta continuamente
            max_messages: Número máximo de mensajes a procesar (None = ilimitado)
        """
        print("=== Worker de Procesamiento de Videos AWS SQS ===")
        print(f"Cola: {self.queue_name}")
        print(f"Region: {self.region_name}")
        print(f"Modo: {'Continuo' if continuous else 'Single run'}")
        
        # Estadísticas iniciales
        stats = self.get_queue_stats()
        print(f"Mensajes en cola: {stats.get('ApproximateNumberOfMessages', 'N/A')}")
        print("\nEsperando mensajes...\n")
        
        try:
            while True:
                # Verificar límite de mensajes
                if max_messages and self.processed_count >= max_messages:
                    print(f"\n✓ Límite alcanzado: {max_messages} mensajes procesados")
                    break
                
                result = self.consume_message()
                
                if result:
                    print(f"[{self.processed_count}] Procesado:")
                    print(f"  ID Video:  {result['video_id']}")
                else:
                    if not continuous:
                        print("⏳ No hay mensajes disponibles")
                        break
                    # Long polling maneja la espera automáticamente
                    # No necesitamos sleep adicional
                    
        except KeyboardInterrupt:
            print(f"\n✓ Worker detenido por usuario")
        finally:
            self._shutdown()
    
    def _shutdown(self):
        """Cierre limpio del worker"""
        print(f"✓ Mensajes procesados: {self.processed_count}")
        
        # Estadísticas finales
        stats = self.get_queue_stats()
        remaining = stats.get('ApproximateNumberOfMessages', 'N/A')
        print(f"✓ Mensajes restantes en cola: {remaining}")


def main():
    """Función principal para ejecutar el worker"""
    worker = SQSCipherWorker(
        queue_name='message-queue',
        region_name='us-east-1',
    )
    
    # Ejecutar continuamente
    worker.start(continuous=True)
    
    # O procesar solo N mensajes:
    # worker.start(continuous=False, max_messages=10)


if __name__ == "__main__":
    main()