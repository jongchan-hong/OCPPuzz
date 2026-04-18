class ForceConditionException(Exception):
    def __init__(self, message:str, force_condition_list:list):
        super().__init__(message)
        self.force_condition_list = force_condition_list