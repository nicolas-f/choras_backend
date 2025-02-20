from app.services.export_factory.export_parameters import ExportParameters
from app.services.export_factory.export_edc import ExportEdc


class ExportFactory:
    strategies = {
        "Parameters": ExportParameters(),
        "EDC": ExportEdc(),
        # "auralization": NewResultsExport(),
    }

    @staticmethod
    def get_exporter(export_type, params, simulationId, zip_buffer):
        strategy = ExportFactory.strategies.get(export_type, None)
        return strategy.export(export_type, params, simulationId, zip_buffer)
    
    

    # def get_export_types -> array of export_type


