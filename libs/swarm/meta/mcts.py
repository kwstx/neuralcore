import math
import random
from typing import List, Dict, Any, Optional
from .causal import CausalWorldModel

class Node:
    def __init__(self, state: Dict[str, Any], parent=None):
        self.state = state
        self.parent = parent
        self.children: List['Node'] = []
        self.visits = 0
        self.value = 0.0

    def is_fully_expanded(self, possible_actions: List[Dict[str, Any]]) -> bool:
        return len(self.children) == len(possible_actions)

    def best_child(self, exploration_weight: float = 1.41):
        choices_weights = [
            (child.value / child.visits) + exploration_weight * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

class BusinessScenarioMCTS:
    """
    Monte Carlo Tree Search agent that explores hypothetical business scenarios.
    Uses a CausalWorldModel to evaluate outcome rewards.
    """
    def __init__(self, causal_model: CausalWorldModel, iterations: int = 100):
        self.causal_model = causal_model
        self.iterations = iterations

    def search(self, initial_state: Dict[str, Any], possible_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        root = Node(initial_state)

        for _ in range(self.iterations):
            node = self._select(root, possible_actions)
            reward = self._simulate(node)
            self._backpropagate(node, reward)

        return root.best_child(exploration_weight=0).state

    def _select(self, node: Node, possible_actions: List[Dict[str, Any]]) -> Node:
        while not self._is_terminal(node):
            if not node.is_fully_expanded(possible_actions):
                return self._expand(node, possible_actions)
            else:
                node = node.best_child()
        return node

    def _expand(self, node: Node, possible_actions: List[Dict[str, Any]]) -> Node:
        untried_actions = [a for a in possible_actions if a not in [child.state for child in node.children]]
        action = random.choice(untried_actions)
        new_state = node.state.copy()
        new_state.update(action)
        child = Node(new_state, parent=node)
        node.children.append(child)
        return child

    def _simulate(self, node: Node) -> float:
        """
        Calculates expected value through the causal world model.
        """
        return self.causal_model.simulate_counterfactual(node.state)

    def _backpropagate(self, node: Node, reward: float):
        while node is not None:
            node.visits += 1
            node.value += reward
            node.parent = node.parent 
            node = node.parent

    def _is_terminal(self, node: Node) -> bool:
        # Business scenarios have a fixed horizon for exploration
        return node.visits > 10 or len(node.state) > 5
