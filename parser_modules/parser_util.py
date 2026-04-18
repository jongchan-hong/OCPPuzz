def is_class_point(config, word):
    return word["text"] == "Class" and round(word["x0"]) == config["coordinate"]["class_x"]

def is_field_point(config, word):
    return word["text"] == "Field" and round(word["x0"]) == config["coordinate"]["field_x"]

def is_value_point(config, word):
    return word["text"] == "Value" and round(word["x0"]) == config["coordinate"]["field_x"]