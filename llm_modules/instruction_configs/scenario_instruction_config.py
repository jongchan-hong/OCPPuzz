from typing import List, Optional

from sqlalchemy import desc

from parser_modules.parser import Parser
from dto.constraint_collect_dto import AdditionalPageRequest
from dto.gpt_retry_dto import GPTRetryDTO
from dto.instruction_message_dto import InstructionMessageDTO
from dto.scenario_page_dto import ScenarioPageDTO
from storage.entity.base_entity import session
from storage.entity.gpt_scenario_collect_log_entity import GPTScenarioCollectLogEntity
from storage.entity.scenario_collect_entity import ScenarioCollectEntity
from llm_modules.instruction_configs.instruction_config import InstructionConfig
from exception.gpt_exception_interface import GPTExceptionInterface
import textwrap
from parser_modules.s3_upload_config_dto import S3UploadConfigDTO
import json

class ScenarioInstructionConfig(InstructionConfig):

    def __init__(self, scenario_page_dto:ScenarioPageDTO, parser: Parser, gpt_retry_dto: Optional[GPTRetryDTO] = None,
                 additional_page_request_list: Optional[List[AdditionalPageRequest]] = None,
                 s3_config: S3UploadConfigDTO = None, scenario_collect_instructions = None, json_schemas = None):
        self.scenario_page_dto = scenario_page_dto
        self.parser = parser
        self.gpt_retry_dto = gpt_retry_dto
        self.additional_page_request_list = additional_page_request_list
        self.s3_config = s3_config
        self.temperature = 0.2
        self.model = "gpt-4o"
        self.timeout = 120
        self.end_mark = "[IMPOSSIBLE]"
        self.json_schemas = json_schemas
        self.system_instructions = "Extract scenario flows from OCPP descriptions and figures, and represent them as structured JSON data."

        self.developer_main_instructions = textwrap.dedent('''
        The following is an excerpt from the OCPP scenario documentation. Based on the provided information, extract the following elements:
        Do not format the response with ```json or any other code block notation. Return raw JSON data only.
        
        The description and the corresponding figure together define the complete scenario

        The output must follow this structure:
        - scenario_collect_list: a list of grouped scenario sequences under the same scenario name
          Each group must include:
          - description_type: one of the following:
                - "main": when the section is labeled as "Scenario description" or equivalent.
                - "alternative": only if explicitly labeled as "Alternative scenario(s)" in the document.
                - "combined": only if explicitly labeled as "Combined scenario description" in the document.
          - reference_value (optional): if the sequence is omitted and instead refers to another scenario (e.g., "See E09")
          - scenario_list: list of scenarios, or null if only a reference exists
          - pre_configuration_variable_list: a list of configuration variables that must be pre-set before executing the scenario. Use this to capture prerequisites such as "AuthCacheEnabled = true" or "TxStartPoint contains: DataSigned".
        
        Each individual scenario should include:
        - caller: the entity that sends the message (e.g., Charging Station, CSMS)
        - callee: the entity that receives the message
        - message: the name of the message being used (e.g., BootNotificationRequest)
        - fix_value_list: a list of fixed values that must appear in specific fields, expressed as {"name": field_name, "value": fixed_value}
            - Do not include values like `"Accepted/Rejected"` in `fix_value_list`. Only include fixed values that are clearly and unambiguously specified. If the value is ambiguous or listed as multiple possible outcomes, omit it.
            - For every TransactionEventRequest in the scenario_list, the eventType field must be explicitly included in the fix_value_list.
            - If eventType is not directly labeled in the diagram or table, you should still infer it based on context.
            - **Do not** include vague or ambiguous fixed values (e.g., `"status": "Accepted/Rejected"`). Only include field values that are explicitly required or constrained to a **single specific value**.
            - Do not insert arbitrary placeholder values such as "connectorId": "1", "evseId": "23", idToken = ABCD, or idToken.id = 1234 into fix_value_list. If the actual value is unclear or merely illustrative, omit the value field entirely and return only the field name, e.g., { "name": "connectorId" }.
            - Do not include field values in fix_value_list if they are only described as selectable from a list (e.g., "configurationSlot out of the valuesList"). Only include a field if its value is explicitly fixed to a single value, not a range, list, or conditionally chosen option.
            - In most cases:
                - If it is the first TransactionEventRequest of the transaction, assume eventType = "Started".
                - If it is the last one, especially followed by StatusNotification(connectorStatus=Unavailable), assume eventType = "Ended".
                - If it appears between those or is repeated periodically, assume eventType = "Updated"
        
        If the corresponding field name cannot be identified with certainty,
        do not include the message in scenario_list; instead, request its schema information via additional_schema_message_list.
                
        Note:
        - If multiple scenario descriptions (main and alternative) exist under the same scenario name, group them separately by description_type.
        - Maintain the **original order of appearance** in the `scenario_list`. Do not reorder or group messages.
        - Scenarios that only refer to another (e.g., "See E09", “B11 - Reset Without Ongoing Transaction” ...) should not include `scenario_list`, but may include `reference_value`.
        - When extracting scenario_list, always combine the message flows described in the Scenario description section and those explicitly shown in the figures below or on the following pages.
        - If a figure contains additional messages (e.g., TransactionEventRequest with eventType = Ended) that are not explicitly mentioned in the description, they must still be included in the scenario_list, preserving their order of appearance.
        - Description and the corresponding figure together define the complete scenario.
        
        ''')
        self.developer_prerequisite_instruction = textwrap.dedent('''
        Additional rules for handling Prerequisite(s):
        - If valid OCPP messages are found in the "Prerequisite(s)" section, insert them **at the beginning** of the `scenario_list`, before the main flow messages.
        - If the "Prerequisite(s)" section refers to another scenario (e.g., "See E09") **without describing message flow**, set scenario_list to null and store the reference in reference_value.
        - If the referenced scenario (e.g., "E09") **is not part of the current image**, but **is found in the Table of Contents**,  
          then also add its corresponding page range to additional_info_request.additional_page_request_list.
        - If prerequisite messages are ambiguous or incomplete (e.g., message name mentioned without direction or field context), treat them using the same inclusion criteria above.
        - If the Prerequisite section refers to another use case and the current page does not contain that use case’s definition or figure, do not attempt partial extraction. You must wait until the full content is available by requesting the appropriate page range.
        
        Handling Prerequisite References to Other Use Cases:

        If the scenario's "Prerequisite(s)" section refers to another use case (e.g., "Use case B09") without describing any OCPP message flow, follow this two-round procedure:
        
        First Round:
        - If the referenced use case is not included in the current image but exists in the Table of Contents, extract its page range from the Table of Contents.
        - Set scenario_collect_list to empty and return only additional_info_request.additional_page_request_list with the extracted page range.
        
        Second Round:
        - Check whether the requested additional_page_request_list from the previous round is included in the current request.
        - Do not request the same page range again as additional_page_request_list in this round.
        - If present, analyze the corresponding image(s).
        - If valid OCPP message flow is found, merge the extracted messages before the current scenario flow to construct a complete scenario that reflects the prerequisite dependency.
        ''')

        self.developer_textual_states_instructions = textwrap.dedent('''
        You are strictly required to extract and reflect all yellow annotation boxes shown in the figure — without exception.
        These annotations represent implicit OCPP states and must be interpreted into concrete message(s) in every applicable scenario, including both main and alternative.
        
        Matching Examples:
        "User authorization successful."
        → Insert Scenario:
        {
          "caller": "Charging Station",
          "callee": "CSMS",
          "message": "AuthorizeRequest"
        },
          "caller": "CSMS",
          "callee": "Charging Station",
          "message": "AuthorizeResponse",
          "fix_value_list": [
            { "name": "certificateStatus", "value": "Accepted" }
          ]
        }
        
        "User authorization successful and transaction is started"
        → Insert Scenario:
        {
          "caller": "Charging Station",
          "callee": "CSMS",
          "message": "AuthorizeRequest"
        },
          "caller": "CSMS",
          "callee": "Charging Station",
          "message": "AuthorizeResponse",
          "fix_value_list": [
            { "name": "certificateStatus", "value": "Accepted" }
          ]
        },
        {
          "caller": "Charging Station",
          "callee": "CSMS",
          "message": "TransactionEventRequest",
          "fix_value_list": [
            { "name": "eventType", "value": "Started" }
          ]
        },
        {
          "caller": "CSMS",
          "callee": "Charging Station",
          "message": "TransactionEventResponse"
        },
        
        "Transaction is stopped"
        → Insert Scenario: TransactionEventRequest Fix with eventType=Ended
        {
          "caller": "Charging Station",
          "callee": "CSMS",
          "message": "TransactionEventRequest",
          "fix_value_list": [
            { "name": "eventType", "value": "Ended" },
            { "name": "chargingState", "value": "EVConnected" }
          ]
        },
        {
          "caller": "CSMS",
          "callee": "Charging Station",
          "message": "TransactionEventResponse"
        }
        
        "one or more transactions are ongoing" or "A transaction is ongoing" or "Ongoing transaction" ..etc
        → Insert Scenario:
        {
          "caller": "Charging Station",
          "callee": "CSMS",
          "message": "TransactionEventRequest",
          "fix_value_list": [
            { "name": "eventType", "value": "Started" }
          ]
        },
        {
          "caller": "CSMS",
          "callee": "Charging Station",
          "message": "TransactionEventResponse"
        }
        
        
        ⚠️ Important:
        If a yellow annotation box appears in a shared figure used for both main and alternative scenarios,
        then the corresponding OCPP messages MUST be included in **each scenario group**, including the one labeled as `description_type = "alternative"`.
        ''')

        self.developer_pre_configuration_instructions = textwrap.dedent('''
        Pre-configuration Variables:
        Some scenarios include conditions that reference the state of configuration variables (e.g., `AuthCacheEnabled = true`, `TxStartPoint contains: DataSigned`). These should be collected in the field `pre_configuration_variable_list`, according to the following rules:
        
        - If the scenario title includes a variable definition (e.g., TxStopPoint = Authorized (or PowerPathClosed)), include the variable and its values in the pre_configuration_variable_list.
          `{ "name": "TxStopPoint", "values": ["Authorized", "PowerPathClosed"] }`
        
        - If a prerequisite states that a configuration variable **must be enabled or set to a specific value**, extract it as:
          `{ "name": "VariableName", "values": ["expected_value"] }`
        
        - If it states that a variable **must be configured or supported** but without a specific value:
          `{ "name": "VariableName" }`
        
        - If the condition uses `contains` to indicate **partial value matching** (e.g., member of list-type variable), express only the mentioned values:
          `{ "name": "VariableName", "values": ["partial_value"] }`
        
        If the scenario includes conditions that reference the state of configuration variables, such variables must be included in the pre_configuration_variable_list field inside each corresponding scenario group.
        
        Examples:
        
        - `AuthCacheEnabled = true` → `{ "name": "AuthCacheEnabled", "values": ["true"] }`
        - `TxStartPoint contains: DataSigned` → `{ "name": "TxStartPoint", "values": ["DataSigned"] }`
        - `OrganizationName must be set` → `{ "name": "OrganizationName" }`
        ''')
        self.developer_example_instructions = textwrap.dedent('''
        Examples:
        
        1.Alternative scenario refers to another (no flow described):
        {
          "scenario_collect_list": [
            {
              "description_type": "main",
              "scenario_list": [
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "BootNotificationRequest",
                  "fix_value_list": [
                    { "name": "reason", "value": "PowerUp" }
                  ]
                }
              ]
            },
            {
              "description_type": "alternative",
              "reference_value": "See E09",
              "scenario_list": null
            }
          ],
          "additional_info_request": null
        }
        
        2. Schema required to confirm field names or referred page missing:
        {
          "scenario_collect_list": [],
          "additional_info_request": {
            "additional_schema_message_list": ["AuthorizeRequest", "SetChargingProfileRequest"],
            "additional_page_request_list": [
              {
                "page_range": { "start": 132, "end": 133 }
              },
              {
                "page_range": { "start": 20, "end": 21 }
              }
            ]
          }
        }
        
        3. Scenario with configuration prerequisites:
        {
          "scenario_collect_list": [
            {
              "description_type": "main",
              "scenario_list": [
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "AuthorizeRequest"
                },
                {
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "AuthorizeResponse"
                }
              ],
              "pre_configuration_variable_list": [
                { "name": "AuthCacheEnabled", "values": ["true"] },
                { "name": "TxStartPoint", "values": ["DataSigned"] },
                { "name": "OrganizationName" }
              ]
            }
          ],
          "additional_info_request": null
        }
        
        4. Scenario depends on external protocols or contains no valid OCPP messages:
        [IMPOSSIBLE]
        
        Scenario with implicit state annotation in diagram 
        (yellow box says "A transaction is ongoing"):
        {
          "scenario_collect_list": [
            {
              "description_type": "main",
              "scenario_list": [
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Started" }
                  ]
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Ended" },
                    { "name": "chargingState", "value": "EVConnected" }
                  ]
                }
              ]
            }
          ],
          "additional_info_request": null
        }
        
        5. Scenario with implicit state annotation in diagram 
        (yellow box says "User authorization successful."):
        {
          "scenario_collect_list": [
            {
              "description_type": "main",
              "scenario_list": [
                {// Derived from shared annotation User authorization successful.
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "AuthorizeRequest"
                },
                {// Derived from shared annotation User authorization successful.
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "AuthorizeResponse"
                  "fix_value_list": [
                    { "name": "certificateStatus", "value": "Accepted" }
                  ]
                },
                {// Inserted due to logical requirement: Updated/Ended must follow a Started event
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Started" }
                  ]
                },
                {// Inserted due to logical requirement: Updated/Ended must follow a Started event
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "TransactionEventResponse"
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Ended" },
                    { "name": "triggerReason", "value": "StopAuthorized" },
                    { "name": "stoppedReason", "value": "Local" }
                  ]
                },
                {
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "TransactionEventResponse"
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "StatusNotificationRequest",
                  "fix_value_list": [
                    { "name": "connectorStatus", "value": "Available" }
                  ]
                },
                {
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "StatusNotificationResponse"
                }
              ],
              "pre_configuration_variable_list": [
                { "name": "TxStopPoint", "values": ["Authorized", "PowerPathClosed"] }
              ]
            },
            {
              "description_type": "alternative",
              "scenario_list": [
                {// Derived from shared annotation
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "AuthorizeRequest"
                },
                {// Derived from shared annotation
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "AuthorizeResponse",
                  "fix_value_list": [
                    { "name": "certificateStatus", "value": "Accepted" }
                  ]
                },
                {// Inserted due to logical requirement: Updated/Ended must follow a Started event
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Started" }
                  ]
                },
                {// Inserted due to logical requirement: Updated/Ended must follow a Started event
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "TransactionEventResponse"
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Updated" },
                    { "name": "triggerReason", "value": "StopAuthorized" }
                  ]
                },
                {
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "TransactionEventResponse"
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "TransactionEventRequest",
                  "fix_value_list": [
                    { "name": "eventType", "value": "Ended" },
                    { "name": "triggerReason", "value": "ChargingStateChanged" },
                    { "name": "chargingState", "value": "EVConnected" },
                    { "name": "stoppedReason", "value": "Local" }
                  ]
                },
                {
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "TransactionEventResponse"
                }
              ],
              "pre_configuration_variable_list": [
                { "name": "TxStopPoint", "values": ["Authorized", "PowerPathClosed"] }
              ]
            }
          ],
          "additional_info_request": null
        }
        6. When the "Prerequisite" section is linked to another use case and the flows are merged together.
        {
          "scenario_collect_list": [
            {
              "description_type": "main",
              "scenario_list": [
                { // Prerequisite "Use case B09 - Setting a new NetworkConnectionProfile was executed successfully prior to this use case"
                  "caller": "CSMS",
                  "callee": "Charging Station",
                  "message": "SetNetworkProfileRequest"
                },
                { // Prerequisite "Use case B09 - Setting a new NetworkConnectionProfile was executed successfully prior to this use case"
                  "caller": "Charging Station",
                  "callee": "CSMS",
                  "message": "SetNetworkProfileResponse",
                  "fix_value_list": [
                    {
                      "name": "status",
                      "value": "Accepted"
                    }
                  ]
                },
                {
                  "caller": "CSMS 1",
                  "callee": "Charging Station",
                  "message": "SetVariablesRequest",
                  "fix_value_list": [
                    {
                      "name": "NetworkConfigurationPriority",
                      "value": "NetworkConnectionProfile"
                    }
                  ]
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS 1",
                  "message": "SetVariablesResponse",
                  "fix_value_list": [
                    {
                      "name": "status",
                      "value": "RebootRequired"
                    }
                  ]
                },
                {
                  "caller": "CSMS 1",
                  "callee": "Charging Station",
                  "message": "ResetRequest",
                  "fix_value_list": [
                    {
                      "name": "type",
                      "value": "OnIdle"
                    }
                  ]
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS 1",
                  "message": "ResetResponse",
                  "fix_value_list": [
                    {
                      "name": "status",
                      "value": "Accepted"
                    }
                  ]
                },
                {
                  "caller": "Charging Station",
                  "callee": "CSMS 2",
                  "message": "BootNotificationRequest"
                },
                {
                  "caller": "CSMS 2",
                  "callee": "Charging Station",
                  "message": "BootNotificationResponse"
                }
              ]
            }
          ],
          "additional_info_request": null
        }
        ''')


        explanation = (
            "The following is a list of messages with their possible caller and callee. Messages with both caller and callee specified are valid and can be used for scenario extraction. If either field is empty, it indicates that direction detection failed due to insufficient or unclear description. In such cases, refer to the figure and surrounding text to determine whether to use the message and how to interpret its direction.\n\n"
        )

        self.developer_table_of_contents_spec = f"Specification File Table of Contents: {parser.table_of_contents_from_specification_parser.get_instruction_content()}"

        self.developer_message_direction_instructions = (
                explanation +
                json.dumps(scenario_collect_instructions, ensure_ascii=False,separators=(",", ":"))
        )

        self.content = textwrap.dedent(f'''
            You are tasked with analyzing the {self.scenario_page_dto.scenario_name} scenario.
            This scenario is based on the figure titled: {self.scenario_page_dto.figure_line}.
            
            Use this figure as the anchor point, and match it with the closest preceding Scenario description section — located either on the same page (above the figure) or within a logically continuous table on the immediately preceding page.
            Treat this pair — the figure and its matching Scenario description — as a single analysis unit.
            
            Even if multiple Scenario descriptions exist under the same {self.scenario_page_dto.scenario_name},
            you must only use the one closest above the figure.
            Do not include any description blocks positioned above the matched one, even if they are on the same page or belong to the same scenario.
            
            Only analyze figures that appear below their matching Scenario description on the same page, or on a subsequent page.
            Do not analyze any figure that appears above its Scenario description, even if they are on the same page.

            All valid OCPP 2.0.1 message flows in these images **must be merged** into a single complete response.
            Only include valid OCPP 2.0.1 messages. Ignore vendor-specific or ambiguous content.

            ⚠️ Strict Compliance Required:
            - You must check for the presence of yellow annotation boxes in the figure. If the annotation contains references to authorization or indicates the need for a preceding TransactionEvent, you must insert the appropriate OCPP message(s) into the scenario flow based on the surrounding context.
            - If a TransactionEventRequest with eventType="Updated" or "Ended" is present without a preceding Started event, you must insert a TransactionEventRequest with eventType="Started" before it. This is a logical requirement based on the protocol flow — a transaction cannot be updated or ended without first being started.
            - When an "Alternative scenario(s)" section is present, it must be added to scenario_collect_list separately using description_type = "alternative", following the format shown in the example cases.
            - Only include flows labeled as "Alternative scenario(s)" under `description_type = "alternative"`. Do **not** infer alternatives from conditionals or diagrams alone.
            - If the scenario **depends primarily on other protocols (e.g., ISO 15118, OCSP, OCPI)** and cannot be simulated using OCPP messages alone from the Charging Station's perspective, respond with `[IMPOSSIBLE]` only. Do not return `scenario_collect_list` or `additional_info_request`.
            - Conditionally triggered messages should only be included in the main flow if they are shown in the diagram and deemed reachable given the scenario logic.
            - You must not populate both scenario_collect_list and additional_info_request in the same response. Only include scenario_collect_list if it is complete and fully constructed.
            - If a "Prerequisite(s)" section refers to another use case (e.g., "Use case B09") without describing any message flow, and the referenced use case is not present in the current image, return only additional_info_request.additional_page_request_list.
                - However, if the prerequisite section contains valid OCPP message flow, extract it and place it before the main scenario_list.
                - If the referenced use case appears in a future response (i.e., as an additional image in a retry), you must merge its extracted messages before the current scenario flow to reflect the prerequisite relationship.
            - If the scenario contains no valid OCPP messages, respond with [IMPOSSIBLE] only.
            - Returning the same response as previously provided is strictly prohibited.
        ''')

        self.messages = [
            InstructionMessageDTO(role="system", content=self.system_instructions),
            InstructionMessageDTO(role="developer", content=self.developer_main_instructions),
            InstructionMessageDTO(role="developer", content=self.developer_textual_states_instructions),
            InstructionMessageDTO(role="developer", content=self.developer_prerequisite_instruction),
            InstructionMessageDTO(role="developer", content=self.developer_pre_configuration_instructions),
            InstructionMessageDTO(role="assistant", content=self.developer_example_instructions),
            InstructionMessageDTO(role="developer", content=self.developer_table_of_contents_spec),
            InstructionMessageDTO(role="developer", content=self.developer_message_direction_instructions),
            InstructionMessageDTO(role="user", content=self.content),
            self.get_main_page_assistant_message_dto(),
            self.get_main_page_instruction_message_dto(),
        ]

        if self.gpt_retry_dto:
            retry_content = f"# This question is a retry, and the response you previously provided is as follows: {self.gpt_retry_dto.error_content}"
            if isinstance(self.gpt_retry_dto.exception, GPTExceptionInterface):
                retry_content += "\n "+ self.gpt_retry_dto.exception.get_instruction_message_for_gpt()
            else:
                retry_content += "\n " + f"# Internal Error Occurred: {str(self.gpt_retry_dto.exception)}"
            self.messages.append(InstructionMessageDTO(role="assistant", content=retry_content))

    def set_additional_schemas(self, json_data_list:List[str]) -> None:
        for json_data in json_data_list:
            if json_data:
                self.messages.append(
                    InstructionMessageDTO(
                        role="developer",
                        content=json_data
                    )
                )
    def get_main_page_assistant_message_dto(self):
        img_text = self.filter_hint_text(self.parser.get_img_text(self.scenario_page_dto))
        content = "The provided image is included for reference, as there may be ambiguity in distinguishing between 'I' (capital i) and 'l' (lowercase L). Please refer to it if there is any confusion. :\n\n" + img_text
        return InstructionMessageDTO(
            role="assistant",
            content=content
        )


    def get_main_page_instruction_message_dto(self):
        img_list = self.parser.get_select_page_img_list(self.scenario_page_dto, s3_config=self.s3_config)


        image_blocks = [
            {
                "type": "image_url",
                "image_url": {"url": image_data_uri}
            }
            for image_data_uri in img_list
        ]

        image_blocks.append({
            "type": "text",
            "text": "These images are the main source for analyzing the scenario. Please extract the scenario flow, message direction, and fixed field values based on the tables and figures shown"
        })
        return InstructionMessageDTO(
                role="user",
                content=image_blocks
            )

    def append_previous_responses(self, object_name:str, scenario_collect_entity:ScenarioCollectEntity, gpt_retry_dto:GPTRetryDTO = None):
        if gpt_retry_dto and gpt_retry_dto.retry > 0:
            gpt_scenario_collect_logs = (
                session.query(GPTScenarioCollectLogEntity)
                .filter_by(
                    scenario_collect_id=scenario_collect_entity.id,
                    object_name=object_name
                )
                .order_by(desc(GPTScenarioCollectLogEntity.created_at))
                .limit(gpt_retry_dto.retry)
            )
            print(f"logs size: {gpt_scenario_collect_logs.count()}")
            if gpt_scenario_collect_logs.count() > 0:
                print("previous messages.append init::")
                previous_content = "previous responses:\n"
                previous_set = set()
                for log in gpt_scenario_collect_logs:
                    try:
                        parsed = json.loads(log.response)
                        compacted = json.dumps(parsed, separators=(",", ":"))
                        previous_set.add(compacted)
                    except json.JSONDecodeError as e:
                        previous_set.add(log.response)
                for compacted in previous_set:
                    previous_content += compacted + "\n"
                self.messages.append(InstructionMessageDTO(role="developer", content=previous_content))

    def filter_hint_text(self, raw_text: str) -> str:
        words = raw_text.split()
        filtered = {word for word in words if 'l' in word or 'I' in word}
        return ' '.join(filtered)

    def set_additional_page(self, additional_page_request_list:List[AdditionalPageRequest]) -> None:
        additional_img_list = self.parser.get_select_page_img_list(additional_page_request_list, self.s3_config)
        additional_text = self.filter_hint_text(self.parser.get_img_text(additional_page_request_list))

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
            "text": "These images are related to a previously processed scenario. Analyze them and merge the results with the existing scenario flow. \n\n"
                    "The provided image is included for reference, as there may be ambiguity in distinguishing between 'I' (capital i) and 'l' (lowercase L). Please refer to it if there is any confusion. :" + additional_text
        })

        self.messages.append(
            InstructionMessageDTO(
                role="user",
                content=image_blocks
            )
        )

