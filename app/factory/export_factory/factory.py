import io

from virtualenv.config.convert import ListType

from app.factory.export_factory.export_parameters import ExportParameters
from app.factory.export_factory.export_edc import ExportEdc
from app.factory.export_factory.export_auralization import ExportAuralization
from app.factory.export_factory.export_impulse_response import ExportImpulseResponse


class ExportFactory:
    strategies = {
        "Parameters": ExportParameters(),
        "EDC": ExportEdc(),
        "Auralization": ExportAuralization(),
        "ImpulseResponse": ExportImpulseResponse(),
    }

    @staticmethod
    def get_exporter(export_type:str, params:ListType, simulationId:ListType, zip_buffer:io.BytesIO)->io.BytesIO:
        strategy = ExportFactory.strategies.get(export_type, None)
        return strategy.export(export_type, params, simulationId, zip_buffer)



