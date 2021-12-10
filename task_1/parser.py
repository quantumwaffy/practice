import copy
import json
import os
from abc import ABC, abstractmethod

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

    def __init__(self, path) -> None:
        self._path = path

    def get_data(self) -> list[dict]:
        with open(self._path) as json_data:
            data: list[dict] = json.load(json_data)
        return data


class RoomStudentComparerData(ComparerData):
    def __init__(self, rooms_data: list[dict], students_data: list[dict]) -> None:
        super().__init__()
        self._rooms_data: list[dict] = rooms_data
        self._students_data: list[dict] = students_data
        self._preset_compared_data = copy.deepcopy(rooms_data)

    @abstractmethod
    def compare(self) -> list[dict]:
        pass


class JSONRoomStudentComparerData(RoomStudentComparerData):
    def compare(self) -> list[dict]:
        list(
            map(
                lambda room: room.update(
                    {
                        "students": [
                            {"id": student.get("id"), "name": student.get("name")}
                            for student in self._students_data
                            if student.get("room") == room.get("id")
                        ]
                    }
                ),
                self._preset_compared_data,
            )
        )
        return self._preset_compared_data


class XMLRoomStudentComparerData(RoomStudentComparerData):
    def compare(self) -> list[dict]:
        list(map(lambda room: room.update({"students": {}}), self._preset_compared_data))
        list(
            map(
                lambda room: room.get("students").update(
                    {
                        "student": [
                            {"id": student.get("id"), "name": student.get("name")}
                            for student in self._students_data
                            if student.get("room") == room.get("id")
                        ]
                    }
                ),
                self._preset_compared_data,
            )
        )
        return self._preset_compared_data


class JSONRoomStudentSerializer(Serializer):
    def serialize(self) -> str:
        json_data: str = json.dumps(self._data)
        return json_data


class XMLRoomStudentSerializer(Serializer):
    def serialize(self) -> str:
        xml_data: str = "<rooms>\n" + dict2xml(self._data, wrap="room") + "\n</rooms>"
        return xml_data


class RoomStudentProcessFile(ABC):
    _compared_data = None
    _serialized_data = None

    def __call__(self, *args, **kwargs):
        return self.write_output_file()

    def __init__(self, path_to_rooms: str, path_to_students: str, output_format: str) -> None:
        self._rooms_data: list[dict] = JSONInputDataConverter(path_to_rooms).get_data()
        self._students_data: list[dict] = JSONInputDataConverter(path_to_students).get_data()
        self._output_format = output_format

    @abstractmethod
    def _compare_data(self) -> list[dict]:
        pass

    @abstractmethod
    def _serialize_data(self) -> str:
        pass

    def write_output_file(self) -> None:
        return RoomStudentOutputFile(self._serialize_data(), self._output_format).write_file()


class JSONProcessFile(RoomStudentProcessFile):
    def _compare_data(self) -> list[dict]:
        self._compared_data: list[dict] = JSONRoomStudentComparerData(self._rooms_data, self._students_data).compare()
        return self._compared_data

    def _serialize_data(self) -> str:
        self._serialized_data: str = JSONRoomStudentSerializer(self._compare_data()).serialize()
        return self._serialized_data


class XMLProcessFile(RoomStudentProcessFile):
    def _compare_data(self) -> list[dict]:
        self._compared_data: list[dict] = XMLRoomStudentComparerData(self._rooms_data, self._students_data).compare()
        return self._compared_data

    def _serialize_data(self) -> str:
        self._serialized_data: str = XMLRoomStudentSerializer(self._compare_data()).serialize()
        return self._serialized_data
