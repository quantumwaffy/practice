import argparse

from task_1 import parser


def main() -> None:
    supported_output_formats = ("json", "xml")
    arg_parser = argparse.ArgumentParser(description="Process room data")
    arg_parser.add_argument(
        "-pr", dest="path_to_rooms", type=str, default="rooms.json", help="Path to .json file with rooms data"
    )
    arg_parser.add_argument(
        "-ps", dest="path_to_students", type=str, default="students.json", help="Path to .json file with students data"
    )
    arg_parser.add_argument(
        "-f",
        dest="output_format",
        type=str,
        required=True,
        choices=supported_output_formats,
        help="Format type of output file",
    )
    args = arg_parser.parse_args()
    parser.RoomStudentFileHandler(args.path_to_rooms, args.path_to_students, args.output_format)()
    print("Well done!")


if __name__ == "__main__":
    main()
