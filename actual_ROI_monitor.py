import json
import modelop.utils as utils

logger = utils.configure_logger()


# modelop.init
def begin() -> None:
    """
    A function to set model-specific global variables used in ROI computations.
    """
    
    with open("modelop_parameters.json", "r") as parameters_file:
        modelop_parameters = json.load(parameters_file)
    
    ROI_parameters = modelop_parameters["monitoring"]["business_value"]["ROI"]
    logger.info("ROI parameters: %s", ROI_parameters)

    global amount_field, label_field, score_field
    global cost_multipliers
    global positive_class_label

    amount_field = ROI_parameters["amount_field"] # Column containing transaction amount
    score_field = ROI_parameters["score_field"] # Column containing model prediction
    label_field = ROI_parameters["label_field"] # Column containing ground_truth
        
    # ROI cost multipliers for each classification case
    cost_multipliers = ROI_parameters["cost_multipliers"]

    # Read and set label of positive class
    try:
        positive_class_label = modelop_parameters["monitoring"]["performance"]["positive_class_label"]
        logger.info("Label of Positive Class: %s", positive_class_label)
    except KeyError:
        raise KeyError("model parameters should define label of positive class!")


# modelop.metrics
def metrics(dataframe) -> dict:
    """
    A Function to classify records & compute actual ROI given a labeled & scored DataFrame.

    Args:
        dataframe (pd.DataFrame): Slice of Production data

    Yields:
        dict: Test Result containing actual roi metrics
    """

    # Classify each record in dataframe
    for idx in range(len(dataframe)):
        if dataframe.iloc[idx][label_field] == dataframe.iloc[idx][score_field]:
            dataframe["record_class"] = (
                "TP" if dataframe.iloc[idx][label_field] == positive_class_label else "TN"
            )
        elif dataframe.iloc[idx][label_field] < dataframe.iloc[idx][score_field]:
            dataframe["record_class"] = "FP"
        else:
            dataframe["record_class"] = "FN"

    # Compute actual ROI
    actual_roi = compute_actual_roi(dataframe)

    yield {
        "actual_roi": actual_roi,
        "amount_field": amount_field,
        "business_value": [
            {
                "test_name": "Actual ROI",
                "test_category": "business_value",
                "test_type": "actual_roi",
                "test_id": "business_value_actual_roi",
                "values": {
                    "actual_roi": actual_roi,
                    "amount_field": amount_field,
                    "cost_multipliers": cost_multipliers,
                },
            }
        ],
    }


def compute_actual_roi(data) -> float:
    """
    Helper function to compute actual ROI.

    Args:
        data (pd.DataFrame): Input DataFrame containing record_class

    Returns:
        float: actual ROI
    """

    actual_roi = 0
    for idx in range(len(data)):
        actual_roi += (
            data.iloc[idx][amount_field]
            * cost_multipliers[data.iloc[idx]["record_class"]]
        )

    return round(actual_roi, 2)
