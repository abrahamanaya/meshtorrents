"""
MeshTorrents - Módulo de Procesamiento BitTorrent y P2P
Maneja la validación de magnet links, extracción de InfoHash y comunicación con agregadores.
"""

from torf import Magnet
import re
import httpx
from typing import Dict, Any, Optional

class MeshP2PEngine:
    
    @staticmethod
    def parse_magnet(magnet_uri: str) -> Dict[str, Any]:
        """
        Analiza una cadena Magnet Link y extrae sus componentes principales (InfoHash, Nombre, Trackers).
        """
        try:
            mag = Magnet.from_string(magnet_uri)
            return {
                "success": True,
                "infohash": str(mag.infohash).lower(),
                "name": mag.dn or "Modelo 3D Desconocido",
                "trackers": mag.tr,
                "magnet_uri": str(mag)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Formato de Magnet Link inválido: {str(e)}"
            }

    @staticmethod
    def is_stl_related(title: str, tags_list: list = None) -> bool:
        """
        Filtro básico para verificar si el contenido corresponde a un modelo 3D/STL.
        """
        keywords = [r'\bstl\b', r'\b3d\b', r'\b3mf\b', r'print', r'impresion', r'miniature', r'cad', r'mesh']
        pattern = re.compile('|'.join(keywords), re.IGNORECASE)
        
        if pattern.search(title):
            return True
        
        if tags_list:
            for tag in tags_list:
                if pattern.search(tag):
                    return True
                    
        return False

async def fetch_prowlarr_feed(api_url: str, api_key: str, query: str = "stl") -> Optional[list]:
    """
    Función asíncrona para consultar un agregador tipo Prowlarr/Jackett 
    y filtrar resultados con formato STL para insertar en MeshTorrents.
    """
    params = {
        "apikey": api_key,
        "query": query,
        "type": "search"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{api_url}/api/v1/search", params=params, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data:
                    title = item.get("title", "")
                    magnet = item.get("magnetUrl") or item.get("downloadUrl", "")
                    
                    # Filtrar únicamente si contiene metadatos de impresión 3D/STL
                    if MeshP2PEngine.is_stl_related(title) and magnet.startswith("magnet:"):
                        parsed = MeshP2PEngine.parse_magnet(magnet)
                        if parsed["success"]:
                            results.append({
                                "title": title,
                                "infohash": parsed["infohash"],
                                "magnet_uri": parsed["magnet_uri"],
                                "seeders": item.get("seeders", 0),
                                "size": item.get("size", 0)
                            })
                return results
        except Exception as e:
            print(f"[MeshTorrents P2P Error] No se pudo consultar la API externa: {e}")
            return None