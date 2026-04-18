DEFAULT_SAMPLED_DATA_TX_UPDATED_MEASURANDS = "Energy.Active.Import.Register"
DEFAULT_SAMPLED_DATA_TX_STARTED_MEASURANDS = "Energy.Active.Import.Register"

def get_default_measurand(value):
    match value:
        case "variable.SampledDataCtrlr.TxStartedMeasurands":
            return DEFAULT_SAMPLED_DATA_TX_STARTED_MEASURANDS
        case "variable.SampledDataCtrlr.TxUpdatedMeasurands":
            return DEFAULT_SAMPLED_DATA_TX_UPDATED_MEASURANDS
        case _:
            return None