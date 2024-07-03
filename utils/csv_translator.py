
from collections.abc import Generator
from deep_translator import GoogleTranslator
import csv

class CSVTranslator:
    PREFIX = "rus_"
    FIELDS = [
        "product_name",
        "category",
        "product_description",
        "care",
        "color",
        "material_"
    ]

    def __init__(self, file: str, sep: str = "\n") -> None:
        self.translator = GoogleTranslator("en", "ru")
        self.sep = sep
        
        self.file = file

        self.csv_reader_f = open(file, "r", encoding="utf-8")
        self.csv_reader = csv.DictReader(self.csv_reader_f, delimiter=";")

    @property
    def new_fields(self) -> list[str]:
        fields = self.csv_reader.fieldnames
        return [self.PREFIX + field for field in fields if any(field.startswith(i) for i in self.FIELDS)]

    def add_new_columns(self, output_file: str) -> None:
        new_fields = self.csv_reader.fieldnames + self.new_fields

        self.csv_writer_f = open(output_file, "w", encoding="utf-8", newline="")
        self.csv_writer = csv.DictWriter(self.csv_writer_f, new_fields, delimiter=";")

        self.csv_writer.writeheader()

    def translate_rows(self) -> Generator[int, None, None]:
        bundle = []
        processed_rows = 0

        for row in self.csv_reader:
            if not bundle: bundle.append(row)
            else:
                if row.get("bundle_id") == bundle[-1].get("bundle_id"):
                    bundle.append(row)
                else:
                    fields = { k: v for k, v in bundle[0].items() if v and any(k.startswith(i) for i in self.FIELDS) }
                    translated_fields = self.translator.translate("\n".join(fields.values())).split("\n")

                    translated_data = { self.PREFIX + k: v for k, v in zip(fields.keys(), translated_fields) }
                    translated_data |= { k: "" for k in self.new_fields if k not in translated_data }

                    for i in bundle: i |= translated_data
                    self.csv_writer.writerows(bundle)
                    processed_rows += len(bundle)

                    bundle = []; bundle.append(row)
                    yield processed_rows

    def close_files(self) -> None:
        self.csv_reader_f.close()
        self.csv_writer_f.close()
