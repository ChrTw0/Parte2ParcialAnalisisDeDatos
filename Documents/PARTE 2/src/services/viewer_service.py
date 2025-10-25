"""
Servicio para manejar la lógica de negocio del visor de datos.
Carga y procesa el DataFrame de Pandas.
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from fastapi.encoders import jsonable_encoder

class ViewerService:
    def __init__(self, csv_path: Path):
        self.df = self._load_data(csv_path)

    def _load_data(self, csv_path: Path) -> pd.DataFrame:
        """Carga los datos desde el archivo CSV a un DataFrame de Pandas."""
        if not csv_path.exists():
            return pd.DataFrame()
        
        df = pd.read_csv(csv_path)
        return df.astype(object).where(pd.notna(df), None)

    def get_filter_options(self) -> Dict[str, List[str]]:
        """Obtiene los valores únicos para los controles de filtro."""
        if self.df.empty:
            return {"bancos": [], "tipos": [], "monedas": []}

        return {
            "bancos": sorted(self.df["Banco"].dropna().unique().tolist()),
            "tipos": sorted(self.df["Tipo"].dropna().unique().tolist()),
            "monedas": sorted(self.df["Moneda"].dropna().unique().tolist()),
        }

    def get_stats(self) -> Dict:
        """Calcula estadísticas generales del dataset."""
        if self.df.empty:
            return {
                "total_registros": 0,
                "bancos_count": 0,
                "tipos_count": {},
                "tasa_promedio_mn": 0,
                "tasa_promedio_me": 0,
            }

        tasa_promedio_mn = pd.to_numeric(self.df["Tasa_Porcentaje_MN"], errors='coerce').dropna().mean()
        tasa_promedio_me = pd.to_numeric(self.df["Tasa_Porcentaje_ME"], errors='coerce').dropna().mean()

        return {
            "total_registros": len(self.df),
            "bancos_count": self.df["Banco"].nunique(),
            "tipos_count": self.df["Tipo"].value_counts().to_dict(),
            "tasa_promedio_mn": round(tasa_promedio_mn, 2) if pd.notna(tasa_promedio_mn) else None,
            "tasa_promedio_me": round(tasa_promedio_me, 2) if pd.notna(tasa_promedio_me) else None,
        }

    def _get_filtered_df(self, 
                         banco: Optional[str] = None,
                         tipo: Optional[str] = None,
                         moneda: Optional[str] = None,
                         producto: Optional[str] = None,
                         concepto: Optional[str] = None,
                         tasa_mn_gte: Optional[float] = None,
                         tasa_mn_lte: Optional[float] = None,
                         tasa_me_gte: Optional[float] = None,
                         tasa_me_lte: Optional[float] = None,
                         sort_by: Optional[str] = None,
                         sort_order: str = 'asc') -> pd.DataFrame:
        
        if self.df.empty:
            return pd.DataFrame()

        filtered_df = self.df.copy()

        # Convertir columnas de tasa a numérico para filtros y ordenamiento
        for col in ['Tasa_Porcentaje_MN', 'Tasa_Porcentaje_ME']:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

        # Aplicar filtros de texto
        if banco:
            filtered_df = filtered_df[filtered_df["Banco"] == banco]
        if tipo:
            filtered_df = filtered_df[filtered_df["Tipo"] == tipo]
        if moneda:
            filtered_df = filtered_df[filtered_df["Moneda"] == moneda]
        if producto:
            filtered_df = filtered_df[filtered_df["Producto_Nombre"].str.contains(producto, case=False, na=False)]
        if concepto:
            filtered_df = filtered_df[filtered_df["Concepto"].str.contains(concepto, case=False, na=False)]
        
        # Aplicar filtros numéricos
        if tasa_mn_gte is not None:
            filtered_df = filtered_df[filtered_df['Tasa_Porcentaje_MN'] >= tasa_mn_gte]
        if tasa_mn_lte is not None:
            filtered_df = filtered_df[filtered_df['Tasa_Porcentaje_MN'] <= tasa_mn_lte]
        if tasa_me_gte is not None:
            filtered_df = filtered_df[filtered_df['Tasa_Porcentaje_ME'] >= tasa_me_gte]
        if tasa_me_lte is not None:
            filtered_df = filtered_df[filtered_df['Tasa_Porcentaje_ME'] <= tasa_me_lte]

        # Ordenar
        if sort_by and sort_by in filtered_df.columns:
            ascending = sort_order == 'asc'
            filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending)
        
        return filtered_df

    def get_tarifarios(self, 
                       skip: int = 0, 
                       limit: int = 20, 
                       **kwargs) -> Dict:
        """Filtra, ordena y pagina los datos del DataFrame."""
        
        filtered_df = self._get_filtered_df(**kwargs)

        if filtered_df is None or filtered_df.empty:
            return {"total_items": 0, "items": [], "total_pages": 0, "current_page": 1}

        total_items = len(filtered_df)
        total_pages = (total_items + limit - 1) // limit
        current_page = (skip // limit) + 1

        # Paginar
        paginated_df = filtered_df.iloc[skip:skip + limit]

        # Limpieza final y explícita para asegurar compatibilidad con JSON
        paginated_df = paginated_df.astype(object).where(pd.notna(paginated_df), None)

        return {
            "total_items": total_items,
            "items": jsonable_encoder(paginated_df.to_dict(orient="records")),
            "total_pages": total_pages,
            "current_page": current_page
        }