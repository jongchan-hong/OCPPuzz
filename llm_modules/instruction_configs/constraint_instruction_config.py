from typing import List, Optional

from parser_modules.parser import Parser
from dto.constraint_collect_dto import AdditionalPageRequest
from dto.gpt_retry_dto import GPTRetryDTO
from dto.instruction_message_dto import InstructionMessageDTO
from storage.entity.attribute_entity import AttributeEntity
from storage.entity.base_entity import session
from storage.entity.rule_collect_entity import RuleCollectEntity
from storage.entity.gpt_rule_collect_log_entity import GPTRuleCollectLogEntity
from storage.entity.operator_entity import OperatorEntity
from llm_modules.instruction_configs.instruction_config import InstructionConfig
from exception.gpt_exception_interface import GPTExceptionInterface
import json
from parser_modules.s3_upload_config_dto import S3UploadConfigDTO


class ConstraintInstructionConfig(InstructionConfig):

    def __init__(self, content: str, parser:Parser, gpt_retry_dto: Optional[GPTRetryDTO] = None, additional_page_request_list: Optional[ List[AdditionalPageRequest]] = None, s3_config: S3UploadConfigDTO = None):
        self.content = content
        self.temperature = 0.2
        self.gpt_retry_dto = gpt_retry_dto
        self.additional_page_request_list = additional_page_request_list
        self.s3_config = s3_config
        self.model = "gpt-4o"
        self.timeout = 120
        self.end_mark = "[IMPOSSIBLE]"

        self.system_instructions = "Extract constraints from OCPP message specifications and represent them as structured JSON rules."

        self.developer_table_of_contents = (
            "Before extracting any constraints, you MUST first refer to the table of contents of both the Specification and Appendix documents "
            "to determine if additional content is needed for the current object. "
            "If the current object_name is `TransactionEventRequest` or `TransactionType`, you MUST actively review the Specification Table of Contents to locate any sections related to transactions or message field clarification. This includes sections like “Clarification for optional fields in TransactionEventRequest.” If any relevant section exists in the table of contents, include an `additional_page_request_list` targeting that section’s page range"
            "Do NOT make assumptions or fabricate constraints based on prior examples or domain intuition. "
            "If all possible rules have been extracted from the referenced pages and previous results, respond with [IMPOSSIBLE].\n\n"

            "**Note:** If the `object_name` is `TransactionEventRequest` or `TransactionType`, you are REQUIRED to check the Specification table of contents "
            "and request relevant content. These objects involve conditional logic and temporal relationships that cannot be inferred solely from field-level descriptions.\n\n"

            "**IMPORTANT:** Even when additional content is required, you MUST extract any rules that can be immediately derived from the provided object description, field descriptions, or references. "
            "Do NOT skip rule extraction just because additional_page_request_list is included."
        )

        self.developer_rule_instructions = [
            "The purpose of this prompt is to extract constraints based on OCPP message information. Do not format the response with ```json or any other code block notation. Return raw JSON data only."
            "Rules:",
            "0. Do not generate or infer causes, constraints, or conditions based solely on example patterns! Only produce outputs based on actual input content or explicitly provided supplemental materials (e.g., base64 images or document page requests).",
            "1. The response must strictly follow the predefined JSON format.",
            "2. [values] must be an array of single values, not an object.",
            "3. `attribute` and `operator` should maintain consistency and match the provided values exactly. - If an exact match is not found, new entries may be added when necessary.",
            "4. If a certain value (e.g., ENUM, specific numeric/string value) affects the constraints of another field, make sure to include it.",
            "5. Since the goal is to identify non-trivial corner cases, make sure to include relevant details for this purpose.",
            '6. Do not combine independent constraints into a single rule. Each constraint should have its own entry in the "rules" list.',
            "7. Ensure that cases similar to the ones in the provided examples are fully included. Any similar patterns or dependencies should be reflected in the response.",
            "8. Only generate new rules that have not been mentioned in previous responses. If there are no more new rules to generate, including those from previous responses, return '"+self.end_mark+"' instead.",
            "9. Use standard operators instead of 'custom' whenever possible.",
            "10. Do not guess the fields of condition, and if there is no way to express them, do not provide any suggestion.",
            "11. If the field or section being referenced matches one of the standardized types shown in the examples (e.g., from the reference appendix), you must use the exact standardized naming convention. For instance: use 'Appendix.StandardizedVariables.Names' for variable names, 'Appendix.StandardizedComponents.Names' for component names, 'Appendix.StandardizedUnitsOfMeasure.Values' for measurement units, and 'Appendix.SecurityEvents.Names' for security event types. If the intent of the field clearly aligns with one of these categories, return the appropriate standardized key exactly as shown. Do not invent new naming formats or variations.",
            "12. If a constraint applies based on the OCPP Variable context rather than a specific field value, use a 'variable' object instead of 'field'. The 'variable' must include both 'componentName' and 'variableName', and follow the format: variable.[ComponentName].[VariableName] (e.g., variable.SmartChargingCtrlr.ACPhaseSwitchingSupported). If the constraint applies to a message field instead, use a 'field' object following the format: field.[FieldName] (e.g., field.type). Do not mix 'field' and 'variable' in the same rule.",
            "13. If additional information is required to extract a rule, you must request the relevant document section explicitly. This should be returned using the 'additional_page_request_list' field in the response JSON. Use the format: \"additional_page_request\": [{\"document\": \"Specification\" or \"Appendix\", \"page_range\": {\"start\": <start_page>, \"end\": <end_page>}}]. Multiple entries may be included if needed. Do not guess or infer beyond the specified pages.",
            "14. The cause name 'img_data' must only be used when the constraint is derived from explicitly provided image data (via additional_page_request_list). If no such image is included in the current request, do not use 'img_data' as a cause.",
            "15. Do NOT repeat any rule that was previously generated and included under `Here is the previous response...`. "
            "You must treat previous responses as *strictly immutable*. Repeating rules will be considered a failure."
        ]

        self.developer_attribute = "Attribute: " + ", ".join(attribute.value for attribute in session.query(AttributeEntity))
        self.developer_operator = "Operator: " + ", ".join(operator.value for operator in session.query(OperatorEntity))
        self.developer_reference_variables = f"Reference Variables: {parser.referenced_components_and_variables_parser.get_instruction_content()}"
        self.developer_table_of_contents_spec = f"Specification File Table of Contents: {parser.table_of_contents_from_specification_parser.get_instruction_content()}"
        self.developer_table_of_contents_appendix = f"Appendix File Table of Contents: {parser.table_of_contents_from_appendices_parser.get_instruction_content()}"

        affect_case = "\n".join([
            "## Case : Affects the constraints of another field",
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "idToken", "field_description": "Required. IdToken is case insensitive. Might hold the hidden id of an RFID tag, but can for example also contain a UUID.", "json_description": "IdToken is case insensitive. Might hold the hidden id of an RFID tag, but can for example also contain a UUID."}, {"name": "type", "field_description": "Required. Enumeration of possible idToken types.", "reference": {"enumMembers": [{"name": "Central", "field_description": "A centrally, in the CSMS (or other server) generated id (for example used for a remotely started transaction that is activated by SMS). No format defined, might be a UUID."}, {"name": "ISO14443", "field_description": "ISO 14443 UID of RFID card. It is represented as an array of 4 or 7 bytes in hexadecimal representation."}]}}]}',
            'Output:\n{"rules":[{"name":"TestObject.idToken","rules":[{"causes":[ {"name":"TestObject.idToken.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}},{"causes":[{"name":"TestObject.type.ISO14443.field_description","sentence":"ISO 14443 UID of RFID card. It is represented as an array of 4 or 7 bytes in hexadecimal representation."}],"conditions":[{"target":"field.type","attribute":"values","operator":"equal","values":["ISO14443"]}],"constraint":{"attribute":"bytes","operator":"either","values":[4,7]}},{"causes":[{"name":"TestObject.type.ISO14443.field_description","sentence":"ISO 14443 UID of RFID card. It is represented as an array of 4 or 7 bytes in hexadecimal representation."}],"conditions":[{"target":"field.type","attribute":"values","operator":"equal","values":["ISO14443"]}],"constraint":{"attribute":"format","operator":"equal","values":["hexadecimal"]}}]},{"name":"TestObject.type","rules":[{"causes":[ {"name":"TestObject.type.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}'
        ])

        inferring_value_restrictions_case = "\n".join([
            "## Case : Inferring Value Restrictions",
            'Input:\n{"object_name": "TestRequest", "object_description": "", "json_description": "", "fields": [{"name": "evseId", "field_description": "Optional. The charging schedule contained in this notification applies to an EVSE. evseId must be > 0.", "json_description": "The charging schedule contained in this notification applies to an EVSE. evseId must be &gt; 0."}]}',
            'Output:\n{"rules":[{"name":"TestRequest.evseId","rules":[{"causes":[{"name":"TestRequest.evseId.field_description","sentence":"Optional."}],"constraint":{"attribute":"optional","operator":"equal","values":["true"]}},{"causes":[{"name":"TestRequest.evseId.field_description","sentence":"evseId must be > 0."}, {"name":"TestRequest.evseId.json_description","sentence":"evseId must be > 0."}],"constraint":{"attribute":"values","operator":"gt","values":[0]}}]}]}',
        ])

        restrict_fraction_digits_case = "\n".join([
            "## Case : Restrict Fraction Digits",
            'Input:\n{"name":"TestRequest","object_description":"","fields":[{"name": "limit", "field_description": "Required. Charging rate limit during the schedule period, in the applicable chargingRateUnit, for example in Amperes (A) or Watts (W). Accepts at most one digit fraction (e.g. 8.1).", "json_description": "Charging_ Schedule_ Period. Limit. Measure urn:x-oca:ocpp:uid:1:569241 Charging rate limit during the schedule period, in the applicable chargingRateUnit, for example in Amperes (A) or Watts (W). Accepts at most one digit fraction (e.g. 8.1). "}]}',
            'Output:\n{"rules":[{"name":"TestRequest.limit","rules":[{"causes":[{"name":"TestRequest.limit.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}},{"causes":[{"name":"TestRequest.limit.field_description","sentence":"Accepts at most one digit fraction (e.g. 8.1)."},{"name":"TestRequest.limit.json_description","sentence":"Accepts at most one digit fraction (e.g. 8.1)."}],"constraint":{"attribute":"decimalPlaces","operator":"max","values":[1]}}]}]}',
        ])

        fixed_set_of_allowed_values_case = "\n".join([
            "## Case : Fixed Set of Allowed Values Case",
            'Input:\n{"object_name": "TestRequest", "object_description": "", "json_description": "", "fields": [{"name": "type", "field_description": "Required. Type of the security event. This value should be taken from the Security events list.", "json_description": "Type of the security event. This value should be taken from the Security events list."}]}',
            'Output:\n{"rules":[{"name":"TestRequest.type","rules":[{"causes":[{"name":"TestRequest.type.field_description","sentence":"This value should be taken from the Security events list."},{"name":"TestRequest.type.json_description","sentence":"This value should be taken from the Security events list."}],"constraint":{"attribute":"value","operator":"from","values":["Appendix.SecurityEvents.Names"]}},{"causes":[{"name":"TestRequest.type.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}',
        ])

        enforcing_data_format_case = "\n".join([
            "## Case : Enforcing Data Format",
            'Input:\n{"object_name": "TestRequest", "object_description": "", "json_description": "", "fields": [{"name": "csr", "field_description": "Required. The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986 [22] and then PEM encoded, using the TestRequest message.", "json_description": "The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986 [22] and then PEM encoded, using the &lt;&lt;TestRequest,TestRequest&gt;&gt; message."}]}',
            'Output:\n{"rules":[{"name":"TestRequest.csr","rules":[{"causes":[{"name":"TestRequest.csr.field_description","sentence":"The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986"}, {"name":"TestRequest.csr.json_description","sentence":"The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986"}],"constraint":{"attribute":"format","operator":"equal","values":["RFC 2986"]}},{"causes":[{"name":"TestRequest.csr.field_description","sentence":"The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986 [22] and then PEM encoded"}, {"name":"TestRequest.csr.json_description","sentence":"The Charging Station SHALL send the public key in form of a Certificate Signing Request (CSR) as described in RFC 2986 [22] and then PEM encoded"}],"constraint": {"attribute":"encoding","operator":"equal","values":["PEM"]}},{"causes":[{"name":"TestRequest.csr.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}',
        ])

        restricting_to_conceptual_values_case = "\n".join([
            "## Case : Restricting to Conceptual Values",
            'Input:\n{"object_name": "TestRequest", "object_description": "", "json_description": "", "fields": [{"name": "iso15118SchemaVersion", "field_description": "Required. Schema version currently used for the 15118 session between EV and Charging Station. Needed for parsing of the EXI stream by the CSMS.", "json_description": "Schema version currently used for the 15118 session between EV and Charging Station. Needed for parsing of the EXI stream by the CSMS."}]}',
            'Output:\n{"rules":[{"name":"TestRequest.iso15118SchemaVersion","rules":[{"causes":[{"name":"TestRequest.iso15118SchemaVersion.name","sentence":"iso15118SchemaVersion"}],"constraint":{"attribute": "specification","operator":"in","values": ["ISO 15118 schema versions"]}},{"causes":[{"name":"TestRequest.iso15118SchemaVersion.field_description","sentence":"Required."}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}',
        ])

        url_format_case = "\n".join([
            "## Case : URL Format",
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "responderURL", "field_description": "This contains the responder URL (Case  insensitive).", "json_description": "This contains the responder URL (Case insensitive)."}]}',
            'Output:\n{"rules":[{"name":"TestObject.responderURL","rules":[{"causes":[ {"name":"TestObject.responderURL.field_description","sentence":"This contains the responder URL (Case insensitive)."}, {"name":"TestObject.responderURL.json_description","sentence":"This contains the responder URL (Case insensitive)."}],"constraint":{"attribute":"format","operator":"equal","values":["url"]}},{"causes": [{"name": "TestObject.responderURL.field_description", "sentence": "This contains the responder URL (Case insensitive)."}, {"name": "TestObject.responderURL.json_description", "sentence": "This contains the responder URL (Case insensitive)."}], "conditions": [], "constraint": {"attribute": "case", "operator": "equal", "values": ["insensitive"]}}]}]}',
        ])

        hex_clean_format_case = "\n".join([
            "## Case : Hex Clean Format",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "serialNumber", "field_description": "The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes.", "json_description": "The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}]}',
            'Output:\n{"rules":[{"name":"TestObject.serialNumber","rules":[{"causes":[ {"name":"TestObject.serialNumber.field_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}, {"name":"TestObject.serialNumber.json_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}],"constraint":{"attribute": "format", "operator": "equal", "values": ["hexadecimal"]}},{"causes":[ {"name":"TestObject.serialNumber.field_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}, {"name":"TestObject.serialNumber.json_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}],"constraint":{"attribute": "prefix", "operator": "notEqual", "values": ["0x"]}},{"causes":[ {"name":"TestObject.serialNumber.field_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}, {"name":"TestObject.serialNumber.json_description","sentence":"The string representation of the hexadecimal value of the serial number without the prefix \"0x\" and without leading zeroes."}],"constraint":{"attribute": "leadingZeros", "operator": "equal", "values": ["false"]}}]}]}',
        ])

        remove_field_case = "\n".join([
            "## Case : Remove Field Case (only when the field must be strictly removed and cannot be present under any circumstances.)",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "phaseToUse", "field_description": "Used if numberPhases=1 and if the EVSE is capable of switching the phase connected to the EV, i.e. ACPhaseSwitchingSupported is defined and true. It’s not allowed unless both conditions above are true.", "json_description": "Used if numberPhases=1 and if the EVSE is capable of switching the phase connected to the EV, i.e. ACPhaseSwitchingSupported is defined and true. It’s not allowed unless both conditions above are true."}]}',
            'Output:\n{"rules":[{"name":"TestObject.phaseToUse","rules":[{"causes":[ {"name":"TestObject.phaseToUse.field_description","sentence":"Used if numberPhases=1 and if the EVSE is capable of switching the phase connected to the EV, i.e. ACPhaseSwitchingSupported is defined and true. It’s not allowed unless both conditions above are true."}, {"name":"TestObject.phaseToUse.json_description","sentence":"Used if numberPhases=1 and if the EVSE is capable of switching the phase connected to the EV, i.e. ACPhaseSwitchingSupported is defined and true. It’s not allowed unless both conditions above are true."}],"conditions":[{"target":"field.numberPhases","attribute":"values","operator":"notEqual","values":["1"]}],"constraint":{"attribute":"removeField","operator":"equal","values":["true"]}}]}]}',
        ])

        contrapositive_case = "\n".join([
            "## Case : Contrapositive Case",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "iso15118CertificateHashData", "field_description": "Not needed if certificate is provided.", "json_description": "Not needed if certificate is provided."}]}',
            'Output:\n{"rules":[{"name":"TestObject.iso15118CertificateHashData","rules":[{"causes":[ {"name":"TestObject.iso15118CertificateHashData.field_description","sentence":"Not needed if certificate is provided."}, {"name":"TestObject.iso15118CertificateHashData.json_description","sentence":"Not needed if certificate is provided."}],"conditions":[{"target":"field.certificate","attribute":"provided","operator":"equal","values":["false"]}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}',
        ])

        characterSet_in_case = "\n".join([
            "## Case : characterSet in Case",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "identifierString", "field_description": "This is a case-insensitive dataType and can only contain characters from the following character set: a-z, A-Z, 0-9, \'*\', \'-\', \'_\', \'=\', \':\', \'+\', \'|\', \'@\', \'.\'"}]}',
            'Output:\n{"rules":[{"name":"TestObject.identifierString","rules":[{"causes":[ {"name":"TestObject.identifierString.field_description","sentence":"This is a case-insensitive dataType and can only contain characters from the following character set: a-z, A-Z, 0-9, \'*\', \'-\', \'_\', \'=\', \':\', \'+\', \'|\', \'@\', \'.\'"}],"conditions":[],"constraint":{"attribute":"characterSet","operator":"in","values":["a-z", "A-Z", "0-9", "*", "-", "_", "=", ":", "+", "|", "@", "."]}}]}]}',
        ])

        bit_case = "\n".join([
            "## Case : Bit Case",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "integer", "field_description": "32 bit (31 bit resolution, 1 sign bit)\n No leading 0’s  \n No plus sign Allowed value examples: 1234, -1234 \n Not Allowed: 01234, +1234"}]}',
            'Output:\n{"rules":[{"name":"TestObject.integer","rules":[{"causes":[ {"name":"TestObject.integer.field_description","sentence":"32 bit (31 bit resolution, 1 sign bit)"}],"conditions":[],"constraint":{"attribute":"bit","operator":"equal","values":["32"]}}, {"causes":[ {"name":"TestObject.integer.field_description","sentence":"No leading 0’s"}],"conditions":[],"constraint":{"attribute": "leadingZeros", "operator": "equal", "values": ["false"]}}, {"causes":[ {"name":"TestObject.integer.field_description","sentence":"No plus sign Allowed value examples: 1234, -1234 \n Not Allowed: 01234, +1234"}],"conditions":[],"constraint":{"attribute": "prefix", "operator": "notEqual", "values": ["+"]}}]}]}',
        ])

        value_from_appendices = "\n".join([
            "## Case : Value from Appendices Case",
            'Input:\n{"object_name": "TestObject", "object_description": "test description", "json_description": "", "fields": [{"name": "unit", "field_description": "Optional. Unit of the value. Default = \"Wh\" if the (default) measurand is an \"Energy\" type. This field SHALL use a value from the list Standardized Units of Measurements in Part 2 Appendices. If an applicable unit is available in that list, otherwise a \"custom\" unit might be used."}]}',
            'Output:\n{"rules":[{"name":"TestObject.unit","rules":[{"causes":[ {"name":"TestObject.unit.field_description","sentence":"This field SHALL use a value from the list Standardized Units of Measurements in Part 2 Appendices."}],"conditions":[],"constraint":{"attribute":"value","operator":"from","values":["Appendix.StandardizedUnitsOfMeasure.Values"]}}]}]}',
        ])

        format_content_relation = "\n".join([
            '## Case : Format Content Relation Case',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "format", "field_description": "Required. Format of the message.", "reference": {"enumMembers": [{"name": "ASCII", "field_description": "Message content is ASCII formatted, only printable ASCII allowed."},{"name": "HTML", "field_description": "Message content is HTML formatted."},{"name": "URI", "field_description": "Message content is URI that Charging Station should download and use to display. for example a HTML page to be shown in a web-browser."}]}}, {"name": "content", "field_description": " Required. Message contents."}]}',
            'Output:\n{"rules":[{"name":"TestObject.content","rules":[{"causes":[ {"name":"TestObject.format.ASCII.field_description","sentence":"Message content is ASCII formatted, only printable ASCII allowed."}],"conditions":[{"target":"field.format","attribute":"values","operator":"equal","values":["ASCII"]}],"constraint":{"attribute":"format","operator":"equal","values":["ASCII"]}},{"causes":[ {"name":"TestObject.format.HTML.field_description","sentence":"Message content is HTML formatted."}],"conditions":[{"target":"field.format","attribute":"values","operator":"equal","values":["HTML"]}],"constraint":{"attribute":"format","operator":"equal","values":["HTML"]}},{"causes":[ {"name":"TestObject.format.URI.field_description","sentence":"Message content is URI that Charging Station should download and use to display. for example a HTML page to be shown in a web-browser."}],"conditions":[{"target":"field.format","attribute":"values","operator":"equal","values":["URI"]}],"constraint":{"attribute":"format","operator":"equal","values":["URI"]}}]}]}',
        ])

        configured_by_variable = "\n".join([
            '## Case : configured by variable Case',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "eventType", "field_description": "Required. This contains the type of this event. The first TransactionEvent of a transaction SHALL contain: \"Started\" The last TransactionEvent of a transaction SHALL contain: \"Ended\" All others SHALL contain: \"Updated\"", "reference": {"enumMembers": [{"name": "Ended", "field_description": "Last event of a transaction"},{"name": "Started", "field_description": "First event of a transaction."},{"name": "Updated", "field_description": "Transaction event in between \'Started\' and \'Ended\'."}]}}, {"name": "meterValue", "field_description": "Optional. This contains the relevant meter values. Depending on the EventType of this TransactionEvent the following Configuration Variable is used to configure the content: Started:SampledDataTxStartedMeasurands Updated: SampledDataTxUpdatedMeasurands Ended: SampledDataTxEndedMeasurands & AlignedDataTxEndedMeasurands"}]}',
            'Output:\n{"rules":[{"name":"TestObject.meterValue","rules":[{"causes":[ {"name":"TestObject.meterValue.field_description","sentence":"Depending on the EventType of this TransactionEvent the following Configuration Variable is used to configure the content: Started: SampledDataTxStartedMeasurands Updated: SampledDataTxUpdatedMeasurands Ended: SampledDataTxEndedMeasurands & AlignedDataTxEndedMeasurands"}],"conditions":[{"target":"field.eventType","attribute":"values","operator":"equal","values":["Started"]}],"constraint":{"attribute":"contentConfiguredBy","operator":"equal","values":["variable.SampledDataCtrlr.TxStartedMeasurands"]}}, {"causes":[ {"name":"TestObject.meterValue.field_description","sentence":"Depending on the EventType of this TransactionEvent the following Configuration Variable is used to configure the content: Started: SampledDataTxStartedMeasurands Updated: SampledDataTxUpdatedMeasurands Ended: SampledDataTxEndedMeasurands & AlignedDataTxEndedMeasurands"}],"conditions":[{"target":"field.eventType","attribute":"values","operator":"equal","values":["Updated"]}],"constraint":{"attribute":"contentConfiguredBy","operator":"equal","values":["variable.SampledDataCtrlr.TxUpdatedMeasurands"]}}, {"causes":[ {"name":"TestObject.meterValue.field_description","sentence":"Depending on the EventType of this TransactionEvent the following Configuration Variable is used to configure the content: Started: SampledDataTxStartedMeasurands Updated: SampledDataTxUpdatedMeasurands Ended: SampledDataTxEndedMeasurands & AlignedDataTxEndedMeasurands"}],"conditions":[{"target":"field.eventType","attribute":"values","operator":"equal","values":["Ended"]}],"constraint":{"attribute":"contentConfiguredBy","operator":"in","values":["variable.SampledDataCtrlr.TxEndedMeasurands","variable.AlignedDataCtrlr.TxEndedMeasurands"]}}]}]}',
        ])

        sending_depends_on_variable = "\n".join([
            '## Case : sending depends on case',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "publicKey", "field_description": "Required. Base64 encoded, sending depends on  configuration variable PublicKeyWithSignedMeterValue."}]}',
            'Output:\n{"rules":[{"name":"TestObject.publicKey","rules":[{"causes":[ {"name":"TestObject.publicKey.field_description","sentence":"sending depends on configuration variable _PublicKeyWithSignedMeterValue_."}],"conditions":[{"target":"variable.OCPPCommCtrlr.PublicKeyWithSignedMeterValue","attribute":"values","operator":"equal","values":["Never"]}],"constraint":{"attribute":"values","operator":"equal","values":[""]}}, {"causes":[ {"name":"TestObject.publicKey.field_description","sentence":"sending depends on configuration variable _PublicKeyWithSignedMeterValue_."}],"conditions":[{"target":"variable.OCPPCommCtrlr.PublicKeyWithSignedMeterValue","attribute":"values","operator":"equal","values":["OncePerTransaction"]}, {"target":"context.hasSentPublicKeyBefore", "attribute":"values","operator":"equal","values":["true"]}],"constraint":{"attribute":"values","operator":"equal","values":[""]}}, {"causes":[ {"name":"TestObject.publicKey.field_description","sentence":"sending depends on configuration variable _PublicKeyWithSignedMeterValue_."}],"conditions":[{"target":"variable.OCPPCommCtrlr.PublicKeyWithSignedMeterValue","attribute":"values","operator":"equal","values":["EveryMeterValue"]}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]}]}',
        ])

        was_provided_in = "\n".join([
            '## Case : was provided in case ',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "requestId", "field_description": "The id of the GetReportRequest or GetBaseReportRequest that requested this report"}]}',
            'Output:\n{"rules":[{"name":"TestObject.requestId","rules":[{"causes":[ {"name":"TestObject.requestId.field_description","sentence":"The id of the GetReportRequest or GetBaseReportRequest that requested this report"}],"conditions":[],"constraint":{"attribute":"wasProvidedIn","operator":"or","values":["GetReportRequest","GetBaseReportRequest"]}}]}]}',
        ])

        triggered_by_fix_enum_case = "\n".join([
            '## Case : TriggerMessageRequest fix enum case',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "reason", "field_description": "This contains the reason for sending this message to the CSMS.", "reference": {"enumMembers": [{"name": "Triggered", "field_description": "Requested by the CSMS via a TriggerMessage"}]}},{"name": "context", "field_description": " Type of detail value: start, end or sample. Default = \"Sample.Periodic\"", "reference": {"enumMembers": [{"name": "Trigger", "field_description": "Value taken in response to TriggerMessageRequest."}]}},{"name": "triggerReason", "field_description": "Reason the Charging Station sends this  message to the CSMS", "reference": {"enumMembers": [{"name": "Trigger", "field_description": "Requested by the CSMS via a TriggerMessageRequest."},{"name": "RemoteStart", "field_description": "A RequestStartTransactionRequest has been sent."},{"name": "RemoteStop", "field_description": "A RequestStopTransactionRequest has been sent."}]}}]}',
            'Output:\n{"rules":[{"name":"TestObject.reason","rules":[{"causes":[ {"name":"TestObject.reason.Triggered.field_description","sentence":"Requested by the CSMS via a TriggerMessage"}],"conditions":[ {"attribute":"triggeredBy","operator":"equal","values":["TriggerMessageRequest"]}],"constraint":{"attribute":"value","operator":"equal","values":["Triggered"]}}]},{"name":"TestObject.context","rules":[{"causes":[ {"name":"TestObject.context.Trigger.field_description","sentence":"Value taken in response to TriggerMessageRequest."}],"conditions":[ {"attribute":"triggeredBy","operator":"equal","values":["TriggerMessageRequest"]}],"constraint":{"attribute":"value","operator":"equal","values":["Trigger"]}}]},{"name":"TestObject.triggerReason","rules":[{"causes":[ {"name":"TestObject.triggerReason.Trigger.field_description","sentence":"Requested by the CSMS via a TriggerMessageRequest."}],"conditions":[ {"attribute":"triggeredBy","operator":"equal","values":["TriggerMessageRequest"]}],"constraint":{"attribute":"value","operator":"equal","values":["Trigger"]}}, {"causes":[ {"name":"TestObject.triggerReason.RemoteStart.field_description","sentence":"A RequestStartTransactionRequest has been sent."}],"conditions":[ {"attribute":"triggeredBy","operator":"equal","values":["RequestStartTransactionRequest"]}],"constraint":{"attribute":"value","operator":"equal","values":["RemoteStart"]}}, {"causes":[ {"name":"TestObject.triggerReason.RemoteStop.field_description","sentence":"A RequestStopTransactionRequest has been sent."}],"conditions":[ {"attribute":"triggeredBy","operator":"equal","values":["RequestStopTransactionRequest"]}],"constraint":{"attribute":"value","operator":"equal","values":["RemoteStop"]}}]}]}',
        ])

        remote_id_was_provided_in = "\n".join([
            '## Case : remoteId was provided in case',
            'Input:\n{"object_name": "TestObject", "object_description": "", "json_description": "", "fields": [{"name": "remoteStartId", "field_description": "The ID given to remote start request(RequestStartTransactionRequest. This enables to CSMS to match the started transaction to the given start request."}]}',
            'Output:\n {"rules":[{"name":"TestObject.remoteStartId","rules":[{"causes":[ {"name":"TestObject.remoteStartId.field_description","sentence":"The ID given to remote start request(RequestStartTransactionRequest. This enables to CSMS to match the started transaction to the given start request."}],"conditions":[],"constraint":{"attribute":"wasProvidedIn","operator":"equal","values":["RequestStartTransactionRequest"]}}]}]}',
        ])

        content_request_from_table_of_contents_step1 = "\n".join([
            '## Case : Content Request from Table of Contents',
            'Input:\n{"object_name": "TestRequest", ...}',
            'Output:\n{',
            '  "rules": [',
            '    // 🚨 You MUST fill in any rules that can be derived from the current input.',
            '    // Do NOT leave this empty if any field or object description suggests constraints.',
            '  ],',
            '  "additional_page_request_list": [',
            '    {"document": "Specification", "page_range": {"start": 123, "end": 124}}',
            '  ]',
            '}'
        ])

        content_request_from_table_of_contents_step2 = "\n".join([
            '## Case : content request from table of contents (request)- Step 2 (after providing image)',
            'Input:\n{"object_name": "TestRequest", ...}',
            'Output:\n{"rules":[{"name":"TestRequest.evse","rules":[{"causes":[{"name":"img_data","sentence":"(E01.FR.16) The field evse is only provided in the first TestRequest that occurs after the EV has connected."}],"conditions":[{"target":"context","attribute":"isFirstTransactionEventAfterEVConnection","operator":"equal","values":["false"]}],"constraint":{"attribute":"removeField","operator":"equal","values":["true"]}}]},{"name":"TestRequest.idToken","rules":[{"causes":[{"name":"img_data","sentence":"(E03.FR.01) The field idToken is provided once in the first TestRequest that occurs after the transaction has\n been authorized.\n (E07.FR.02) The field idToken is provided once in the TestRequest that occurs when the authorization of the\n transaction has been ended."}],"conditions":[{"target":"context","attribute":"isFirstTransactionEventAfterAuthorization","operator":"equal","values":["false"]},{"target":"field.eventType","attribute":"values","operator":"notEqual","values":["Ended"]},{"target":"field.triggerReason","attribute":"values","operator":"notEqual","values":["StopAuthorized"]}],"constraint":{"attribute":"removeField","operator":"equal","values":["true"]}}]},{"name":"TestRequest.reservationId","rules":[{"causes":[{"name":"img_data","sentence":"The field reservationId is only provided in the first TransactionEventRequest that occurs when the transaction has been authorized by the idToken for which a reservation existed in the charging station."}],"constraint":{"attribute":"oncePerTransaction","operator":"equal","values":["true"]}}]}]}',
        ])

        content_request_from_table_of_contents_step2_object = "\n".join([
            '## Case : content request from table of contents (object) - Step 2 (after providing image)',
            'Input:\n{"object_name": "TestObject", ...}',
            'Output:\n{"rules":[{"name":"TestObject.chargingState","rules":[{"causes":[{"name":"img_data","sentence":"This implies that a TransactionEventRequest(eventType = Started) always has a chargingState, because the state goes from non-existent to a value."}],"conditions":[{"target":"context.eventType","attribute":"values","operator":"equal","values":["Started"]}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}},{"causes":[{"name":"img_data","sentence":"A TransactionEventRequest with triggerReason = ChargingStateChanged must contain chargingState."}],"conditions":[{"target":"context.triggerReason","attribute":"values","operator":"equal","values":["ChargingStateChanged"]}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}}]},{"name":"TestObject.stoppedReason","rules":[{"causes":[{"name":"img_data","sentence":"The stoppedReason must be provided in the TransactionEventRequest(eventType=Ended), unless the value is Local, in which case it may be omitted. The above also applies to transactions that are stopped by a RequestStopTransactionRequest, however in this case the stoppedReason value must be Remote."}],"conditions":[{"target":"context.eventType","attribute":"values","operator":"equal","values":["Ended"]},{"target":"context.chargingSession","attribute":"stoppedBy","operator":"equal","values":["RequestStopTransactionRequest"]}],"constraint":{"attribute":"required","operator":"equal","values":["true"]}},{"causes":[{"name":"img_data","sentence":"The stoppedReason must be provided in the TransactionEventRequest(eventType=Ended), unless the value is Local, in which case it may be omitted. The above also applies to transactions that are stopped by a RequestStopTransactionRequest, however in this case the stoppedReason value must be Remote."}],"conditions":[{"target":"context.eventType","attribute":"values","operator":"equal","values":["Ended"]},{"target":"context.chargingSession","attribute":"stoppedBy","operator":"equal","values":["RequestStopTransactionRequest"]}],"constraint":{"attribute":"values","operator":"equal","values":["Remote"]}}]},{"name":"TestObject.remoteStartId","rules":[{"causes":[{"name":"img_data","sentence":"The remoteStartId must be sent in the next TransactionEventRequest after the RequestStartTransactionRequest with the same remoteStartId."}],"constraint":{"attribute":"wasProvidedIn","operator":"equal","values":["RequestStartTransactionRequest"]}}]}]}',
        ])

        content_request_from_table_of_contents_step3 = "\n".join([
            '## Case : content request from table of contents (object, request) - Step 3 (after analyze)',
            'Input:\n{"object_name": "TestObject", ...}',
            'Output:\n[IMPOSSIBLE]',
        ])

        assistant_examples = [
            affect_case,
            inferring_value_restrictions_case,
            restrict_fraction_digits_case,
            fixed_set_of_allowed_values_case,
            enforcing_data_format_case,
            restricting_to_conceptual_values_case,
            url_format_case,
            hex_clean_format_case,
            remove_field_case,
            contrapositive_case,
            characterSet_in_case,
            bit_case,
            value_from_appendices,
            format_content_relation,
            configured_by_variable,
            sending_depends_on_variable,
            was_provided_in,
            remote_id_was_provided_in,
            content_request_from_table_of_contents_step1,
            content_request_from_table_of_contents_step2,
            content_request_from_table_of_contents_step2_object,
            content_request_from_table_of_contents_step3,
            triggered_by_fix_enum_case
        ]

        self.messages = [
            InstructionMessageDTO(role="system", content="\n".join(self.system_instructions)),
            InstructionMessageDTO(role="developer", content="\n".join(self.developer_rule_instructions)),
            InstructionMessageDTO(role="developer", content=self.developer_table_of_contents),
            InstructionMessageDTO(role="developer", content=self.developer_attribute),
            InstructionMessageDTO(role="developer", content=self.developer_operator),
            InstructionMessageDTO(role="developer", content=self.developer_reference_variables),
            InstructionMessageDTO(role="developer", content=self.developer_table_of_contents_spec),
            InstructionMessageDTO(role="developer", content=self.developer_table_of_contents_appendix),
            InstructionMessageDTO(role="assistant",content="\n\n".join(assistant_examples))
        ]

        if self.gpt_retry_dto:
            retry_content = f"# This question is a retry, and the response you previously provided is as follows: {self.gpt_retry_dto.error_content}"
            if isinstance(self.gpt_retry_dto.exception, GPTExceptionInterface):
                retry_content += "\n "+ self.gpt_retry_dto.exception.get_instruction_message_for_gpt()
            else:
                retry_content += "\n " + f"# Internal Error Occurred: {str(self.gpt_retry_dto.exception)}"
            self.messages.append(InstructionMessageDTO(role="developer", content=retry_content))
        if self.additional_page_request_list:
            additional_img_list = parser.get_select_page_img_list(self.additional_page_request_list, s3_config)
            unique_img_uris = list(set(additional_img_list))
            image_blocks = [
                {
                    "type": "image_url",
                    "image_url": {"url": image_data_uri}
                }
                for image_data_uri in unique_img_uris
            ]

            image_blocks.append({
                "type": "text",
                "text": "These images are the ones you requested in the previous conversation. Please analyze them for extracting additional constraints."
            })

            self.messages.append(
                InstructionMessageDTO(
                    role="user",
                    content=image_blocks
                )
            )
            print("image_blocks:", image_blocks)

        self.messages.append(InstructionMessageDTO(role="user", content=self.content))

    def append_previous_responses(self, object_name:str, rule_collect_entity:RuleCollectEntity):
        print("append_previous_responses init")
        print(f"rule_collect_id: {rule_collect_entity.id}")
        print(f"object_name: {object_name}")
        gpt_rule_collect_logs =  session.query(GPTRuleCollectLogEntity).filter_by(
            rule_collect_id=rule_collect_entity.id,
            object_name = object_name
        )
        print(f"logs size: {gpt_rule_collect_logs.count()}")
        if gpt_rule_collect_logs.count() > 0:
            print("previous messages.append init::")
            previous_content = "Here is the previous response. Use it for reference only — do not include it again in your response under any circumstances.:\n"
            previous_set = set()
            for log in gpt_rule_collect_logs:
                try:
                    parsed = json.loads(log.response)
                    compacted = json.dumps(parsed, separators=(",", ":"))
                    previous_set.add(compacted)
                except json.JSONDecodeError as e:
                    previous_set.add(log.response)

            for compacted in previous_set:
                previous_content += compacted + "\n"
            self.messages.append(InstructionMessageDTO(role="developer", content=previous_content))


