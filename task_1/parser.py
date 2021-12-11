import copy
import json
import os
from abc import ABC, abstractmethod
from itertools import groupby
from typing import Type

from dict2xml import dict2xml


class JSONInputFilePath:
    def __set_name__(self, owner, name: str) -> None:
        self.__name: str = name

    def __get__(self, obj, objtype=None) -> str:
        return obj.__dict__[self.__name]

    def __set__(self, obj, value: str) -> None:
        if os.path.isfile(value):
            if value.endswith(".json"):
                obj.__dict__[self.__name] = value
            else:
                raise ValueError("The file must have a '.json' extension")
        else:
            raise FileNotFoundError(f"'{value}' is not a file or does not exist.")


class RoomStudentOutputFormat:
    __supported_output_formats: tuple = ("json", "xml")

    def __set_name__(self, owner, name: str) -> None:
        self.__name: str = name

    def __get__(self, obj, objtype=None) -> str:
        return obj.__dict__[self.__name]

    def __set__(self, obj, value: str) -> None:
        if value in self.__supported_output_formats:
            obj.__dict__[self.__name] = value
        else:
            raise ValueError(f"Unknown output format '{value}'. Use {' or '.join(self.__supported_output_formats)}.")


class InputDataConverter(ABC):
    def __init__(self, path) -> None:
        self._path = path

    @abstractmethod
    def get_data(self) -> list[dict]:
        pass


class ComparerData(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass


class Serializer(ABC):
    def __init__(self, data: list[dict]) -> None:
        self._data: list[dict] = data

    @abstractmethod
    def serialize(self) -> str:
        pass


class OutputFile(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def write_file(self) -> None:
        pass


class RoomStudentOutputFile(OutputFile):
    _output_format = RoomStudentOutputFormat()

    def __init__(self, serialized_data: str, output_format: str) -> None:
        super().__init__()
        self._serialized_data = serialized_data
        self._output_format = output_format

    def write_file(self) -> None:
        with open(f"students_rooms_data.{self._output_format}", "w") as output:
            output.write(self._serialized_data)


class JSONInputDataConverter(InputDataConverter):
    _path = JSONInputFilePath()

    def get_data(self) -> list[dict]:
        with open(self._path) as json_data:
            data: list[dict] = json.load(json_data)
        return data


class RoomStudentComparerData(ComparerData):
    _prepared_students_data_cache: dict = None

    def __init__(self, rooms_data: list[dict], students_data: list[dict]) -> None:
        super().__init__()
        self._rooms_data: list[dict] = rooms_data
        self._students_data: list[dict] = sorted(students_data, key=lambda student: student.get("room"))
        self._preset_compared_data = copy.deepcopy(rooms_data)

    @property
    def _prepared_students_data(self) -> dict:
        if not self._prepared_students_data_cache:
            self._prepared_students_data_cache: dict = {
                room: list(students)
                for room, students in groupby(self._students_data, key=lambda student: student.get("room"))
            }
        return self._prepared_students_data_cache

    @abstractmethod
    def compare(self) -> list[dict]:
        pass


class JSONRoomStudentComparerData(RoomStudentComparerData):
    def compare(self) -> list[dict]:
        [
            room.update({"students": self._prepared_students_data.get(room.get("id"))})
            for room in self._preset_compared_data
        ]
        return self._preset_compared_data


class XMLRoomStudentComparerData(RoomStudentComparerData):
    def compare(self) -> list[dict]:
        list(map(lambda room: room.update({"students": {}}), self._preset_compared_data))
        [
            room.get("students").update({"student": self._prepared_students_data.get(room.get("id"))})
            for room in self._preset_compared_data
        ]
        return self._preset_compared_data


class JSONRoomStudentSerializer(Serializer):
    def serialize(self) -> str:
        json_data: str = json.dumps(self._data)
        return json_data


class XMLRoomStudentSerializer(Serializer):
    def serialize(self) -> str:
        xml_data: str = "<rooms>\n" + dict2xml(self._data, wrap="room") + "\n</rooms>"
        return xml_data


class RoomStudentFileFactory:
    _output_format = RoomStudentOutputFormat()

    _input_conversion_handlers: dict = {
        "json": JSONInputDataConverter,
    }
    _comparison_handlers: dict = {
        "json": JSONRoomStudentComparerData,
        "xml": XMLRoomStudentComparerData,
    }
    _serializers: dict = {"json": JSONRoomStudentSerializer, "xml": XMLRoomStudentSerializer}
    _output_handlers: dict = {"default": RoomStudentOutputFile}

    def __init__(self, output_format: str, input_format: str = "json") -> None:
        self._output_format: str = output_format
        self._input_format: str = input_format

    @property
    def input_handler(self) -> Type[InputDataConverter]:
        return self._input_conversion_handlers.get(self._input_format)

    @property
    def comparison_handler(self) -> Type[RoomStudentComparerData]:
        return self._comparison_handlers.get(self._output_format)

    @property
    def serializer(self) -> Type[Serializer]:
        return self._serializers.get(self._output_format)

    @property
    def output_handler(self) -> Type[RoomStudentOutputFile]:
        return self._output_handlers.get("default")


class RoomStudentFileHandler:
    _file_factory: Type[RoomStudentFileFactory] = RoomStudentFileFactory

    def __init__(self, path_to_rooms: str, path_to_students: str, output_format: str) -> None:
        instance_file_factory: RoomStudentFileFactory = self._file_factory(output_format)
        self._input_handler: Type[InputDataConverter] = instance_file_factory.input_handler
        self._comparison_handler: Type[RoomStudentComparerData] = instance_file_factory.comparison_handler
        self._serializer: Type[Serializer] = instance_file_factory.serializer
        self._output_handler: Type[RoomStudentOutputFile] = instance_file_factory.output_handler
        self._path_to_rooms: str = path_to_rooms
        self._path_to_students: str = path_to_students
        self._output_format: str = output_format

    def __call__(self, *args, **kwargs) -> None:
        return self.write_output_file()

    @property
    def _rooms_data(self) -> list[dict]:
        return self._input_handler(self._path_to_rooms).get_data()

    @property
    def _students_data(self) -> list[dict]:
        return self._input_handler(self._path_to_students).get_data()

    @property
    def _compared_data(self) -> list[dict]:
        return self._comparison_handler(self._rooms_data, self._students_data).compare()

    @property
    def _serialized_data(self) -> str:
        return self._serializer(self._compared_data).serialize()

    def write_output_file(self) -> None:
        return self._output_handler(self._serialized_data, self._output_format).write_file()
