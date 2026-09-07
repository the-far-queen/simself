from typing import Dict, List, Any, Optional

class InstructionLibrary:
    """
    Stores all possible actions/constraints and semantic mappings for the
    RoboticMasterController, as described in master_apprentice_controller.md.
    """
    def __init__(self):
        self.actions: Dict[str, Dict[str, Any]] = {
            'grasp': {
                'constraints': ["force_limits", "object_properties", "gripper_kinematics"],
                'preconditions': ["object_visible", "gripper_free"],
                'postconditions': ["object_held"]
            },
            'move_to': {
                'constraints': ["collision_free", "joint_limits", "smooth_trajectory"],
                'preconditions': ["path_exists"],
                'postconditions': ["at_position"]
            },
            'brew_coffee': {
                'constraints': ["water_available", "beans_available", "mug_present"],
                'preconditions': ["machine_on", "machine_clean"],
                'postconditions': ["coffee_brewed"]
            },
            'fill_water': {
                'constraints': ["water_source_accessible", "container_present"],
                'preconditions': ["water_tap_on"],
                'postconditions': ["container_filled"]
            }
        }
        
        self.semantic_mapping: Dict[str, List[str]] = {
            'make coffee': ['grasp mug', 'fill water', 'brew coffee'],
            'clean table': ['locate items', 'grasp items', 'move to dishwasher']
        }
        print("InstructionLibrary: Initialized with default actions and semantic mappings.")

    def lookup_action(self, action_name: str) -> Optional[Dict[str, Any]]:
        """
        Looks up a specific action by name.
        """
        return self.actions.get(action_name)

    def lookup_semantic_command(self, command: str) -> List[str]:
        """
        Looks up a sequence of primitive actions for a semantic command.
        """
        return self.semantic_mapping.get(command, [])

    def add_action(self, name: str, constraints: List[str], preconditions: List[str], postconditions: List[str]):
        """
        Adds a new action to the library.
        """
        self.actions[name] = {
            'constraints': constraints,
            'preconditions': preconditions,
            'postconditions': postconditions
        }
        print(f"InstructionLibrary: Added new action '{name}'.")

    def add_semantic_mapping(self, command: str, actions: List[str]):
        """
        Adds a new semantic mapping to the library.
        """
        self.semantic_mapping[command] = actions
        print(f"InstructionLibrary: Added new semantic mapping for '{command}'.")

if __name__ == '__main__':
    print("--- Running InstructionLibrary simulation ---")
    
    library = InstructionLibrary()
    
    print("
Lookup 'grasp' action:")
    grasp_action = library.lookup_action('grasp')
    if grasp_action:
        print(f"  Constraints: {grasp_action['constraints']}")
        print(f"  Preconditions: {grasp_action['preconditions']}")
        print(f"  Postconditions: {grasp_action['postconditions']}")
    
    print("
Lookup 'make coffee' command:")
    coffee_sequence = library.lookup_semantic_command('make coffee')
    print(f"  Action sequence: {coffee_sequence}")

    print("
Adding a new action 'stir':")
    library.add_action('stir', ['container_present', 'spoon_present'], ['liquid_in_container'], ['liquid_stirred'])
    print(f"Lookup 'stir' action: {library.lookup_action('stir')}")

    print("
Adding a new semantic mapping 'prepare tea':")
    library.add_semantic_mapping('prepare tea', ['boil water', 'steep tea', 'add sugar'])
    print(f"Lookup 'prepare tea' command: {library.lookup_semantic_command('prepare tea')}")
