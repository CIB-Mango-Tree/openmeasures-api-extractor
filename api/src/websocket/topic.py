class TopicStore:
    _topics: dict[str, bool]

    def __init__(self) -> None:
        self._topics = {}

    def get(self) -> list[str]:
        return list(self._topics.keys())

    def set(self, topic: str) -> None:
        self._topics[topic] = True

    def remove(self, topic: str) -> None:
        if not self.has(topic):
            return

        del self._topics[topic]

    def has(self, topic: str) -> bool:
        return topic in self._topics
