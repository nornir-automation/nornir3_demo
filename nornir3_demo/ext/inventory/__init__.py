from typing import Dict, List, Optional


dev_types = {
    "edge": 2,
    "spine": 4,
    "leaf": 100,
}
sites = ["mercury", "venus", "earth", "mars", "jupyter", "uranus", "saturn", "neptune"]


InventoryDataType = Dict[str, Dict[str, Dict[str, str]]]


class ACMEAPI:
    @staticmethod
    def get_rack(i: int, dev_type: str) -> str:
        offset_map = {
            "edge": 10,
            "spine": 20,
            "leaf": 100,
        }
        rack_num = offset_map[dev_type] + i // 2
        return f"{rack_num}"

    def get(
        self,
        filter_sites: Optional[List[str]] = None,
        filter_dev_types: Optional[List[str]] = None,
    ) -> InventoryDataType:
        """
        Returns something like:
            {
            }
        """
        result: InventoryDataType = {}
        if filter_sites is None:
            filter_sites = sites
        if filter_dev_types is None:
            filter_dev_types = [t for t in dev_types]

        for site in sites:
            if site not in filter_sites:
                continue

            result[site] = {}

            for dev_type, num in dev_types.items():
                if dev_type not in filter_dev_types:
                    continue

                for i in range(0, dev_types[dev_type]):
                    name = f"{dev_type}{i:02}.{site}"
                    result[site][name] = {
                        "platform": "acmeos",
                        "dev_type": dev_type,
                        "rack": self.get_rack(i, dev_type),
                    }

        return result


if __name__ == "__main__":
    from pprint import pprint

    pprint(ACMEAPI().get(filter_sites=["earth", "mars"]))
