import json
import os

from dict2xml import dict2xml


class RoomData:
    """The class takes the paths to the json files with the list of students and rooms and the output format type.
    Supported output file types: "json", "xml".Calling an instance of the class returns a string with the final data in
    the selected format, and generates an output file in the working directory."""

    __slots__ = ("path_to_rooms", "path_to_students", "output_format")
    __supported_output_formats: tuple = ("json", "xml")

    def __call__(self, *args, **kwargs) -> str:
        if self.output_format == "xml":
            return self.get_result_xml()
        elif self.output_format == "json":
            return self.get_result_json()

    def __init__(self, path_to_rooms: str, path_to_students: str, output_format: str) -> None:
        if os.path.isfile(path_to_rooms):
            self.path_to_rooms: str = path_to_rooms
        else:
            raise FileNotFoundError(f"'{path_to_rooms}' is not a file or does not exist.")

        if os.path.isfile(path_to_students):
            self.path_to_students: str = path_to_students
        else:
            raise FileNotFoundError(f"'{path_to_students}' is not a file or does not exist.")

        if output_format in self.__supported_output_formats:
            self.output_format: str = output_format
        else:
            raise TypeError(
                f"Unknown output format '{output_format}'. Use {' or '.join(self.__supported_output_formats)}."
            )

    def get_data_dicts(self) -> tuple:
        with open(self.path_to_rooms) as json_rooms:
            rooms: list = json.load(json_rooms)
        with open(self.path_to_students) as json_students:
            students: list = json.load(json_students)
        return rooms, students

    def compare_input_data(self) -> list:
        is_xml_output: bool = self.output_format == "xml"
        rooms, students = self.get_data_dicts()
        list(map(lambda room: room.update({"students": {}}), rooms)) if is_xml_output else None
        list(
            map(
                lambda room: (room.get("students") if is_xml_output else room).update(
                    {
                        f"student{'s' if not is_xml_output else ''}": [
                            {"id": student.get("id"), "name": student.get("name")}
                            for student in students
                            if student.get("room") == room.get("id")
                        ]
                    }
                ),
                rooms,
            )
        )
        return rooms

    def get_result_json(self) -> str:
        json_data: str = json.dumps(self.compare_input_data())
        self.write_output_file(json_data)
        return json_data

    def get_result_xml(self) -> str:
        xml_data: str = "<rooms>\n" + dict2xml(self.compare_input_data(), wrap="room") + "\n</rooms>"
        self.write_output_file(xml_data)
        return xml_data

    def write_output_file(self, data: str) -> None:
        with open(f"output_data.{self.output_format}", "w") as output:
            output.write(data)


def main():
    print(RoomData.__doc__)
    path_to_rooms: str = input("Please, enter the path to json file with rooms data: ")
    path_to_students: str = input("Please, enter the path to json file with students data: ")
    output_format: str = input("Please, enter the output format: ")
    RoomData(path_to_rooms, path_to_students, output_format)()
    print("Well done!")


if __name__ == "__main__":
    main()
