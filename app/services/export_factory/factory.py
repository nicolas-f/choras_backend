from app.services.export_factory.export_parameters import ExportParameters


class ExportFactory:
    strategies = {
        "Parameters": ExportParameters(),
        # "plot": PlotExport(),
        # "auralization": NewResultsExport(),
    }

    @staticmethod
    def get_exporter(export_type, params, simulationId):
        parameter_strategy = ExportFactory.strategies.get(export_type, None)
        return parameter_strategy.export(params, simulationId)

    # def get_export_types -> array of export_type


