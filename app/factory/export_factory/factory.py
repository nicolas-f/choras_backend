import io

from typing import List

from app.factory.export_factory.export_xlsx import ExportExcel
from app.factory.export_factory.export_parameters import ExportParameters
from app.factory.export_factory.export_edc import ExportEdc
from app.factory.export_factory.export_auralization import ExportAuralization


class ExportFactory:
    strategies = {
        "xlsx": ExportExcel(),
        "Parameters": ExportParameters(),
        "EDC": ExportEdc(),
        "Auralization": ExportAuralization(),
    }

    @staticmethod
    def get_exporter(export_type: str, params: List, simulationId: List, zip_buffer: io.BytesIO) -> io.BytesIO:
        strategy = ExportFactory.strategies.get(export_type, None)
        return strategy.export(export_type, params, simulationId, zip_buffer)
