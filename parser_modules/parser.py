from typing import List

import pdfplumber
import yaml
import fitz
import os
import io

from parser_modules.appendices.appendices_pages import AppendicesPages
from parser_modules.appendices.security_events_parser import SecurityEventsParser
from parser_modules.appendices.standardized_units_of_measure_parser import StandardizedUnitsOfMeasureParser
from parser_modules.appendices.standardized_variables_parser import StandardizedVariablesParser
from parser_modules.appendices.summary_list_of_standardized_components_parser import SummaryListOfStandardizedComponentsParser
from parser_modules.pages import Pages
from parser_modules.s3_upload_config_dto import S3UploadConfigDTO
from parser_modules.specification.data_type import get_data_types_from_pages
from parser_modules.specification.enum_type import get_enumerations_from_pages
from parser_modules.specification.message import get_message_from_pages
from parser_modules.specification.primitive_data_types import get_primitive_data_types_from_pages
from dto.scenario_page_dto import ScenarioPageDTO
import base64
import boto3
from functools import singledispatchmethod
from collections import defaultdict

from parser_modules.specification.referenced_components_and_variables_parser import ReferencedComponentsAndVariablesParser
from parser_modules.specification.table_of_contents_parser import TableOfContentsParser


class Parser:
    def __init__(self, config):
        self.document_path = config.document_path
        self.appendices_document_path = config.appendices_document_path
        self.config_path = config.config_path
        self.version = config.version

        with open(config.config_path, 'r') as f:
            self.yaml_config = yaml.safe_load(f)

        self.pages = Pages(config, self.yaml_config)
        self.appendices_pages = AppendicesPages(config, self.yaml_config)
        self.primitive_data_types = get_primitive_data_types_from_pages(self.version, self.pages.get_primitive_data_types_pages(), self.yaml_config)
        print(f"primitive_data_types len: {len(self.primitive_data_types)}")
        self.messages = get_message_from_pages(self.version, self.pages.get_message_pages(), self.yaml_config)
        print(f"messages len: {len(self.messages)}")
        self.data_types = get_data_types_from_pages(self.version, self.pages.get_data_types_pages(), self.yaml_config)
        print(f"data_types len: {len(self.data_types)}")
        self.enumerations = get_enumerations_from_pages(self.version, self.pages.get_enumerations_pages(), self.yaml_config)
        print(f"enumerations len: {len(self.enumerations)}")

        self.referenced_components_and_variables_parser = ReferencedComponentsAndVariablesParser(self.pages.get_variables_pages(), self.yaml_config)
        print(f"referenced_components_and_variables_parser len: {len(self.referenced_components_and_variables_parser.variable_list)}")
        self.summary_list_of_standardized_components_parser = SummaryListOfStandardizedComponentsParser(self.appendices_pages.get_summary_list_of_standardized_components_pages())
        print(f"standardized components len: {len(self.summary_list_of_standardized_components_parser.list)}")
        self.standardized_variables_parser = StandardizedVariablesParser(self.appendices_pages.get_standardized_variables_pages())
        print(f"standardized variables len: {len(self.standardized_variables_parser.list)}")
        self.security_events_parser = SecurityEventsParser(self.appendices_pages.get_security_events_pages())
        print(f"security_events len: {len(self.security_events_parser.list)}")
        self.standardized_units_of_measure_parser = StandardizedUnitsOfMeasureParser(self.appendices_pages.get_standardized_units_of_measure_pages())
        print(f"standardized_units_of_measure len: {len(self.standardized_units_of_measure_parser.list)}")
        self.table_of_contents_from_specification_parser = TableOfContentsParser(self.pages.get_table_of_contents_pages(), self.yaml_config)
        # print(self.table_of_contents_from_specification_parser.tree)
        self.table_of_contents_from_appendices_parser = TableOfContentsParser(self.appendices_pages.get_table_of_contents_pages(), self.yaml_config)



        def count_by_depth(tree, depth=1, counter=None):
            if counter is None:
                counter = defaultdict(int)
            for node in tree:
                counter[depth] += 1
                if node.get('children'):
                    count_by_depth(node['children'], depth + 1, counter)
            return counter

    @singledispatchmethod
    def get_select_page_img_list(self, arg, s3_config):
        raise NotImplementedError("Unsupported type")

    @singledispatchmethod
    def get_img_text(self, arg):
        raise NotImplementedError("Unsupported type")

    @get_img_text.register
    def _(self, scenario_page_dto: ScenarioPageDTO):
        start = scenario_page_dto.start_index
        end = scenario_page_dto.end_index

        extracted_text = []
        with pdfplumber.open(self.document_path) as pdf:
            for i in range(start, end + 1):
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_text.append(f"# Page {i + 1}\n{text.strip()}")

        return "\n\n".join(extracted_text)

    @get_img_text.register
    def _(self, additional_page_request_list: list):
        extracted_text = []
        for additional_page_request in additional_page_request_list:
            match additional_page_request.document:
                case "Specification":
                    start = self.pages.get_page_index(additional_page_request.page_range.start)
                    end = self.pages.get_page_index(additional_page_request.page_range.end)
                    with pdfplumber.open(self.document_path) as pdf:
                        for i in range(start, end + 1):
                            page = pdf.pages[i]
                            text = page.extract_text()
                            if text:
                                extracted_text.append(f"# Page {i + 1}\n{text.strip()}")
        return "\n\n".join(extracted_text)
    @get_select_page_img_list.register
    def _(self, additional_page_request_list: list, s3_config: S3UploadConfigDTO):
        images = []
        for additional_page_request in additional_page_request_list:
            start_page_index = 0
            end_page_index = 0
            match additional_page_request.document:
                case "Specification":
                    s3_config.s3_prefix = os.path.splitext(os.path.basename(self.document_path))[0]
                    start_page_index = self.pages.get_page_index(additional_page_request.page_range.start)
                    end_page_index = self.pages.get_page_index(additional_page_request.page_range.end)
                    images.extend(self.upload_pdf_pages_to_s3(pdf_path=self.document_path, start_index=start_page_index, end_index=end_page_index, s3_config = s3_config))
                case "Appendix":
                    s3_config.s3_prefix = os.path.splitext(os.path.basename(self.appendices_document_path))[0]
                    start_page_index = self.appendices_pages.get_page_index(additional_page_request.page_range.start)
                    end_page_index = self.appendices_pages.get_page_index(additional_page_request.page_range.end)
                    images.extend(self.upload_pdf_pages_to_s3(pdf_path=self.appendices_document_path, start_index=start_page_index, end_index=end_page_index, s3_config = s3_config))


        return images

    @get_select_page_img_list.register
    def _(self, scenario_page_dto:ScenarioPageDTO, s3_config):
        s3_config.s3_prefix = os.path.splitext(os.path.basename(self.document_path))[0]
        return self.upload_pdf_pages_to_s3(pdf_path=self.document_path, start_index=scenario_page_dto.start_index, end_index=scenario_page_dto.end_index,s3_config=s3_config)

    def extract_images_from_pdf(self, pdf_path, start_index, end_index, output_dir = "extract_images"):
        file_path_list = []
        os.makedirs(output_dir, exist_ok=True)
        doc = fitz.open(pdf_path)

        for page_index in range(start_index, end_index + 1):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=300)
            file_name = f"{output_dir}/page_{page_index}.png"
            pix.save(file_name)
            file_path_list.append(file_name)
        return file_path_list

    def get_pdf_pages_as_base64_images(self, pdf_path, start_index, end_index):
        doc = fitz.open(pdf_path)
        base64_images = []

        for page_index in range(start_index, end_index + 1):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("png")
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")
            data_uri = f"data:image/png;base64,{image_base64}"
            base64_images.append(data_uri)

        return base64_images

    def upload_pdf_pages_to_s3(
            self,
            pdf_path: str,
            start_index: int,
            end_index: int,
            s3_config: S3UploadConfigDTO,
            is_index = True
    ) -> List[str]:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=s3_config.access_key,
            aws_secret_access_key=s3_config.secret_key,
            region_name=s3_config.region,
        )

        doc = fitz.open(pdf_path)
        uploaded_urls = []

        for page_index in range(start_index, end_index + 1):
            page_number = 0
            if pdf_path == self.document_path:
                page_number = self.pages.get_page_number(page_index)
            if pdf_path == self.appendices_document_path:
                page_number = self.appendices_pages.get_page_number(page_index)
            image_key = f"{s3_config.s3_prefix}/page_{page_number}.png"
            from botocore.exceptions import ClientError
            try:
                s3.head_object(Bucket=s3_config.bucket_name, Key=image_key)
                image_url = f"https://{s3_config.bucket_name}.s3.{s3_config.region}.amazonaws.com/{image_key}"
                uploaded_urls.append(image_url)
                continue
            except ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=150)
            image_bytes = pix.tobytes("png")

            s3.put_object(
                Bucket=s3_config.bucket_name,
                Key=image_key,
                Body=io.BytesIO(image_bytes),
                ContentType="image/png",
            )

            image_url = f"https://{s3_config.bucket_name}.s3.{s3_config.region}.amazonaws.com/{image_key}"
            uploaded_urls.append(image_url)

        return uploaded_urls

    def get_scenario_pages(self):
        return self.pages.get_scenario_pages()
