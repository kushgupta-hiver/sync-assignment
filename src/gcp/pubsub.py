from google.cloud import pubsub_v1


class Subscriber:
    def __init__(self, project_id: str, subscription: str, callback):
        self.project_id = project_id
        self.subscription = subscription
        self.callback = callback
        self.subscriber = pubsub_v1.SubscriberClient()
        self.path = self.subscriber.subscription_path(project_id, subscription)

    def start(self):
        streaming_pull_future = self.subscriber.subscribe(self.path, callback=self._on_message)
        try:
            streaming_pull_future.result()  # block
        except KeyboardInterrupt:
            streaming_pull_future.cancel()

    def _on_message(self, message: pubsub_v1.subscriber.message.Message):
        try:
            self.callback(message)
            message.ack()
        except Exception:  # noqa: BLE001
            # transient error: let Pub/Sub redeliver
            message.nack()

