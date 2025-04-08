from enum import Enum


class NodeType(str, Enum):
    DIR = "DIR"
    MODULE = "MODULE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"


class EventType(str, Enum):
    COLLECTION = "COLLECTION"
    SCHEDULED = "SCHEDULED"
    OUTCOME = "OUTCOME"
    REPORT = "REPORT"


def get_nice_tooltip(node_data: dict) -> str | None:
    tooltip_str = f"{node_data['nodeid']:^20}\n".replace("[", "\[")

    status = node_data["status"].replace("[", "\[")
    tooltip_str += f"\n[yellow]{status}[/]\n\n"
    # tooltip_str += f"Level needed: [blue]{node_data.level_needed:>6}[/]\n"
    # tooltip_str += f"Damage: [blue]{node_data.damage:>12}[/]\n" if item.damage > 0 else ""
    # tooltip_str += (
    #     f"Attack Speed: [blue]{node_data.attack_speed:>6}[/]\n"
    #     if node_data.attack_speed > 0
    #     else ""
    # )
    # if sum([node_data.strength, item.intelligence, item.dexterity, item.luck]) > 0:
    #     tooltip_str += f"\n[yellow]{'Bonus Stats':-^20}[/]\n\n"
    #     tooltip_str += (
    #         f"Strength: [blue]{node_data.strength:>10}[/]\n" if item.strength > 0 else ""
    #     )
    #     tooltip_str += (
    #         f"Intelligence: [blue]{node_data.intelligence:>6}[/]\n"
    #         if node_data.intelligence > 0
    #         else ""
    #     )
    #     tooltip_str += (
    #         f"Dexterity: [blue]{node_data.dexterity:>9}[/]\n" if item.dexterity > 0 else ""
    #     )
    #     tooltip_str += f"Luck: [blue]{node_data.luck:>14}[/]\n" if item.luck > 0 else ""
    return tooltip_str
