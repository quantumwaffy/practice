from pkg_resources import parse_version


class Version:
    def __init__(self, version):
        self.version = version

    @property
    def parsed_version(self):
        return parse_version(self.version)

    def __lt__(self, other):
        return self.parsed_version < other.parsed_version

    def __gt__(self, other):
        return self.parsed_version > other.parsed_version

    def __ne__(self, other):
        return self.parsed_version != other.parsed_version


def main():
    to_test = [
        ("1.0.0", "2.0.0"),
        ("1.0.0", "1.42.0"),
        ("1.2.0", "1.2.42"),
        ("1.1.0-alpha", "1.2.0-alpha.1"),
        ("1.0.10-alpha.beta", "1.0.1b"),
        ("1.0.0-rc.1", "1.0.0"),
    ]

    for version_1, version_2 in to_test:
        assert Version(version_1) < Version(version_2), "lt failed"
        assert Version(version_2) > Version(version_1), "gt failed"
        assert Version(version_2) != Version(version_1), "ne failed"


if __name__ == "__main__":
    main()
