from typing import Dict, List


class TopicStore:
    _topics = Dict[str, bool]

    def __init__(self) -> None:
        self._topics = {}

    def get(self) -> List[str]:
        return self._topics.keys()

    def set(self, topic: str) -> None:
        self._topics[topic] = True

    def remove(self, topic: str) -> None:
        if not self.has(topic):
            return

        del self._topics[topic]

    def has(self, topic: str) -> bool:
        return topic in self._topics
